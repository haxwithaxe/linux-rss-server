import pathlib

import feedparser
import pytest

from linux_rss_server.config import Config
from linux_rss_server.feed import Feed


def _test_fails_on_something(tmp_path: pathlib.Path):
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
    with pytest.raises():
        feed.load()
