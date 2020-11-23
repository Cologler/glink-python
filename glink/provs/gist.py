# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
from functools import cache
import click

import requests
import github

from ..abc import IRemoteProvider

@cache
def get_gist(gist_id: str, token: str=None):
    client = github.Github(token)
    return client.get_gist(gist_id)

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
