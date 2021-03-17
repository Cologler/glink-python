# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
from functools import lru_cache
import re

import github
from github.GithubException import UnknownObjectException

from ..abc import IRemoteProvider, RemoteFileInfo
from ..errors import RemoteFileRemovedError, MissingDataError

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
    return expect_name

@lru_cache(maxsize=None)
def get_gist(gist_id: str, token: str=None):
    client = github.Github(token)
    try:
        return client.get_gist(gist_id)
    except UnknownObjectException:
        raise RemoteFileRemovedError(f'gist("{gist_id}") is removed')

class GistProvider(IRemoteProvider):
    name = 'gist'

    def parse_url(self, url: str) -> Optional[RemoteFileInfo]:
        gist_info = parse_gist_url(url)
        if not gist_info:
            return None

        gist_id: str = gist_info['gist_id']
        file: Optional[str] = gist_info.get('file')
        gist = get_gist(gist_id, None)

        # determine remote file
        remote_files: List[str] = list(gist.files)

        if file:
            remote_file = determine_gist_file(file, remote_files)
        else:
            if len(remote_files) == 1:
                remote_file = remote_files[0]
            else:
                self._logger.debug(f'must select a determinate file.')
                return

        return RemoteFileInfo(
            origin_url=url, prov=self.name,
            user=gist.owner.login,
            repo=gist_id,
            remote_file=remote_file
        )

    def get_remote_version(self, *, user: str, repo: str, remote_file: str,
                           access_token: str,
                           **kwargs) -> str:
        gist = get_gist(repo, access_token)
        return gist.history[0].version

    def get_remote_file_content(self, *, user: str, repo: str, remote_file: str, version: str,
                                access_token: str,
                                **kwargs) -> Optional[bytes]:
        gist = get_gist(repo, access_token)
        for revision in gist.history:
            if revision.version == version:
                remote_file_info = revision.files.get(remote_file)
                if remote_file_info:
                    return self._http_get(remote_file_info.raw_url).content
                break

    def push_local_file_content(self, *, user: str, repo: str, remote_file: str,
                                local_file_content: bytes,
                                access_token: str,
                                **kwargs) -> str:
        if not access_token:
            raise MissingDataError('access token is required')

        gist = get_gist(repo, access_token)
        files_content = {
            remote_file: github.InputFileContent(local_file_content.decode('utf-8'))
        }
        gist.edit(files=files_content)
        return gist.history[0].version

    def new_gist(self, *,
            user: str, filename: str, content: bytes, access_token: str,
            public: bool,
            **kwargs) -> str:
        if not access_token:
            raise MissingDataError('access token is required')

        files_content = {
            filename: github.InputFileContent(content.decode('utf-8'))
        }
        client = github.Github(access_token)
        gist = client.get_user().create_gist(public, files=files_content)
        return gist.id
