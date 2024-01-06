"""Linux RSS Server configuration."""

import datetime
import enum
import os
import pathlib
import random
from dataclasses import dataclass
from typing import Iterable

import yaml

_APP_PATH = '/linux_rss_server'
DEFAULT_CHECK_EVERY_MULTIPLIER = 1
DEFAULT_CHECK_EVERY_UNIT = 'day'
DEFAULT_CONFIG = f'{_APP_PATH}/config.yml'
DEFAULT_FILE_EXTENSION = '.torrent'
DEFAULT_PORT = 56427
DEFAULT_RSS_CACHE = f'{_APP_PATH}/cache/rss_cache.rss'
DEFAULT_START_AT_HOUR = 12
DEFAULT_START_AT_MINUTE = 0


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
        for arch in self.arches or ['noarches']:
            url = self.url_format.format(arch=arch)
            if url not in urls:
                urls.append(url)
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

    def __post_init__(self):
        if self.unit not in ['week', 'day', 'hour', 'minute']:
            raise ValueError(
                f'Invalid value for `check_every.unit`: {self.unit}',
            )
        if self.multiplier < 0:
            raise ValueError(
                'Invalid value for `check_every.multiplier`: '
                f'{self.multiplier}',  # nofmt
            )
        if self.timedelta < datetime.timedelta(minutes=15):
            raise ValueError(
                'Don\'t be an mean. Checking every %s %ss (less than 15min) '
                'is abusive.',  # nofmt
                self.multiplier,
                self.unit,
            )

    @property
    def timedelta(self) -> datetime.timedelta:
        """The interval between checks."""
        if self.unit == 'week':
            return datetime.timedelta(weeks=self.multiplier)
        if self.unit == 'day':
            return datetime.timedelta(days=self.multiplier)
        if self.unit == 'hour':
            return datetime.timedelta(hours=self.multiplier)
        if self.unit == 'minute':
            return datetime.timedelta(minutes=self.multiplier)
        # Just in case
        raise ValueError(f'Invalid value for `check_every.unit`: {self.unit}')


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
        raise ValueError(
            'Invalid value for `check_every`: {config.get("check_every")}',
        )
    return CheckEvery(
        unit=unit or DEFAULT_CHECK_EVERY_UNIT,
        multiplier=int(multiplier or DEFAULT_CHECK_EVERY_MULTIPLIER),
    )


def _get_start_at(config: dict, overrides: dict) -> Time:
    hour = overrides.get('start_at_hour')
    minute = overrides.get('start_at_minute')
    if hour is None:
        hour = config.get('start_at', {}).get('hour', DEFAULT_START_AT_HOUR)
    if minute is None:
        minute = config.get('start_at', {}).get(
            'minute',
            DEFAULT_START_AT_MINUTE,
        )
    if isinstance(hour, str) and hour.lower() == 'random':
        hour = random.randint(0, 23)
    if isinstance(minute, str) and minute.lower() == 'random':
        minute = random.randint(0, 59)
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
    file_extension: str = DEFAULT_FILE_EXTENSION

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
                DEFAULT_CONFIG,
            ),
        )
        return cls.from_file(
            path=config_path,
            check_every=env.get('CHECK_EVERY_UNIT'),
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
        file_extension = overrides.get('file_extension')
        if file_extension is None:
            file_extension = config.get('file_extension', cls.file_extension)
        healthcheck_url = overrides.get('healthcheck_url')
        if not healthcheck_url:
            healthcheck_url = config.get('healthcheck_url')
        port = overrides.get('port')
        if not port:
            port = config.get('port', DEFAULT_PORT)
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
                DEFAULT_RSS_CACHE,
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
