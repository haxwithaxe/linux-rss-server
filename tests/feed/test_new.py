"""Tests for creating new RSS cache."""

import pathlib

from linux_rss_server.config import Config
from linux_rss_server.feed import Feed


def test_create_new_feed(tmp_path: pathlib.Path):
    """Test creating a new RSS cache."""
    rss_cache = tmp_path.joinpath('feed.rss')
    config = Config(
        check_every=None,
        healthcheck_url=None,
        port=None,
        repos=None,
        rss_cache=rss_cache,
        start_at=None,
        file_extension=None,
    )
    feed = Feed(config)
    feed.load()  # This should be a noop. Calling just in case.
    feed.append(name='test name', url='http://test.example.com')
    feed.dump()
    assert rss_cache.exists()
