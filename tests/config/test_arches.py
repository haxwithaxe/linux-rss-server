"""Tests verifying repo URL generation with various `arches`."""

from linux_rss_server.config import Repo, RepoType


def test_no_arches():
  repo = Repo('https://cd.example.com/{arch}', [], RepoType('debian'))
  assert list(repo) == ['https://cd.example.com/noarches']


def test_an_arch():
  repo = Repo('https://cd.example.com/{arch}', ['somearch'], RepoType('debian'))
  assert list(repo) == ['https://cd.example.com/somearch']


def test_duplicate_arches():
  repo = Repo('https://cd.example.com/{arch}', ['a', 'a'], RepoType('debian'))
  assert list(repo) == ['https://cd.example.com/a']
