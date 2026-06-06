import aiosqlite


class TweetStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def init(self):
        self._conn = await aiosqlite.connect(self.db_path)
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                link TEXT NOT NULL,
                published TEXT NOT NULL,
                is_a_stock INTEGER NOT NULL DEFAULT 0,
                is_reply INTEGER NOT NULL DEFAULT 0,
                pushed_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        await self._conn.commit()

    async def exists(self, tweet_id: str) -> bool:
        cursor = await self._conn.execute(
            "SELECT 1 FROM tweets WHERE id = ?", (tweet_id,)
        )
        row = await cursor.fetchone()
        return row is not None

    async def save(
        self,
        tweet_id: str,
        author: str,
        content: str,
        link: str,
        published: str,
        is_a_stock: bool,
        is_reply: bool,
    ):
        await self._conn.execute(
            """
            INSERT INTO tweets (id, author, content, link, published, is_a_stock, is_reply)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tweet_id,
                author,
                content,
                link,
                published,
                1 if is_a_stock else 0,
                1 if is_reply else 0,
            ),
        )
        await self._conn.commit()

    async def get_latest_published(self, author: str) -> str | None:
        cursor = await self._conn.execute(
            "SELECT MAX(published) FROM tweets WHERE author = ?", (author,)
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] else None

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None
