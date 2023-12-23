
import pathlib

import pytest

from linux_rss_server.feed import Feed
from linux_rss_server.config import Config

MOCK_RSS_FEED = '''\
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
	<channel>
		<title>test title</title>
		<description>test description</description>
		<link>http://test.example.com/test_link</link>
		<language>en-us</language>
			<item>
				<title>test item title 1</title>
				<link>http://test.example.com/test_item_link_1</link>
				<description>test item description 1</description>
				<pubDate>Thu, 21 Dec 2023 20:14 GMT</pubDate>
				<content>http://test.example.com/test_item_link_1</content>
			</item>
			<item>
				<title>test item title 2</title>
				<link>http://test.example.com/test_item_link_2</link>
				<description>test item description 2</description>
				<pubDate>Thu, 21 Dec 2023 20:13 GMT</pubDate>
				<content>http://test.example.com/test_item_link_2</content>
			</item>
			<item>
				<title>test item title 3</title>
				<link>http://test.example.com/test_item_link_3</link>
				<description>test item description 3</description>
				<pubDate>Thu, 21 Dec 2023 20:12 GMT</pubDate>
				<content>http://test.example.com/test_item_link_3</content>
			</item>
	</channel>
</rss>
'''

def test_appends_to_existing_feed(tmp_path: pathlib.Path):
    rss_cache = tmp_path.joinpath('feed.rss')
    rss_cache.write_text(MOCK_RSS_FEED)
    config = Config(check_every=None, healthcheck_url=None, port=None, repos=None, rss_cache=rss_cache, start_at=None, file_extension=None,)
    feed = Feed(config)
    feed.load()
    feed.append(name='test append new name', url='http://test.example.com/test_append_new_url')
    feed.dump()
    assert rss_cache.exists()
    # Appended entry
    assert feed.feed.entries[0].content == 'http://test.example.com/test_append_new_url'
    assert feed.feed.entries[0].description == 'test append new name'
    assert feed.feed.entries[0].link == 'http://test.example.com/test_append_new_url'
    assert feed.feed.entries[0].title == 'test append new name'
    # Existing entries
    assert feed.feed.entries[1].content == 'http://test.example.com/test_item_link_1'
    assert feed.feed.entries[1].description == 'test item description 1'
    assert feed.feed.entries[1].link == 'http://test.example.com/test_item_link_1'
    assert feed.feed.entries[1].title == 'test item title 1'

    assert feed.feed.entries[2].content == 'http://test.example.com/test_item_link_2'
    assert feed.feed.entries[2].description == 'test item description 2'
    assert feed.feed.entries[2].link == 'http://test.example.com/test_item_link_2'
    assert feed.feed.entries[2].title == 'test item title 2'

    assert feed.feed.entries[3].content == 'http://test.example.com/test_item_link_3'
    assert feed.feed.entries[3].description == 'test item description 3'
    assert feed.feed.entries[3].link == 'http://test.example.com/test_item_link_3'
    assert feed.feed.entries[3].title == 'test item title 3'

