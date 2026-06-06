from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

import structlog

from src.config import Config
from src.fetcher import Fetcher
from src.matcher import match_keywords
from src.pusher import DingTalkPusher
from src.store import TweetStore, DuplicateTweetError

logger = structlog.get_logger()


class Monitor:
    def __init__(self, config: Config):
        self.config = config
        self.fetcher = Fetcher(instances=config.nitter_instances)
        self.pusher = DingTalkPusher(webhook_url=config.dingtalk_webhook_url)
        self.store = TweetStore(db_path=config.database_path)

    async def start(self):
        await self.store.init()
        logger.info("Monitor initialized", authors=len(self.config.authors))

    async def tick(self):
        """Single polling cycle — fetch, match, push."""
        for author in self.config.authors:
            username = author["username"]
            display_name = author.get("display_name", username)

            try:
                tweets = await self.fetcher.fetch(username)
            except Exception as e:
                logger.error("Fetch failed", author=username, error=str(e))
                continue

            if tweets is None:
                logger.warning("No data from any Nitter instance", author=username)
                continue

            if not tweets:
                logger.debug("No new tweets", author=username)
                continue

            new_count = 0
            for tweet in tweets:
                try:
                    already_seen = await self.store.exists(tweet.tweet_id)
                    if already_seen:
                        continue

                    is_a_stock = match_keywords(tweet, self.config.a_stock_keywords)

                    success = await self.pusher.send(
                        tweet=tweet,
                        display_name=display_name,
                        is_a_stock=is_a_stock,
                    )

                    if success:
                        try:
                            await self.store.save(
                                tweet_id=tweet.tweet_id,
                                author=username,
                                content=tweet.content,
                                link=tweet.link,
                                published=tweet.published,
                                is_a_stock=is_a_stock,
                                is_reply=tweet.is_reply,
                            )
                        except DuplicateTweetError:
                            logger.debug("Duplicate tweet skipped", tweet_id=tweet.tweet_id)
                        new_count += 1
                except Exception as e:
                    logger.error(
                        "Failed to process tweet",
                        tweet_id=tweet.tweet_id,
                        error=str(e),
                    )

            if new_count > 0:
                logger.info(
                    "Cycle complete",
                    author=username,
                    new_tweets=new_count,
                )

    async def shutdown(self):
        await self.store.close()
        logger.info("Monitor shut down")


def create_scheduler(monitor: Monitor) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        monitor.tick,
        trigger=IntervalTrigger(seconds=monitor.config.poll_interval_seconds),
        id="poll_tweets",
        name="Poll Twitter RSS",
        replace_existing=True,
    )
    return scheduler
