# linux-rss-server
An RSS server and installer repo scraper. I've made this for my VM template build pipeline. It's intended to be used in a docker image.

## Usage
Using all defaults
```sh
docker run -d haxwithaxe/linux-rss-server:latest
```

Using a custom config file
```sh
docker run -d -v /path/to/config.yml:/linux_rss_server/config.yml haxwithaxe/linux-rss-server:latest
```

## Config
See [default-config.yml](default-config.yml) for a simple example.

- `arches` - A default list of architectures to use for repos. This list is overridden by `arches` given for individual repo specifications. If this is not specified and any repo doesn't have `arches` set it's assumed there is no formatting to be done to the URL for that repo.
- `check_every` - A string (just the unit) or dictionary specifying the unit and multiplier of the interval to scrape the repos for changes. If just the unit is given the default multiplier is used. This cannot be more frequent than every 15 minutes.
  - `unit` - The unit of the interval. Valid values are ``week``, ``day``, ``hour``, ``minute``. Anything less than 15 minutes is set to 15 minutes. There's no reason to check even that often, but maybe I'm wrong. Defaults to ``day``.
  - `multiplier` - The multiplier to modify the unit interval. Valid values are positive integers or positive floats. For example a multiplier of ``1.5`` with a unit of ``day`` will scrape the repos every 12 hours and a multiplier of ``0.5``with a unit of ``week`` will check every 3.5 days.
- `file_extension` - The extension on the filename for the desired files. This is used to identify the links to the desired file type. Defaults to ``.torrent``.
- `healthcheck_url` - A URL to a healthcheck ping. If no URL is given nothing is done. Defaults to no URL.
- `port` - The port for the RSS server to listen on. Defaults to ``56427``.
- `repos` - A list of repo specifications with the following options.
  - `arches` - A list of architectures to scrape. This overrides the default `arches` given at the root level. If this is not specified for any repo and the default isn't set it's assumed there is no formatting to be done to the URL.
  - `type` - The type of repo. Currently only ``debian`` and ``ubuntu`` are implemented. The repos don't need to be Debian or Ubuntu repos they just need to be structured the same. For instance the Tails repo has a similar enough structure to the Debian repo to use the ``debian`` repo type for Tails.
  - `url_format` - A format string for the repo URL to be used with `.format(arch=<one of the given arches>)`.
- `rss_cache` - The file to store the generated RSS feed in.
- `start_at` - A dictionary of a starting hour and minute. This is just the first check time. Subsequent check times are relative to this. Valid values are positive integers (limits depend on the unit of time) or the string ``random``. If ``random`` is given a random value will be selected for that option.
  - `hour` - The hour of the day to start checking the repos. Valid values are ``0`` to ``23``. Defaults to ``12``.
  - `minute` - The minute of the hour to start checking the repos. Valid values are ``0`` to ``59``. Defaults to ``0``.

### Example Config
See [default-config.yml](default-config.yml) for a working example. The example below shows a config with no defaults.
```yaml
---
repos:
  - url_format: 'http://cd.example.com/{arch}'
    arches:
      - amd64
      - i386
      - arm64
    type: debian
check_every:
  unit: hour
  multiplier: 193
healthcheck_url: http://healthcheck.example.com/ping/rss-feed-updated
port: 792
rss_cache: /some/path/to/a/cache/file.rss
start_at:
  hour: 13
  minute: 57
file_extension: .test-extension
```
## Environment Variables
- `LOG_LEVEL` - The desired log level. The valid values are ``debug``, ``info``, ``warning``, ``error``, ``critical``. Defaults to ``error``.
- `CHECK_EVERY_UNIT` - The unit of the interval to scrape the repos. Overrides `check_every.unit`. See `check_every.unit` above.
- `CHECK_EVERY_MUL` - The multiplier of the interval to scrape the repos. Overrides `check_every.multiplier`. See `check_every.multiplier` above.
- `DEFAULT_ARCHES` - A comma separated list of the default CPU architectures to grab torrent/image links for.
- `FILE_EXTENSION` - The extension on the filename for the desired files. See `file_extension` above.
- `PORT` - The port for the RSS server to listen on. See `port` above.
- `RSS_CACHE` - The location of the RSS file on disk. See `rss_cache` above.
- `START_HOUR` - The hour of the day to begin scraping. See `start_at.hour` above.
- `START_MINUTE` - The minute of the hour to begin scraping. See `start_at.minute` above.
- `CONFIGFILE` - The path to this application's config file. Defaults to ``/linux_rss_server/config.yml``.
