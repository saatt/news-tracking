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

    return Config(
        authors=raw.get("authors", []),
        nitter_instances=raw.get("nitter_instances", []),
        dingtalk_webhook_url=raw.get("dingtalk", {}).get("webhook_url", ""),
        a_stock_keywords=raw.get("a_stock_keywords", []),
        poll_interval_seconds=raw.get("poll_interval_seconds", 60),
        database_path=raw.get("database_path", "data/tweets.db"),
    )
