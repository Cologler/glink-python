# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from glink.utils import parse_gist_url, determine_gist_file

def test_parse_gist_url_fullurl():
    assert parse_gist_url('https://gist.github.com/Cologler/17a6dfcb530d53d0b155706b8d657772#file-python-travis-yml') == dict(
        user='Cologler',
        gist_id='17a6dfcb530d53d0b155706b8d657772',
        file='file-python-travis-yml'
    )

def test_parse_gist_url_fullurl_without_file():
    assert parse_gist_url('https://gist.github.com/Cologler/17a6dfcb530d53d0b155706b8d657772#') == dict(
        user='Cologler',
        gist_id='17a6dfcb530d53d0b155706b8d657772'
    )
    assert parse_gist_url('https://gist.github.com/Cologler/17a6dfcb530d53d0b155706b8d657772') == dict(
        user='Cologler',
        gist_id='17a6dfcb530d53d0b155706b8d657772'
    )

def test_parse_gist_url_without_user():
    assert parse_gist_url('https://gist.github.com/17a6dfcb530d53d0b155706b8d657772#file-python-travis-yml') == dict(
        gist_id='17a6dfcb530d53d0b155706b8d657772',
        file='file-python-travis-yml'
    )

def test_parse_gist_url_without_user_and_file():
    assert parse_gist_url('https://gist.github.com/17a6dfcb530d53d0b155706b8d657772#') == dict(
        gist_id='17a6dfcb530d53d0b155706b8d657772'
    )
    assert parse_gist_url('https://gist.github.com/17a6dfcb530d53d0b155706b8d657772') == dict(
        gist_id='17a6dfcb530d53d0b155706b8d657772'
    )

def test_parse_gist_url_only_gist_id():
    assert parse_gist_url('17a6dfcb530d53d0b155706b8d657772#file-python-travis-yml') == dict(
        gist_id='17a6dfcb530d53d0b155706b8d657772',
        file='file-python-travis-yml'
    )

def test_parse_gist_url_only_gist_id_without_file():
    assert parse_gist_url('17a6dfcb530d53d0b155706b8d657772#') == dict(
        gist_id='17a6dfcb530d53d0b155706b8d657772'
    )
    assert parse_gist_url('17a6dfcb530d53d0b155706b8d657772') == dict(
        gist_id='17a6dfcb530d53d0b155706b8d657772'
    )

def test_guess_gist_file():
    assert determine_gist_file('file-python-travis-yml', {'python.travis.yml'}) == 'python.travis.yml'
