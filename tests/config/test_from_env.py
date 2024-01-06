"""Tests to verify that the config loads from env vars."""

import pathlib

from linux_rss_server.config import Config

MINIMAL_CONFIG = '''\
---

repos:
  - url_format: 'http://test0.example.com/{arch}'
    arches:
      - amd64
    type: debian
'''


def test_loads_from_env_with_no_defaults(tmp_path: pathlib.Path):
    """Verify the config loads when given all values."""
    config_file = tmp_path.joinpath('test_server_config.yml')
    rss_cache = tmp_path.joinpath('test_server_nosuch.rss')
    assert (
        not rss_cache.exists()
    ), 'The RSS cache file exists something is wrong'  # nofmt

    config_file.write_text(MINIMAL_CONFIG)
    env = dict(
        CHECK_EVERY_UNIT='hour',
        CHECK_EVERY_MUL='193',
        HEALTHCHECK_URL='http://healthcheck.example.com',
        PORT='792',
        RSS_CACHE=str(rss_cache),
        START_AT_HOUR='13',
        START_AT_MINUTE='57',
        FILE_EXTENSION='.test-extension',
        CONFIGFILE=str(config_file.absolute()),
    )
    config = Config.from_env(env)
    assert config.check_every.unit == 'hour'
    assert config.check_every.multiplier == 193
    assert config.healthcheck_url == 'http://healthcheck.example.com'
    assert config.port == 792
    assert config.repos[0].url_format == 'http://test0.example.com/{arch}'
    assert config.repos[0].arches == ['amd64']
    assert config.repos[0].type == 'debian'
    assert list(config.repos[0]) == ['http://test0.example.com/amd64']
    assert config.rss_cache == rss_cache
    assert config.start_at.hour == 13
    assert config.start_at.minute == 57
    assert config.file_extension == '.test-extension'
