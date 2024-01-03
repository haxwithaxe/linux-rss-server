"""Linux installer repo scraper runner."""

from . import debian, ubuntu

_SCRAPERS = {
    'debian': debian,
    'ubuntu': ubuntu,
}


def get(repo_type: str):
    """Get the scraper that corresponds to `repo_type`."""
    return _SCRAPERS[repo_type]
