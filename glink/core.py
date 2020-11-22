# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from typing import *
from enum import IntEnum
import os
import pathlib

from click import Context, echo, style
import requests
from typeguard import typechecked
import github

from .configs import GLinkConfigs
from .utils import determine_gist_file, sha1_bytes

class SyncWays(IntEnum):
    pull = 1
    push = 2
    twoway = 3

    def __format__(self, format_spec: str) -> str:
        return self.name

_CONFIGS = GLinkConfigs()

def add_link(ctx: Context, gist_info: dict, local_file: Optional[str], way: SyncWays):
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
            return ctx.fail(f'no file named "{file}" in gist {gist_id}.')
    else:
        if len(remote_files) == 1:
            remote_file = remote_files[0]
        else:
            return ctx.fail(f'must select a determinate file.')

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

    if way == SyncWays.twoway:
        direction = '<->'
    elif way == SyncWays.pull:
        direction = ' ->'
    else:
        direction = '<- '
    echo(f'Link added: gist/{gist_id}/{gist_id} {direction} {local_file}')

    return link_id

@typechecked
def _sync_core(ctx: Context, prov: str, user: str, repo: str, remote_file: str, local_file: str, way: int, sync_state: dict):
    assert prov == 'gist'
    assert way in SyncWays.__members__.values()

    gist_url = f'https://api.github.com/gists/{repo}'
    r = requests.get(gist_url, timeout=10)
    gist_data = r.json()
    remote_file_info = gist_data['files'].get(remote_file)
    if not remote_file_info:
        echo(f'Remote file "{remote_file}" is removed, sync is skiped.')
        return
    remote_version = gist_data['history'][0]['version']
    if remote_version != sync_state.get('remote_version'):
        remote_file_content = requests.get(remote_file_info['raw_url'], timeout=10).content
        remote_file_sha1 = sha1_bytes(remote_file_content)
        remote_file_changed = remote_file_sha1 != sync_state.get('file_sha1')
        if sync_state:
            if not os.path.isfile(local_file):
                echo('Local file "{local_file}" is removed, sync is skiped.')
                return
            raise NotImplementedError
        else: # first sync to pull
            pass
            if os.path.isfile(local_file):
                pass
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
        echo(f'Local file "{local_file}" is removed, sync is skiped.')
        return
    else:
        local_file_content = None
        local_file_sha1 = None
        local_file_changed = False

    if remote_file_changed and local_file_changed:
        if remote_file_sha1 == local_file_sha1:
            echo(f'Reattach Local file "{local_file}" as unchanged.')
            file_sha1 = remote_file_sha1
        else:
            raise NotImplementedError
    elif remote_file_changed:
        if way == SyncWays.push:
            return
        local_file_pathobj.write_bytes(remote_file_content)
        file_sha1 = remote_file_sha1
        echo(f'Update "{local_file}" from remote.')
    elif local_file_changed:
        if way == SyncWays.pull:
            return
        raise NotImplementedError
    else:
        file_sha1 = sync_state.get('file_sha1')

    assert remote_version
    sync_state.update(
        remote_version=remote_version,
        file_sha1=file_sha1
    )
    return True

def sync_one(ctx: Context, link_id: str):
    link_data: dict = _CONFIGS.get_link(link_id=link_id)
    sync_state = link_data.setdefault('sync_state', {})
    if _sync_core(ctx, **link_data):
        _CONFIGS.save_state(link_id=link_id, sync_state=sync_state)

def sync_all(ctx: Context):
    for link_id in _CONFIGS.get_all_linkids():
        sync_one(ctx, link_id)
