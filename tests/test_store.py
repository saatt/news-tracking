import pytest
import tempfile
import os
from src.store import TweetStore


@pytest.fixture
async def store():
    db_path = tempfile.mktemp(suffix=".db")
    s = TweetStore(db_path)
    yield s
    await s.close()
    try:
        os.unlink(db_path)
    except PermissionError:
        pass


@pytest.mark.asyncio
async def test_init_creates_table(store):
    await store.init()
    async with store._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='tweets'"
    ) as cursor:
        row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "tweets"


@pytest.mark.asyncio
async def test_exists_returns_false_for_new_tweet(store):
    await store.init()
    exists = await store.exists("tweet_123")
    assert exists is False


@pytest.mark.asyncio
async def test_save_and_exists(store):
    await store.init()
    await store.save(
        tweet_id="tweet_123",
        author="testuser",
        content="Hello world",
        link="https://x.com/testuser/status/123",
        published="2026-06-06T14:30:00",
        is_a_stock=False,
        is_reply=False,
    )
    exists = await store.exists("tweet_123")
    assert exists is True


@pytest.mark.asyncio
async def test_save_duplicate_raises(store):
    await store.init()
    await store.save(
        tweet_id="tweet_456",
        author="testuser",
        content="Test",
        link="https://x.com/testuser/status/456",
        published="2026-06-06T14:30:00",
        is_a_stock=False,
        is_reply=False,
    )
    with pytest.raises(Exception):
        await store.save(
            tweet_id="tweet_456",
            author="testuser",
            content="Test again",
            link="https://x.com/testuser/status/456",
            published="2026-06-06T15:00:00",
            is_a_stock=False,
            is_reply=False,
        )


@pytest.mark.asyncio
async def test_get_latest_published_returns_none_when_empty(store):
    await store.init()
    result = await store.get_latest_published("testuser")
    assert result is None


@pytest.mark.asyncio
async def test_get_latest_published_returns_max_date(store):
    await store.init()
    await store.save(
        tweet_id="old",
        author="testuser",
        content="Old",
        link="https://x.com/testuser/status/old",
        published="2026-06-06T10:00:00",
        is_a_stock=False,
        is_reply=False,
    )
    await store.save(
        tweet_id="new",
        author="testuser",
        content="New",
        link="https://x.com/testuser/status/new",
        published="2026-06-06T12:00:00",
        is_a_stock=False,
        is_reply=False,
    )
    result = await store.get_latest_published("testuser")
    assert result == "2026-06-06T12:00:00"


@pytest.mark.asyncio
async def test_close(store):
    await store.init()
    await store.close()
    with pytest.raises(Exception):
        await store.exists("tweet_123")
