import os
import tempfile

import pytest

from src.config import load_config

SAMPLE_YAML = """
authors:
  - username: "testuser"
    display_name: "Test User"

nitter_instances:
  - "https://nitter.net"
  - "https://nitter.example.com"

dingtalk:
  webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=abc123"

a_stock_keywords:
  - "A股"
  - "涨停"
  - "跌停"

poll_interval_seconds: 60

database_path: "data/tweets.db"
"""


def test_load_config_parses_all_fields() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_YAML)
        path = f.name

    try:
        config = load_config(path)

        assert len(config.authors) == 1
        assert config.authors[0]["username"] == "testuser"
        assert config.authors[0]["display_name"] == "Test User"

        assert len(config.nitter_instances) == 2
        assert config.nitter_instances[0] == "https://nitter.net"

        assert config.dingtalk_webhook_url == (
            "https://oapi.dingtalk.com/robot/send?access_token=abc123"
        )

        assert config.a_stock_keywords == ["A股", "涨停", "跌停"]
        assert config.poll_interval_seconds == 60
        assert config.database_path == "data/tweets.db"
    finally:
        os.unlink(path)


def test_load_config_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_file.yaml")


def test_load_config_empty_file_raises() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("")
        path = f.name

    try:
        with pytest.raises(ValueError, match="empty"):
            load_config(path)
    finally:
        os.unlink(path)


def test_load_config_defaults_applied_when_keys_missing() -> None:
    minimal_yaml = """
    dingtalk:
      webhook_url: "https://example.com/webhook"
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(minimal_yaml)
        path = f.name

    try:
        config = load_config(path)
        assert config.authors == []
        assert config.nitter_instances == []
        assert config.a_stock_keywords == []
        assert config.poll_interval_seconds == 60
        assert config.database_path == "data/tweets.db"
    finally:
        os.unlink(path)


def test_load_config_rejects_negative_poll_interval() -> None:
    bad_yaml = """
    dingtalk:
      webhook_url: "https://example.com/webhook"
    poll_interval_seconds: -5
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(bad_yaml)
        path = f.name

    try:
        with pytest.raises(ValueError, match="positive integer"):
            load_config(path)
    finally:
        os.unlink(path)


def test_load_config_rejects_non_dict_dingtalk() -> None:
    bad_yaml = """
    dingtalk: "not_a_dict"
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(bad_yaml)
        path = f.name

    try:
        with pytest.raises(ValueError, match="must be a dict"):
            load_config(path)
    finally:
        os.unlink(path)
