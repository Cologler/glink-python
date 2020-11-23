# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from os import remove
from re import T
from threading import local
from typing import *
import os
import sys
import traceback
import logging

from click import Context
import click
from click_anno import click_app
from click_anno.types import flag
import click_log

from .errors import GLinkError, ConflictError
from .core import SyncWays, add_link, sync_one, get_all_link_ids, list_, ConflictPolicies, remove_link
from .utils import parse_gist_url

class _CliLoggerHandler(click_log.ClickHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno == logging.ERROR:
            click.get_current_context().abort()

@click_app
class App:
    def __init__(self, debug: flag=False) -> None:
        # setup logger
        logger = logging.getLogger('glink')
        handler = _CliLoggerHandler()
        handler.formatter = click_log.ColorFormatter()
        logger.handlers = [handler]
        if debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        self._logger = logger

    def list_(self):
        '''
        list all links.
        '''
        list_()

    def link(self, ctx: Context, url: str, file: str=None, *, way: SyncWays=SyncWays.twoway):
        'add doc'
        gist_info = parse_gist_url(url)
        if not gist_info:
            return ctx.fail(f'{url} is not a gist url.')

        try:
            link_id = add_link(gist_info, file, way)
            if click.confirm('sync now?', default=True, show_default=True):
                sync_one(link_id)
        except GLinkError as ge:
            ctx.fail(ge.message)

    def unlink(self, link_id: str):
        try:
            remove_link(link_id)
        except KeyError:
            self._logger.error(f'no such link: {link_id}')

    def push(self, ctx: Context, file: str):
        'push doc'
        # TODO: push
        raise NotImplementedError
        url = ...

        # than add
        self.link(ctx, url, file, way=SyncWays.twoway)

    def sync(self, link_id: str):
        try:
            sync_one(link_id)
        except ConflictError as e:
            self._logger.warning(e)
        else:
            return

        options = {
            str(ConflictPolicies.local): ConflictPolicies.local,
            str(ConflictPolicies.remote): ConflictPolicies.remote,
            str(ConflictPolicies.skip): ConflictPolicies.skip,
            'unlink': 'unlink'
        }

        choice = click.Choice(options)
        policy = click.prompt('decide to?', type=choice, show_choices=True)

        if policy == 'unlink':
            remove_link(link_id)
        elif policy == str(ConflictPolicies.skip):
            pass
        else:
            sync_one(link_id, options[policy])

    def sync_all(self):
        'sync all added links.'
        for link_id in get_all_link_ids():
            self.sync(link_id)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        App()
    except Exception:
        traceback.print_exc()
