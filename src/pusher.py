import asyncio
import httpx
import structlog
from src.fetcher import Tweet

logger = structlog.get_logger()

CONTENT_MAX_LENGTH = 200


def format_markdown(tweet: Tweet, display_name: str, is_a_stock: bool) -> str:
    prefix = "🔴【A股相关】" if is_a_stock else ""
    type_icon = "💬" if tweet.is_reply else "📢"
    type_label = "的回复" if tweet.is_reply else "新推文"

    content = tweet.content
    if len(content) > CONTENT_MAX_LENGTH:
        content = f"{content[:CONTENT_MAX_LENGTH]}..."

    lines = [
        f"{prefix}{type_icon} @{display_name} {type_label}",
        "",
        f"> {content}",
        "",
        f"🔗 {tweet.link}",
        f"🕐 {tweet.published}",
    ]
    return "\n".join(lines)


class DingTalkPusher:
    def __init__(self, webhook_url: str, max_retries: int = 3):
        self.webhook_url = webhook_url
        self.max_retries = max_retries

    async def send(self, tweet: Tweet, display_name: str, is_a_stock: bool) -> bool:
        markdown_text = format_markdown(tweet, display_name, is_a_stock)
        title_prefix = "🔴【A股相关】" if is_a_stock else "📢"
        type_label = "的回复" if tweet.is_reply else "新推文"
        title = f"{title_prefix} @{display_name} {type_label}"

        payload = {
            "msgtype": "markdown",
            "markdown": {"title": title, "text": markdown_text},
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(self.webhook_url, json=payload)
                    data = response.json()
                    if data.get("errcode") == 0:
                        logger.info("Pushed to DingTalk", tweet_id=tweet.tweet_id, is_a_stock=is_a_stock)
                        return True
                    else:
                        logger.warning("DingTalk returned error", errcode=data.get("errcode"), errmsg=data.get("errmsg"), attempt=attempt)
            except Exception as e:
                logger.warning("DingTalk request failed", error=str(e), attempt=attempt)
            if attempt < self.max_retries:
                await asyncio.sleep(2 ** (attempt - 1))

        logger.error("DingTalk push failed after all retries", tweet_id=tweet.tweet_id, max_retries=self.max_retries)
        return False
