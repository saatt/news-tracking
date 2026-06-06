import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Config:
    authors: list[dict]
    nitter_instances: list[str]
    dingtalk_webhook_url: str
    a_stock_keywords: list[str]
    poll_interval_seconds: int
    database_path: str


def load_config(path: str) -> Config:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Config file is empty: {path}")

    dingtalk = raw.get("dingtalk")
    if not isinstance(dingtalk, dict):
        raise ValueError(
            f"Config 'dingtalk' must be a dict, got {type(dingtalk).__name__}"
        )

    webhook_url = (
        os.environ.get("DINGTALK_WEBHOOK_URL")
        or dingtalk.get("webhook_url", "")
    )

    poll_interval = raw.get("poll_interval_seconds", 60)
    if not isinstance(poll_interval, int) or poll_interval <= 0:
        raise ValueError(
            f"Config 'poll_interval_seconds' must be a positive integer, "
            f"got {poll_interval!r}"
        )

    return Config(
        authors=raw.get("authors", []),
        nitter_instances=raw.get("nitter_instances", []),
        dingtalk_webhook_url=webhook_url,
        a_stock_keywords=raw.get("a_stock_keywords", []),
        poll_interval_seconds=poll_interval,
        database_path=raw.get("database_path", "data/tweets.db"),
    )
