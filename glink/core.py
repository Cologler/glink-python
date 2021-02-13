# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
from enum import IntEnum, auto
import os
import pathlib
import logging

from typeguard import typechecked

from .errors import LocalFileRemovedError, ConflictError, RemoteFileRemovedError
from .abc import IRemoteProvider
from .configs import GLinkConfigs
from .provs.gist import GistProvider
from .utils import sha1_bytes


class SyncWays(IntEnum):
    pull = 1
    push = 2
    twoway = 3

    def __str__(self) -> str:
        return self.name

    def __format__(self, format_spec: str) -> str:
        return self.name

    def to_symbol(self) -> str:
        if self == SyncWays.twoway:
            return '<->'
        elif self == SyncWays.pull:
            return ' ->'
        else:
            return '<- '


class ConflictPolicies(IntEnum):
    unset = auto()
    local = auto()
    remote = auto()
    skip = auto()

    def __str__(self) -> str:
        return self.name

    def __format__(self, format_spec: str) -> str:
        return self.name

def _get_providers() -> Dict[str, IRemoteProvider]:
    return dict((x.name, x) for x in [GistProvider()])

class GLinkApi:
    def __init__(self, conf_root: str=None) -> None:
        self._configs = GLinkConfigs(
            pathlib.Path(conf_root) if conf_root else None
        )
        self._logger = logging.getLogger('glink')

    def get_links(self):
        return dict(
            (link_id, self._configs.get_link(link_id=link_id)) for link_id in self._configs.get_all_link_ids()
        )

    def get_all_link_ids(self):
        return self._configs.get_all_link_ids()

    def remove_link(self, link_id: str):
        self._configs.remove_link(link_id=link_id)

    def add_link(self, url: str, local_file: Optional[str], way: SyncWays):
        parsed = [(p, p.parse_url(url)) for p in _get_providers().values()]
        parsed = [(p, r) for p, r in parsed if r]

        if not parsed:
            self._logger.error(f'url "{url}" does not match any pattern.')
            return

        if len(parsed) > 1:
            self._logger.warning(f'url "{url}" matched multi patterns:')
            for _, r in parsed:
                self._logger.info(f'  - {r.s()}')
            return

        prov, rfi = parsed[0]

        remote_file = rfi.remote_file
        assert remote_file

        if not local_file:
            local_file = os.path.basename(remote_file)
        local_file = os.path.abspath(local_file)

        link_id: str = self._configs.add_link(
            prov=prov.name,
            user=rfi.user,
            repo=rfi.repo,
            remote_file=remote_file,
            local_file=local_file,
            way=way.value
        )

        self._logger.info(f'link added: {rfi.s()} {way.to_symbol()} {local_file}')
        return link_id

    def push_new_gist(self, local_file: str, user: Optional[str], public: bool):
        prov = 'gist'

        auth_info = self._configs.read_auth_info(prov, user, allow_default=True)
        if isinstance(auth_info, str):
            access_token = auth_info
        else:
            access_token = None

        provider = GistProvider()
        remote_file = os.path.basename(local_file)
        repo = provider.new_gist(
            user=user,
            filename=remote_file,
            content=pathlib.Path(local_file).read_bytes(),
            access_token=access_token,
            public=public
        )

        link_id: str = self._configs.add_link(
            prov=prov,
            user=user,
            repo=repo,
            remote_file=remote_file,
            local_file=os.path.abspath(local_file),
            way=SyncWays.twoway.value
        )

        self._logger.info(f'link added: gist/{repo}/{remote_file} {SyncWays.twoway.to_symbol()} {local_file}')
        return link_id

    @typechecked
    def _sync_one_core(self,
            prov: str, user: str, repo: str, remote_file: str, local_file: str, way: int, sync_state: dict,
            conflict_policy: ConflictPolicies
        ):
        assert way in SyncWays.__members__.values()

        provider: IRemoteProvider
        if prov == 'gist':
            provider = GistProvider()
        else:
            raise NotImplementedError
        remote_name = f'{prov}("{repo}")'
        local_name = f'local("{local_file}")'

        kwargs = dict(prov=prov, user=user, repo=repo, remote_file=remote_file)
        auth_info = self._configs.read_auth_info(prov, user)
        if isinstance(auth_info, str):
            kwargs['access_token'] = auth_info
        kwargs.setdefault('access_token', None)

        remote_version = provider.get_remote_version(**kwargs)
        self._logger.debug(f'current remote version is: {remote_version}.')
        if remote_version != sync_state.get('remote_version'):
            remote_file_content = provider.get_remote_file_content(**kwargs, version=remote_version)
            if remote_file_content is None:
                self._logger.info(f'remote file "{remote_file}" is removed, sync is skiped.')
                return
            remote_file_sha1 = sha1_bytes(remote_file_content)
            remote_file_changed = remote_file_sha1 != sync_state.get('file_sha1')
        else:
            remote_file_sha1 = None
            remote_file_content = None
            remote_file_changed = False

        local_file_pathobj = pathlib.Path(local_file)
        if os.path.isfile(local_file):
            local_file_content = local_file_pathobj.read_bytes()
            local_file_sha1 = sha1_bytes(local_file_content)
            local_file_changed = local_file_sha1 != sync_state.get('file_sha1')
        elif sync_state:
            raise LocalFileRemovedError(f'local("{local_file}") is removed')
        else:
            local_file_content = None
            local_file_sha1 = None
            local_file_changed = False

        file_sha1 = None
        pull, push = False, False
        if remote_file_changed and local_file_changed:
            self._logger.debug(f'both versions is changed.')
            if remote_file_sha1 == local_file_sha1:
                self._logger.info(f'reattach local file "{local_file}" as unchanged.')
                file_sha1 = remote_file_sha1
            else:
                if conflict_policy == ConflictPolicies.unset:
                    raise ConflictError(f'{local_name} and {remote_name} both changed.')
                elif conflict_policy == ConflictPolicies.local:
                    if way == SyncWays.pull:
                        self._logger.warning('ignore by pull only.')
                        return
                    push = True
                else:
                    if way == SyncWays.push:
                        self._logger.warning('ignore by push only.')
                        return
                    pull = True
        elif remote_file_changed:
            self._logger.debug(f'remote version is changed.')
            if way == SyncWays.push:
                self._logger.debug('ignore by push only.')
                return
            pull = True

        elif local_file_changed:
            self._logger.debug(f'local version is changed.')
            if way == SyncWays.pull:
                self._logger.debug('ignore by pull only.')
                return
            push = True

        else:
            self._logger.debug(f'both versions is not changed.')
            return

        assert not (pull and push)
        if pull:
            local_file_pathobj.write_bytes(remote_file_content)
            file_sha1 = remote_file_sha1
            self._logger.info(f'pull {remote_name} to {local_name}.')
        elif push:
            remote_version = provider.push_local_file_content(local_file_content=local_file_content, **kwargs)
            file_sha1 = local_file_sha1
            self._logger.info(f'push {local_name} to {remote_name}.')

        assert remote_version
        assert file_sha1
        sync_state.update(
            remote_version=remote_version,
            file_sha1=file_sha1
        )
        return True

    def sync_one(self, link_id: str, conflict_policy: ConflictPolicies=ConflictPolicies.unset):
        link_data: dict = self._configs.get_link(link_id=link_id)
        if not link_data:
            self._logger.warning(f'no such link: {link_id}')
            return
        sync_state = link_data.setdefault('sync_state', {})
        synced = False
        try:
            synced = self._sync_one_core(conflict_policy=conflict_policy, **link_data)
        except (LocalFileRemovedError, RemoteFileRemovedError) as e:
            self._logger.warning(f'skiped link("{link_id}") because {e.message}.')
        if synced:
            self._configs.save_state(link_id=link_id, sync_state=sync_state)
