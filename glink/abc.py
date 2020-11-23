# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
from abc import ABC, abstractmethod
from functools import cache

import requests

class IRemoteProvider(ABC):
    name: str

    @abstractmethod
    def get_remote_version(self, *, user: str, repo: str, remote_file: str,
                           access_token: Optional[str],
                           **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_remote_file_content(self, *, user: str, repo: str, remote_file: str,
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
    @cache
    def _http_get(url: str) -> dict:
        return requests.get(url, timeout=10)
