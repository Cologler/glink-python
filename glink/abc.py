# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
from abc import ABC, abstractmethod
from functools import lru_cache
from dataclasses import dataclass
from logging import getLogger

import requests

@dataclass
class RemoteFileInfo:
    origin_url: str
    prov: str
    user: Optional[str]
    repo: Optional[str]
    remote_file: str

    def __str__(self) -> str:
        return self.s(False)

    def s(self, styled=True) -> str:
        prov = self.prov
        repo = self.repo + '#' if self.repo else ''
        remote_file = self.remote_file
        if styled:
            import click
            repo = click.style(repo, fg='green')
            remote_file = click.style(remote_file, fg='green')
        return '{prov}("{repo}{remote_file}")'.format_map(vars())


class IRemoteProvider(ABC):
    name: str

    def __init__(self):
        self._logger = getLogger('glink.' + self.name)

    @abstractmethod
    def parse_url(self, url: str) -> Optional[RemoteFileInfo]:
        'try parse the url'
        raise NotImplementedError

    @abstractmethod
    def get_remote_version(self, *, user: str, repo: str, remote_file: str,
                           access_token: Optional[str],
                           **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_remote_file_content(self, *, user: str, repo: str, remote_file: str, version: str,
                                access_token: Optional[str],
                                **kwargs) -> Optional[bytes]:
        '''
        get file content as bytes.
        return `None` if the file was removed.
        '''
        raise NotImplementedError

    @abstractmethod
    def push_local_file_content(self, *, user: str, repo: str, remote_file: str,
                                access_token: Optional[str],
                                local_file_content: bytes,
                                **kwargs) -> str:
        '''
        return the new version string.
        '''
        raise NotImplementedError

    @staticmethod
    @lru_cache(maxsize=None)
    def _http_get(url: str) -> dict:
        return requests.get(url, timeout=10)
