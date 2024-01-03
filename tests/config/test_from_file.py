import pathlib

import pytest

from linux_rss_server.config import Config
from linux_rss_server.feed import Feed

NO_DEFAULTS_CONFIG = '''\
---
repos:
  - url_format: 'http://test0.example.com/{{arch}}'
    arches:
      - amd64
    type: debian
check_every:
  unit: hour
  multiplier: 193
healthcheck_url: http://healthcheck.example.com
port: 792
rss_cache: '{rss_cache}'
start_at:
  hour: 13
  minute: 57
file_extension: .test-extension
'''

SOME_DEFAULTS_CONFIG = '''\
---
arches:
  - amd64
check_every: hour
repos:
  - url_format: 'http://test0.example.com/{{arch}}'
    type: debian
rss_cache: '{rss_cache}'
'''


def test_loads_from_file_no_defaults(tmp_path: pathlib.Path):
    config_file = tmp_path.joinpath('test_server_config.yml')
    rss_cache = tmp_path.joinpath('test_server_nosuch.rss')
    assert not rss_cache.exists(), 'The RSS cache file exists something is wrong'
    config_file.write_text(
        NO_DEFAULTS_CONFIG.format(rss_cache=str(rss_cache.absolute()))
    )
    config = Config.from_file(path=config_file)
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


def test_loads_from_file_some_defaults(tmp_path: pathlib.Path):
    config_file = tmp_path.joinpath('test_server_config.yml')
    rss_cache = tmp_path.joinpath('test_server_nosuch.rss')
    assert not rss_cache.exists(), 'The RSS cache file exists something is wrong'
    config_file.write_text(
        SOME_DEFAULTS_CONFIG.format(rss_cache=str(rss_cache.absolute()))
    )
    config = Config.from_file(path=config_file)
    assert config.check_every.unit == 'hour'
    assert config.check_every.multiplier == 1
    assert config.healthcheck_url is None
    assert config.port == 56427
    assert config.repos[0].url_format == 'http://test0.example.com/{arch}'
    assert config.repos[0].arches == ['amd64']
    assert config.repos[0].type == 'debian'
    assert list(config.repos[0]) == ['http://test0.example.com/amd64']
    assert config.rss_cache == rss_cache
    assert config.start_at.hour == 12
    assert config.start_at.minute == 0
    assert config.file_extension == '.torrent'
