"""Linux installer RSS feed generator."""

import feedparser
from feedgen.feed import FeedGenerator

from . import log
from .config import Config


class Feed:
    """Feed parser and generator."""

    def __init__(self, config: Config):
        self.config = config
        self.entries = []
        self.feed = FeedGenerator()
        self.feed.title('ISO Release Feed')
        self.feed.description('A feed of Linux installer torrent files.')
        self.feed.link(href='http://localhost')

    def append(self, name: str, url: str):
        """Populate a feed entry given the filename and source URL."""
        if url in self.entries:
            return
        log.debug('Added %s: %s', name, url)
        entry = self.feed.add_entry()
        entry.title(name)
        entry.content(url)
        entry.description(name)
        entry.link(href=url)
        self.entries.append(url)

    def load(self) -> list[str]:
        """Load the previously generated RSS file.

        Returns:
            A tuple of the populated FeedGenerator and a list of the entry
            links.
        """
        if not self.config.rss_cache.exists():
            log.debug('No RSS cache at %s', self.config.rss_cache)
            return
        log.debug(
            'Loading entries from existing cache at %s',
            self.config.rss_cache,
        )
        parsed = feedparser.parse(self.config.rss_cache)
        for item in parsed.entries:
            entry = self.feed.add_entry()
            entry.title(item.title)
            entry.description(item.description)
            entry.content(item.content[0]['value'])
            entry.link(href=item.link)
            self.entries.append(item.link)

    def dump(self):
        """Save the feed to disk."""
        self.feed.rss_file(self.config.rss_cache, pretty=True)
