# Python script to query REST-API from empirica-systeme, see https://www.empirica-systeme.de/en/portfolio/empirica-systeme-rest-api/
# This work is licensed under a "Creative Commons Attribution 4.0 International License", sett http://creativecommons.org/licenses/by/4.0/
# Documentation of REST-API at https://api.empirica-systeme.de/api-docs/

import pytest
import configparser
from os.path import expanduser
from analystApi import api_basic


@pytest.fixture(scope='session')
def test_client():
    config = configparser.ConfigParser()
    home = expanduser("~")
    config.read_file(open(home + '/analystApi.login'))

    api_basic.username = config.get('global', 'username')
    api_basic.password = config.get('global', 'password')
    api_basic.endpoint = config.get('global', 'endpoint')
    yield 1
