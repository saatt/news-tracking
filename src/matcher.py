from src.fetcher import Tweet


def match_keywords(tweet: Tweet, keywords: list[str]) -> bool:
    if not keywords or not tweet.content:
        return False
    content_lower = tweet.content.lower()
    for kw in keywords:
        if kw.lower() in content_lower:
            return True
    return False
