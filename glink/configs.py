# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

import json
from functools import partial
import uuid

import xdg
import sqlitedict
from typeguard import typechecked

class GLinkConfigs:
    def __init__(self) -> None:
        self._conf_root = xdg.XDG_CONFIG_HOME / 'Cologler' / 'glink'
        self._conf_root.mkdir(parents=True, exist_ok=True)

    def _get_linkdb(self, autocommit=False):
        return sqlitedict.SqliteDict(
            filename=str(self._conf_root / 'glink.db'),
            tablename='links',
            journal_mode='WAL',
            autocommit=autocommit,
            encode=partial(json.dumps, ensure_ascii=False),
            decode=json.loads
        )

    @typechecked
    def add_link(self, prov: str, user: str, repo: str, remote_file: str, local_file: str, way: int):
        id = str(uuid.uuid4())
        with self._get_linkdb(True) as linkdb:
            linkdb[id] = dict(
                prov=prov,
                user=user,
                repo=repo,
                remote_file=remote_file,
                local_file=local_file,
                way=way
            )
        return id

    @typechecked
    def get_link(self, link_id: str):
        with self._get_linkdb() as linkdb:
            return linkdb.get(link_id)

    @typechecked
    def save_state(self, link_id: str, sync_state: dict):
        with self._get_linkdb(True) as linkdb:
            data = linkdb[link_id]
            data['sync_state'] = sync_state
            linkdb[link_id] = data

    def get_all_linkids(self):
        with self._get_linkdb() as linkdb:
            return list(linkdb)
