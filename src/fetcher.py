import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
import structlog

logger = structlog.get_logger()


@dataclass(frozen=True)
class Tweet:
    tweet_id: str
    author: str
    content: str
    link: str
    published: str  # ISO 8601
    is_reply: bool


def extract_tweet_id(link: str) -> str:
    match = re.search(r"/status/(\d+)", link)
    if match:
        return match.group(1)
    return link


def _strip_html(text: str) -> str:
    clean = re.compile(r"<.*?>")
    return re.sub(clean, "", text)


def _parse_date(published_str: str) -> str:
    try:
        dt = parsedate_to_datetime(published_str)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def parse_rss_entries(rss: dict, author_username: str) -> list[Tweet]:
    tweets = []
    for entry in rss.get("entries", []):
        title = entry.get("title", "")
        link = entry.get("link", "")

        # Skip retweets
        if title.startswith("RT by") or title.startswith("RT @"):
            continue

        tweet_id = extract_tweet_id(link)
        content = _strip_html(entry.get("summary", ""))
        published = _parse_date(entry.get("published", ""))
        is_reply = title.lower().startswith("re:") or content.startswith("@")

        tweets.append(
            Tweet(
                tweet_id=tweet_id,
                author=author_username,
                content=content,
                link=link,
                published=published,
                is_reply=is_reply,
            )
        )

    return tweets


class Fetcher:
    def __init__(self, instances: list[str], timeout: float = 10.0):
        self.instances = instances
        self.timeout = timeout

    async def fetch(self, author_username: str) -> list[Tweet] | None:
        """Fetch tweets for an author. Returns None if all instances fail."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for instance in self.instances:
                url = f"{instance.rstrip('/')}/{author_username}/with_replies/rss"
                try:
                    logger.debug("Fetching RSS", url=url, author=author_username)
                    response = await client.get(url)
                    response.raise_for_status()
                    rss = feedparser.parse(response.text)
                    tweets = parse_rss_entries(rss, author_username)
                    logger.info(
                        "Fetched tweets",
                        instance=instance,
                        author=author_username,
                        count=len(tweets),
                    )
                    return tweets
                except httpx.TimeoutException:
                    logger.warning(
                        "Nitter instance timeout",
                        instance=instance,
                        author=author_username,
                    )
                except httpx.HTTPStatusError as e:
                    logger.warning(
                        "Nitter instance HTTP error",
                        instance=instance,
                        status=e.response.status_code,
                        author=author_username,
                    )
                except Exception as e:
                    logger.warning(
                        "Nitter instance error",
                        instance=instance,
                        error=str(e),
                        author=author_username,
                    )

        logger.error(
            "All Nitter instances failed",
            author=author_username,
            instances_tried=len(self.instances),
        )
        return None
