# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from sys import implementation
from typing import *
from functools import cache

import click
import github
from github.GithubException import UnknownObjectException

from ..abc import IRemoteProvider
from ..errors import RemoteFileRemovedError

@cache
def get_gist(gist_id: str, token: str=None):
    client = github.Github(token)
    try:
        return client.get_gist(gist_id)
    except UnknownObjectException:
        raise RemoteFileRemovedError(f'gist("{gist_id}") is removed')

class GistProvider(IRemoteProvider):
    name = 'gist'

    def get_remote_version(self, *, user: str, repo: str, remote_file: str,
                           access_token: str,
                           **kwargs) -> str:
        gist = get_gist(repo, access_token)
        return gist.history[0].version

    def get_remote_file_content(self, *, user: str, repo: str, remote_file: str,
                                access_token: str,
                                **kwargs) -> Optional[bytes]:
        gist = get_gist(repo, access_token)
        gist.files.get(remote_file)
        remote_file_info = gist.files.get(remote_file)
        if remote_file_info:
            return self._http_get(remote_file_info.raw_url).content

    def push_local_file_content(self, *, user: str, repo: str, remote_file: str,
                                local_file_content: bytes,
                                access_token: str,
                                **kwargs) -> str:
        if not access_token:
            click.get_current_context().fail('access token is required')
            return

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
            click.get_current_context().fail('access token is required')
            return

        files_content = {
            filename: github.InputFileContent(content.decode('utf-8'))
        }
        client = github.Github(access_token)
        gist = client.get_user().create_gist(public, files=files_content)
        return gist.id
