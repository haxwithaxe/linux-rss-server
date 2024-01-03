"""Linux RSS Server configuration."""

import enum
import os
import pathlib
import random
from dataclasses import dataclass
from typing import Iterable

import yaml

_APP_PATH = '/linux_rss_server'


class RepoType(enum.StrEnum):
    """A selection of repo types with scrapers."""

    debian = enum.auto()
    ubuntu = enum.auto()


@dataclass
class Repo:
    """Repo specification."""

    url_format: str
    arches: list[str]
    type: RepoType

    def __iter__(self) -> Iterable[str]:
        """Return an iterable of URLs based on `url_format` and `arches`."""
        urls = []
        for arch in self.arches:
            urls.append(self.url_format.format(arch=arch))
        return iter(urls)


@dataclass
class Time:
    """Generic time specification."""

    hour: int
    minute: int


@dataclass
class CheckEvery:
    """Check every interval specification."""

    unit: str
    multiplier: float


def _get_check_every(config: dict, overrides: dict) -> CheckEvery:
    unit = overrides.get('check_every')
    multiplier = overrides.get('check_every_multiplier')
    if unit is not None and multiplier is not None:
        # Just skip everything if both overrides are set
        return CheckEvery(unit, int(multiplier))
    if isinstance(config.get('check_every'), dict):
        if unit is None:
            unit = config['check_every']['unit']
        if multiplier is None:
            multiplier = config['check_every'].get('multiplier')
    elif isinstance(config.get('check_every'), str) and unit is None:
        unit = config['check_every']
    elif config.get('check_every') is not None:
        # don't let bad configs pass even if there is an override.
        check_every = config.get('check_every')
        raise ValueError('Invalid value for `check_every`: {check_every}')
    return CheckEvery(unit=unit or 'day', multiplier=int(multiplier or 1))


def _get_start_at(config: dict, overrides: dict) -> Time:
    hour = overrides.get('start_at_hour')
    minute = overrides.get('start_at_minute')
    if hour is None:
        hour = config.get('start_at', {}).get('hour', 12)
    if minute is None:
        minute = config.get('start_at', {}).get('minute', 0)
    if isinstance(hour, str) and hour.lower() == 'random':
        hour = random.randint(0, 23)
    if isinstance(minute, str) and minute.lower() == 'random':
        minute = random.randint(0, 60)
    return Time(
        hour=int(hour),
        minute=int(minute),
    )

@dataclass
class Config:
    """RSS feed generator and server configuration."""

    check_every: CheckEvery
    healthcheck_url: str
    port: int
    repos: list[Repo]
    rss_cache: pathlib.Path
    start_at: Time
    file_extension: str = '.torrent'

    @classmethod
    def from_env(cls, env: dict = None) -> 'Config':
        """Load the config from environment variables."""
        env = env or os.environ
        arches_str = env.get('DEFAULT_ARCHES')
        default_arches = None
        if arches_str:
            default_arches = [x.strip() for x in arches_str.split(',')]
        config_path = pathlib.Path(
            env.get(
                'LINUX_RSS_SERVER_CONFIGFILE',
                f'{_APP_PATH}/config.yml',
            ),
        )
        return cls.from_file(
            path=config_path,
            check_every=env.get('CHECK_EVERY'),
            check_every_multiplier=env.get('CHECK_EVERY_MUL'),
            default_arches=default_arches,
            healthcheck_url=env.get('HEALTHCHECK_URL'),
            file_extension=env.get('FILE_EXTENSION'),
            port=env.get('PORT'),
            rss_cache=env.get('RSS_CACHE'),
            start_at_hour=env.get('START_AT_HOUR'),
            start_at_minute=env.get('START_AT_MINUTE'),
        )

    @classmethod
    def from_file(cls, path: pathlib.Path, **overrides) -> 'Config':
        """Load the config from a yaml file."""
        config = yaml.safe_load(path.read_text())
        print('config', config)
        print('overrides', overrides)
        file_extension = overrides.get('file_extension')
        if file_extension is None:
            file_extension = config.get('file_extension', cls.file_extension)
        healthcheck_url = overrides.get('healthcheck_url')
        if not healthcheck_url:
            healthcheck_url = config.get('healthcheck_url')
        port = overrides.get('port')
        if not port:
            port = config.get('port', 56427)
        default_arches = overrides.get('default_arches')
        if not default_arches:
            default_arches = config.get('arches', [])
        repos = []
        for repo in config['repos']:
            repos.append(
                Repo(
                    repo['url_format'],
                    repo.get('arches', default_arches),
                    RepoType(repo.get('type').lower()),
                ),
            )
        rss_cache_filename = overrides.get('rss_cache')
        if not rss_cache_filename:
            rss_cache_filename = config.get(
                'rss_cache',
                f'{_APP_PATH}/cache/rss_cache.rss',
            )
        rss_cache = pathlib.Path(rss_cache_filename)
        rss_cache.parent.mkdir(exist_ok=True)
        return cls(
            check_every=_get_check_every(config, overrides),
            file_extension=file_extension,
            healthcheck_url=healthcheck_url,
            port=int(port),
            repos=repos,
            rss_cache=rss_cache,
            start_at=_get_start_at(config, overrides),
        )
