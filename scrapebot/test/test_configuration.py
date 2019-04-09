import pytest
from scrapebot.configuration import Configuration
import re
import os


@pytest.fixture
def new_configuration(pytestconfig):
    return make_configuration(pytestconfig.rootdir)


def make_configuration(root_dir):
    config = Configuration()
    config.add_value('Instance', 'browser', 'Firefox')
    config.add_value('Instance', 'LibDirPrefix', os.path.join(root_dir, ''))
    config.add_value('Instance', 'BrowserBinary', '')
    return config


class TestConfiguration(object):
    def test_db_engine_string(self, new_configuration):
        pattern = re.compile('^[a-z+]+://[a-zA-Z0-9-_]{1,32}:.+@[a-zA-Z0-9-_+~.]+/[a-zA-Z0-9-_]+$')
        assert pattern.match(new_configuration.get_db_engine_string())

    def test_get(self, new_configuration):
        assert new_configuration.get('foo', 'bar') is None

    def test_add_value(self, new_configuration):
        new_configuration.add_value('foo', 'bar', 42)
        assert int(new_configuration.get('foo', 'bar')) == 42

    def test_get_fallback(self, new_configuration):
        assert new_configuration.get('foo', 'bar', 42) == 42
