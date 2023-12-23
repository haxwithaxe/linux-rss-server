"""Debian installer RSS feed generator."""

import time

import requests

from .. import log


def _get(url: str) -> requests.Response:
    log.debug('Getting %s', url)
    try:
        page = requests.get(url)
    except requests.exceptions.ConnectionError as err:
        # Warning since it's not fatal to the workflow unless it happens again.
        log.warning('Error Connectiong to the server "%s": %s', url, err)
        return None
    if not page or not page.ok:
        log.error('Could not get "%s" for this reason: %s', url, page.reason)
        return None
    log.debug('Got: %s %s', url, page.reason)
    return page


def get(url, attempts: int = 2) -> str:
    """Attempt to fetch a webpage."""
    tries = 0
    while tries < attempts and not (page := _get(url)):
        tries += 1
        time.sleep(1)
    if not page:  # Too many errors, skip to the next url
        log.error('Failed to connect to the server for "%s" twice.', url)
        return ''
    return page.content
