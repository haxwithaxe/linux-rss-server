"""Linux RSS Server configuration."""

import enum
import os
import pathlib
from dataclasses import dataclass

import yaml


class RepoType(enum.StrEnum):
    """A selection of repo types with scrapers."""

    debian = enum.auto()
    ubuntu = enum.auto()
    alpine = enum.auto()


@dataclass
class Repo:
    """Repo specification."""

    url_format: str
    arches: list[str]
    type: RepoType

    def __iter__(self) -> iter[str]:
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
                '/linux_rss_server/config.yml',
            ),
        )
        return cls.from_file(
            path=config_path,
            check_every=env.get('CHECK_EVERY'),
            check_every_multiplier=env.get('CHECK_EVERY_MUL'),
            default_arches=default_arches,
            file_extension=env.get('FILE_EXTENSION'),
            port=env.get('PORT'),
            rss_cache=env.get('RSS_CACHE'),
            start_at_hour=env.get('START_HOUR'),
            start_at_minute=env.get('START_MINUTE'),
        )

    def from_file(cls, path: pathlib.Path, **overrides) -> 'Config':
        """Load the config from a yaml file."""
        config = yaml.safe_load(path.read_text())

        def _cascading_get(key, override=None, default=None):
            override_key = override or key
            return overrides.get(override_key) or config.get(key, default)

        if isinstance(config.get('check_every'), dict):
            unit = overrides.get('check_every') or config['check_every']['unit']
            multiplier = overrides.get('check_every_multiplier') or config[
                'check_every'
            ].get('multiplier', 1)
            check_every = CheckEvery(unit, multiplier)
        elif isinstance(config.get('check_every'), str):
            check_every = CheckEvery(
                _cascading_get('check_every', default='day'),
                1,
            )
        elif config.get('check_every') is not None:
            # Don't let bad configs pass even if there is an override.
            check_every = config.get('check_every')
            raise ValueError('Invalid value for `check_every`: {check_every}')
        else:
            check_every = CheckEvery(
                unit=_cascading_get('check_every', default='day'),
                multiplier=int(overrides.get('check_every_multiplier') or 1),
            )
        default_arches = _cascading_get('arches')
        repos = []
        for repo in config['repos']:
            repos.append(
                Repo(
                    repo['url'],
                    repo.get('arches', default_arches),
                    RepoType(repo.get('type')),
                ),
            )
        rss_cache = pathlib.Path(
            _cascading_get(
                'rss_cache',
                default='/rss_server/cache/rss_cache.rss',
            ),
        )
        rss_cache.parent.mkdir(exist_ok=True)
        start_at_config = config.get('start_at', {})
        start_at_hour = overrides.get('start_at_hour') or start_at_config.get(
            'hour', 12
        )
        start_at_minute = overrides.get('start_at_minute')
        if start_at_minute is None:
            start_at_minute = start_at_config.get('minute', 0)
        start_at = Time(
            hour=int(start_at_hour),
            minute=int(start_at_minute),
        )
        return cls(
            check_every=check_every,
            file_extension=_cascading_get('file_extension', default='.torrent'),
            healthcheck_url=_cascading_get('healthcheck_url'),
            port=int(_cascading_get('port', default=56427)),
            repos=repos,
            rss_cache=rss_cache,
            start_at=start_at,
        )
