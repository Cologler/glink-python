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

import requests
from click import style
from typeguard import typechecked
import github

from .errors import GLinkError, LocalFileRemovedError, ConflictError, RemoteFileRemovedError
from .abc import IRemoteProvider
from .configs import GLinkConfigs
from .provs.gist import GistProvider
from .utils import determine_gist_file, sha1_bytes


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


_CONFIGS = GLinkConfigs()

def add_link(gist_info: dict, local_file: Optional[str], way: SyncWays):
    gist_id: str = gist_info['gist_id']
    file: Optional[str] = gist_info.get('file')

    gist_url = f'https://api.github.com/gists/{gist_id}'
    r = requests.get(gist_url, timeout=10)
    gist_data = r.json()

    # determine remote file
    remote_files: List[str] = list(gist_data['files'])

    if file:
        remote_file = determine_gist_file(file, remote_files)
        if not remote_file:
            raise GLinkError(f'no file named "{file}" in gist {gist_id}.')
    else:
        if len(remote_files) == 1:
            remote_file = remote_files[0]
        else:
            raise GLinkError(f'must select a determinate file.')

    if not local_file:
        local_file = os.path.basename(remote_file)
    local_file = os.path.abspath(local_file)

    link_id: str = _CONFIGS.add_link(
        prov='gist',
        user=gist_data['owner']['login'],
        repo=gist_id,
        remote_file=remote_file,
        local_file=local_file,
        way=way.value
    )

    glink_logger.info(f'link added: gist/{gist_id}/{remote_file} {way.to_symbol()} {local_file}')
    return link_id

def push_new_gist(local_file: str, user: Optional[str], public: bool):
    prov = 'gist'

    if user is None:
        users = _CONFIGS.get_users(prov)
        if len(users) == 0:
            glink_logger.error('no gist user in configs.')
        elif len(users) > 1:
            glink_logger.error('you must type a user.')
        else:
            user = users[0]

    auth_info = _CONFIGS.read_auth_info(prov, user)
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

    link_id: str = _CONFIGS.add_link(
        prov=prov,
        user=user,
        repo=repo,
        remote_file=remote_file,
        local_file=os.path.abspath(local_file),
        way=SyncWays.twoway.value
    )

    glink_logger.info(f'link added: gist/{repo}/{remote_file} {SyncWays.twoway.to_symbol()} {local_file}')
    return link_id

@typechecked
def _sync_one_core(
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
    auth_info = _CONFIGS.read_auth_info(prov, user)
    if isinstance(auth_info, str):
        kwargs['access_token'] = auth_info

    remote_version = provider.get_remote_version(**kwargs)
    if remote_version != sync_state.get('remote_version'):
        glink_logger.debug(f'found new remote version: {remote_version}.')
        remote_file_content = provider.get_remote_file_content(**kwargs)
        if remote_file_content is None:
            glink_logger.info(f'remote file "{remote_file}" is removed, sync is skiped.')
            return
        remote_file_sha1 = sha1_bytes(remote_file_content)
        remote_file_changed = remote_file_sha1 != sync_state.get('file_sha1')
    else:
        glink_logger.debug(f'remote version is not changed: {remote_version}.')
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
        if remote_file_sha1 == local_file_sha1:
            glink_logger.info(f'reattach local file "{local_file}" as unchanged.')
            file_sha1 = remote_file_sha1
        else:
            if conflict_policy == ConflictPolicies.unset:
                raise ConflictError(f'{local_name} and {remote_name} both changed.')
            elif conflict_policy == ConflictPolicies.local:
                if way == SyncWays.pull:
                    glink_logger.warning('ignore by pull only.')
                    return
                push = True
            else:
                if way == SyncWays.push:
                    glink_logger.warning('ignore by push only.')
                    return
                pull = True
    elif remote_file_changed:
        if way == SyncWays.push:
            glink_logger.debug('ignore by push only.')
            return
        pull = True
    elif local_file_changed:
        if way == SyncWays.pull:
            glink_logger.debug('ignore by pull only.')
            return
        push = True

    assert not (pull and push)
    if pull:
        local_file_pathobj.write_bytes(remote_file_content)
        file_sha1 = remote_file_sha1
        glink_logger.info(f'pull {remote_name} to {local_name}.')
    elif push:
        remote_version = provider.push_local_file_content(local_file_content=local_file_content, **kwargs)
        file_sha1 = local_file_sha1
        glink_logger.info(f'push {local_name} to {remote_name}.')

    assert remote_version
    assert file_sha1
    sync_state.update(
        remote_version=remote_version,
        file_sha1=file_sha1
    )
    return True

def sync_one(link_id: str, conflict_policy: ConflictPolicies=ConflictPolicies.unset):
    link_data: dict = _CONFIGS.get_link(link_id=link_id)
    sync_state = link_data.setdefault('sync_state', {})
    synced = False
    try:
        synced = _sync_one_core(conflict_policy=conflict_policy, **link_data)
    except (LocalFileRemovedError, RemoteFileRemovedError) as e:
        glink_logger.warning(f'skiped link("{link_id}") because {e.message}.')
    if synced:
        _CONFIGS.save_state(link_id=link_id, sync_state=sync_state)

def get_all_link_ids():
    return _CONFIGS.get_all_link_ids()

def list_():
    return dict(
        (link_id, _CONFIGS.get_link(link_id=link_id)) for link_id in _CONFIGS.get_all_link_ids()
    )

def remove_link(link_id: str):
    _CONFIGS.remove_link(link_id=link_id)


glink_logger = logging.getLogger('glink')
