from src.matcher import match_keywords
from src.fetcher import Tweet


def test_match_keywords_hit_single():
    keywords = ["A股", "上证", "涨停"]
    tweet = Tweet(
        tweet_id="1", author="user", content="今天A股走势不错",
        link="https://x.com/user/status/1",
        published="2026-06-06T14:30:00", is_reply=False,
    )
    assert match_keywords(tweet, keywords) is True


def test_match_keywords_no_match():
    keywords = ["A股", "涨停"]
    tweet = Tweet(
        tweet_id="3", author="user", content="今天天气不错",
        link="link", published="2026-06-06T14:30:00", is_reply=False,
    )
    assert match_keywords(tweet, keywords) is False


def test_match_keywords_case_insensitive():
    keywords = ["A股"]
    tweet = Tweet(
        tweet_id="4", author="user", content="关注a股市场",
        link="link", published="2026-06-06T14:30:00", is_reply=False,
    )
    assert match_keywords(tweet, keywords) is True


def test_match_keywords_empty_list():
    tweet = Tweet(
        tweet_id="5", author="user", content="上证指数",
        link="link", published="2026-06-06T14:30:00", is_reply=False,
    )
    assert match_keywords(tweet, []) is False


def test_match_keywords_empty_content():
    keywords = ["A股"]
    tweet = Tweet(
        tweet_id="6", author="user", content="",
        link="link", published="2026-06-06T14:30:00", is_reply=False,
    )
    assert match_keywords(tweet, keywords) is False


def test_match_keywords_substring_match():
    keywords = ["IPO"]
    tweet = Tweet(
        tweet_id="7", author="user", content="这只股票即将IPO上市",
        link="link", published="2026-06-06T14:30:00", is_reply=False,
    )
    assert match_keywords(tweet, keywords) is True
