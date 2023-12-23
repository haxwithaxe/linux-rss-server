"""Debian installer RSS feed generator."""

import os
from typing import Generator

import bs4

from . import page
from ..config import Config


def scrape(config: Config, url: str) -> Generator[str, None, None]:
    """Find all the target files on the page at `url`."""
    content = page.get(url)
    if not content:
        return
    soup = bs4.BeautifulSoup(content, features='lxml')
    for tr in soup.find_all('tr'):
        try:
            _, ext = os.path.splitext(tr.td.a.attrs.get('href', ''))
        except AttributeError:
            continue
        if ext.strip('.') == config.file_extension.strip('.'):
            filename = tr.td.a.attrs['href']
            yield filename, f'{url}/{filename}'
