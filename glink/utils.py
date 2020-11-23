# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
import re
import hashlib

def parse_gist_url(url: str):
    match = re.match(r'^(?:https://gist.github.com/(?:(?P<user>[^/]+)/)?)?(?P<gist_id>[0-9a-f]+)(?:#(?P<file>.*))?$', url)
    if match:
        user = match.group('user')
        file = match.group('file')
        rv = dict(
            gist_id=match.group('gist_id'),
        )
        if user:
            rv['user'] = user
        if file:
            rv['file'] = file
        return rv

_GIST_URL_TRANSLATES = {
    ord('.'): '-'
}

def determine_gist_file(expect_name: str, remote_files: List[str]):
    if expect_name in remote_files:
        return expect_name
    if expect_name.startswith('file-'):
        # file-* like gist link
        remote_files_map = dict((x.translate(_GIST_URL_TRANSLATES), x) for x in remote_files)
        remote_file = remote_files_map.get(expect_name[5:])
        if remote_file:
            return remote_file

def sha1_bytes(buffer: bytes):
    return hashlib.sha1(buffer).hexdigest()
