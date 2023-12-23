"""Run the daemon that scrapes repos and serves RSS."""

import datetime
import http
import logging
import os
import selectors
import socket
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn, _ServerSelector

import requests

from . import feed, log, scrapers
from .config import Config


def _ping_healthcheck(url):
    if not url:
        return
    resp = requests.get(url)
    if resp.status >= 300:
        resp = requests.get(url)
        if resp.status >= 300:
            log.error('Failed to ping healthcheck: %s', url)


class ScraperThread(threading.Thread):
    """A thread to manage the scraper.

    Arguments:
        config: The application configuration.
        stop_all: The `threading.Event` that will signal all the parts of the
            application to stop.
    """

    def __init__(self, config: Config, stop_all: threading.Event):
        threading.Thread.__init__(self, daemon=True)
        self.__stop = threading.Event()
        self.__stop_all = stop_all
        self.config = config
        if self.config.check_every.unit == 'week':
            if self.config.check_every.multiplier >= 1:
                self.check_every = datetime.timedelta(
                    weeks=1 * self.config.check_every.multiplier,
                )
            elif self.config.check_every.multiplier < 1:
                self.check_every = datetime.timedelta(
                    days=int(7 / self.config.check_every.multiplier),
                )
        if self.config.check_every.unit == 'day':
            if self.config.check_every.multiplier >= 1:
                self.check_every = datetime.timedelta(
                    days=1 * self.config.check_every.multiplier,
                )
            elif self.config.check_every.multiplier < 1:
                self.check_every = datetime.timedelta(
                    hours=int(24 / self.config.check_every.multiplier),
                )
        if self.config.check_every.unit == 'hour':
            if self.config.check_every.multiplier >= 1:
                self.check_every = datetime.timedelta(
                    hours=1 * self.config.check_every.multiplier,
                )
            elif self.config.check_every.multiplier < 1:
                self.check_every = datetime.timedelta(
                    minutes=int(7 / self.config.check_every.multiplier),
                )
        if self.config.check_every.unit == 'minute':
            if self.config.check_every.multiplier >= 1:
                self.check_every = datetime.timedelta(
                    minutes=1 * self.config.check_every.multiplier,
                )
            else:
                self.check_every = datetime.timedelta(
                    minutes=1,
                )

    def halt(self, error: Exception):
        """Stop everything gracefully."""
        self.__stop.set()
        self.__stop_all.set()
        self.exception = error

    def run(self):
        """Run the RSS feed generator thread."""
        try:
            self._run_loop()
        except Exception as err:
            log.debug(
                'Unexpected error in the scraper thread: %s: %s',
                err.__class__.__name__,
                err,
            )
            self.halt(err)

    def _generate_feed(self):
        rss_feed = feed.Feed(self.config)
        rss_feed.load()
        for repo in self.config.repos:
            scraper = scrapers.get(repo.type)
            for url in repo:
                for filename, file_url in scraper.scrape(self.config, url):
                    rss_feed.append(filename, file_url)
        rss_feed.dump()

    def _run_loop(self):
        while not self.__stop.is_set():
            self._generate_feed()
            _ping_healthcheck(self.config.healthcheck_url)
            now = datetime.datetime.now()
            then = now + self.check_every
            then = datetime.datetime(
                year=then.year,
                month=then.month,
                day=then.day,
                hour=self.config.start_at.hour,
                minute=self.config.start_at.minute,
            )
            time.sleep((then - now).seconds)


def _request_handler_factory(config: Config) -> SimpleHTTPRequestHandler:
    class RequestHandler(SimpleHTTPRequestHandler):

        _config = config

        def do_GET(self):
            self.send_response(http.HTTPStatus.OK)
            self.send_header('Content-Type', 'application/rss+xml')
            self.end_headers()
            self.wfile.write(self._config.rss_cache.read_bytes())
            self.wfile.flush()

    return RequestHandler


class _Server(ThreadingMixIn, HTTPServer):
    def serve_forever(
        self,
        poll_interval: float = 0.5,
        stop: threading.Event = None,
    ):
        """Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
        # Taken straight from `socketserver.BaseServer`.
        # Added `threading.Event` `stop` to allow asynchronous shutdown.
        self._BaseServer__is_shut_down.clear()
        try:
            # XXX: Consider using another file descriptor or connecting to the
            # socket to wake this up instead of polling. Polling reduces our
            # responsiveness to a shutdown request and wastes cpu at all other
            # times.
            with _ServerSelector() as selector:
                selector.register(self, selectors.EVENT_READ)

                while not (self._BaseServer__shutdown_request
                           and stop.is_set()):  # nofmt
                    ready = selector.select(poll_interval)
                    # bpo-35017: shutdown() called during select(), exit
                    #  immediately.
                    if self._BaseServer__shutdown_request:
                        break
                    if ready:
                        self._handle_request_noblock()
                    self.service_actions()
        finally:
            self._BaseServer__shutdown_request = False
            self._BaseServer__is_shut_down.set()


def main():
    """Entrypoint for the server.

    Environment:
        LOG_LEVEL: The desired log level. Defaults to ``error``. The valid
            values are ``debug``, ``info``, ``warning``, ``error``,
            ``critical``.
        CHECK_EVERY: The unit of the interval to scrape the repos for changes.
            Valid values are ``month``, ``day``, ``hour``, ``minute``. Defaults
            to ``hour``.
        CHECK_EVERY_MUL: The multiplier of the. This can be a positive `float`
            or positive `int`. Defaults to ``1``.
        DEFAULT_ARCHES: A comma separated list of CPU architectures to grab
            torrent/image links for.
        FILE_EXTENSION: The extension on the filename for the desired files.
            Defaults to ``.torrent``.
        PORT: The port for the RSS server to listen on. Defaults to # FIXME.
        RSS_CACHE: The location of the RSS file on disk.
        START_HOUR: The hour of the day to begin scraping. Defaults to
            ``12``.
        START_MINUTE: The minute of the hour to begin scraping. Defaults to
            ``0``.
        LINUX_RSS_SERVER_CONFIGFILE: The path to this application's config file.
            Defaults to ``/linux_rss_server/config.yml``.
    """
    log_level = os.environ.get('LOG_LEVEL', 'error')
    if not hasattr(logging, log_level.upper()):
        log.critical('Invalid value for LOG_LEVEL: %s', log_level)
        sys.exit(1)
    log.setLevel(getattr(logging, log_level.upper()))
    config = Config.from_env()
    stop_all = threading.Event()
    scraper = ScraperThread(config, stop_all)
    scraper.start()
    request_handler = _request_handler_factory(config)
    server = _Server(
        ('0.0.0.0', config.port),
        request_handler,
    )
    log.info(
        'Serving RSS on %s:%s',
        socket.gethostname(),
        config.port,
    )
    sys.stdout.flush()
    server.serve_forever(stop=stop_all)
    scraper.join()
    log.info('Stopped server')
    if scraper.exception:
        log.error('Error in scraper', exc_info=scraper.exception)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
