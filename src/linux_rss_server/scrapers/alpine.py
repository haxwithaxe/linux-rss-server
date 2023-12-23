"""Debian installer RSS feed generator."""

from typing import Generator

import bs4

from .. import log
from ..config import Config
from . import page


def scrape(config: Config, url: str) -> Generator[tuple[str, str], None, None]:
    """Find all the target files on the page at `url`."""
    content = page.get(url)
    if not content:
        return
    soup = bs4.BeautifulSoup(content, features='lxml')
    raise NotImplementedError()
