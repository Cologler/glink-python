# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from re import T
from typing import *
import os
import sys
import traceback
from enum import IntEnum

from click import Context, confirm
from click_anno import click_app

from .core import SyncWays, add_link, sync_one, sync_all
from .utils import parse_gist_url

class SyncWays(IntEnum):
    pull = 1
    push = 2
    twoway = 3

    def __format__(self, format_spec: str) -> str:
        return self.name

@click_app
class App:
    def link(self, ctx: Context, url: str, file: str=None, *, way: SyncWays=SyncWays.twoway):
        'add doc'
        gist_info = parse_gist_url(url)
        if not gist_info:
            return ctx.fail(f'{url} is not a gist url.')

        link_id = add_link(ctx, gist_info, file, way)

        if confirm('Sync now?', default=True, show_default=True):
            sync_one(ctx, link_id)

    def unlink(self):
        pass

    def push(self, ctx: Context, file: str):
        'push doc'
        # TODO: push
        raise NotImplementedError
        url = ...

        # than add
        self.add(ctx, url, file, way=SyncWays.twoway)

    def sync(self, ctx: Context):
        'sync all added links.'
        sync_all(ctx)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        App()
    except Exception:
        traceback.print_exc()
