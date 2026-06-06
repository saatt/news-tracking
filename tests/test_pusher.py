import pytest
from src.pusher import format_markdown, DingTalkPusher
from src.fetcher import Tweet


def make_tweet(content="Hello", is_reply=False):
    return Tweet(
        tweet_id="123", author="testuser", content=content,
        link="https://x.com/testuser/status/123",
        published="2026-06-06T14:30:00+00:00", is_reply=is_reply,
    )


def test_format_markdown_normal_tweet():
    tweet = make_tweet(content="普通推文内容")
    md = format_markdown(tweet, "Test User", is_a_stock=False)
    assert "📢 @Test User 新推文" in md
    assert "普通推文内容" in md
    assert "https://x.com/testuser/status/123" in md
    assert "2026-06-06" in md
    assert "🔴" not in md


def test_format_markdown_a_stock_tweet():
    tweet = make_tweet(content="A股大涨")
    md = format_markdown(tweet, "Test User", is_a_stock=True)
    assert "🔴【A股相关】" in md
    assert "📢 @Test User 新推文" in md


def test_format_markdown_reply_tweet():
    tweet = make_tweet(content="回复某人", is_reply=True)
    md = format_markdown(tweet, "Test User", is_a_stock=False)
    assert "💬 @Test User 的回复" in md
    assert "回复某人" in md


def test_format_markdown_long_content_truncated():
    long_content = "A" * 300
    tweet = make_tweet(content=long_content)
    md = format_markdown(tweet, "Test User", is_a_stock=False)
    content_line = [line for line in md.split("\n") if line.startswith("> ")][0]
    displayed = content_line[2:]
    assert displayed.endswith("...")
    assert len(displayed) <= 203


def test_format_markdown_short_content_not_truncated():
    tweet = make_tweet(content="Short")
    md = format_markdown(tweet, "Test User", is_a_stock=False)
    assert "> Short\n" in md


@pytest.mark.asyncio
async def test_pusher_send_success(httpx_mock):
    httpx_mock.add_response(
        url="https://oapi.dingtalk.com/robot/send?access_token=test",
        json={"errcode": 0, "errmsg": "ok"},
    )
    pusher = DingTalkPusher(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test"
    )
    success = await pusher.send(
        tweet=make_tweet(), display_name="Test User", is_a_stock=False,
    )
    assert success is True


@pytest.mark.asyncio
async def test_pusher_send_failure(httpx_mock):
    httpx_mock.add_response(
        url="https://oapi.dingtalk.com/robot/send?access_token=test",
        status_code=500,
        is_reusable=True,
    )
    pusher = DingTalkPusher(
        webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test"
    )
    success = await pusher.send(
        tweet=make_tweet(), display_name="Test User", is_a_stock=False,
    )
    assert success is False
