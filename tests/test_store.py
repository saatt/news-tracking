import pytest
import tempfile
import os
from src.store import TweetStore, DuplicateTweetError, StoreNotInitializedError


@pytest.fixture
async def store():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
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
    exists = await store.exists("__nonexistent__")
    assert exists is False


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
    with pytest.raises(DuplicateTweetError):
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
async def test_save_with_a_stock_true(store):
    await store.init()
    await store.save(
        tweet_id="astock_1",
        author="testuser",
        content="A股大涨",
        link="https://x.com/testuser/status/astock1",
        published="2026-06-06T14:30:00",
        is_a_stock=True,
        is_reply=True,
    )
    exists = await store.exists("astock_1")
    assert exists is True


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
async def test_get_latest_published_filters_by_author(store):
    await store.init()
    await store.save(
        tweet_id="a1",
        author="user_a",
        content="A",
        link="https://x.com/user_a/status/1",
        published="2026-06-06T10:00:00",
        is_a_stock=False,
        is_reply=False,
    )
    await store.save(
        tweet_id="a2",
        author="user_b",
        content="B",
        link="https://x.com/user_b/status/1",
        published="2026-06-06T14:00:00",
        is_a_stock=False,
        is_reply=False,
    )
    result = await store.get_latest_published("user_a")
    assert result == "2026-06-06T10:00:00"


@pytest.mark.asyncio
async def test_uninitialized_store_raises(store):
    with pytest.raises(StoreNotInitializedError):
        await store.exists("tweet_123")


@pytest.mark.asyncio
async def test_close_disables_store(store):
    await store.init()
    await store.close()
    with pytest.raises(StoreNotInitializedError):
        await store.exists("tweet_123")
