#!/usr/bin/env python3
"""Debian installer RSS feed generator."""

import re
from typing import Generator

import bs4

from ..config import Config
from . import page


def _by_version(
    config: Config,
    source: str,
    path: str,
) -> Generator[tuple[str, str], None, None]:
    """Scrape an individual Ubuntu version's page."""
    page_url = f'{source}/{path}'
    content = page.get(page_url)
    if not content:
        return
    soup = bs4.BeautifulSoup(content, features='lxml')
    for a in soup.findAll('a'):
        if a.attrs.get('href', '').endswith(config.file_extension):
            yield a.attrs['href'], f'{page_url}/{a.attrs["href"]}'


def scrape(config: Config, url: str):
    """Scrape the Ubuntu image repository for files."""
    content = page.get(url)
    if not content:
        return
    soup = bs4.BeautifulSoup(content, features='lxml')
    for a in soup.findAll('a'):
        href = a.attrs.get('href')
        matches_extension = re.match(r'\d+\.\d+(\.\d+)?/', a.text)
        if href == a.text and matches_extension:
            yield from _by_version(config, url, a.attrs['href'])
