import pytest
from src.fetcher import parse_rss_entries, extract_tweet_id, Tweet


SAMPLE_RSS = {
    "entries": [
        {
            "id": "https://x.com/testuser/status/1234567890",
            "title": "Test tweet title",
            "summary": "This is the tweet content",
            "published": "Fri, 06 Jun 2026 14:30:00 GMT",
            "link": "https://x.com/testuser/status/1234567890",
        },
        {
            "id": "https://x.com/testuser/status/9876543210",
            "title": "Another tweet",
            "summary": "More content here",
            "published": "Fri, 06 Jun 2026 15:00:00 GMT",
            "link": "https://x.com/testuser/status/9876543210",
        },
    ]
}


def test_parse_rss_entries_returns_tweet_list():
    tweets = parse_rss_entries(SAMPLE_RSS, "testuser")
    assert len(tweets) == 2
    assert all(isinstance(t, Tweet) for t in tweets)


def test_parse_rss_entries_extracts_content():
    tweets = parse_rss_entries(SAMPLE_RSS, "testuser")
    assert tweets[0].content == "This is the tweet content"
    assert tweets[0].tweet_id == "1234567890"
    assert tweets[0].link == "https://x.com/testuser/status/1234567890"


def test_parse_rss_entries_strips_html():
    rss = {
        "entries": [
            {
                "id": "x/status/1",
                "title": "t",
                "summary": '<p>Content with <a href="link">HTML</a></p>',
                "published": "Fri, 06 Jun 2026 14:30:00 GMT",
                "link": "https://x.com/user/status/1",
            }
        ]
    }
    tweets = parse_rss_entries(rss, "user")
    assert "HTML" in tweets[0].content
    assert "<p>" not in tweets[0].content
    assert "<a" not in tweets[0].content


def test_parse_rss_entries_empty_entries():
    tweets = parse_rss_entries({"entries": []}, "user")
    assert tweets == []


def test_extract_tweet_id_from_status_url():
    assert extract_tweet_id("https://x.com/user/status/1234567890") == "1234567890"


def test_extract_tweet_id_from_nitter_url():
    assert extract_tweet_id("https://nitter.net/user/status/1234567890") == "1234567890"


def test_extract_tweet_id_returns_fallback():
    result = extract_tweet_id("https://example.com/something-else")
    assert result is not None


def test_tweet_dataclass_fields():
    t = Tweet(
        tweet_id="123",
        author="testuser",
        content="Hello",
        link="https://x.com/testuser/status/123",
        published="2026-06-06T14:30:00+00:00",
        is_reply=False,
    )
    assert t.tweet_id == "123"
    assert not t.is_reply


def test_parse_rss_entries_detects_reply():
    rss = {
        "entries": [
            {
                "id": "x/status/1",
                "title": "re: Something",
                "summary": "This is a reply to someone",
                "published": "Fri, 06 Jun 2026 14:30:00 GMT",
                "link": "https://x.com/user/status/1",
            }
        ]
    }
    tweets = parse_rss_entries(rss, "user")
    assert tweets[0].is_reply is True


def test_parse_rss_entries_filters_out_retweets():
    rss = {
        "entries": [
            {
                "id": "x/status/1",
                "title": "RT by user: Original tweet",
                "summary": "Some retweeted content",
                "published": "Fri, 06 Jun 2026 14:30:00 GMT",
                "link": "https://x.com/user/status/1",
            }
        ]
    }
    tweets = parse_rss_entries(rss, "user")
    assert len(tweets) == 0
