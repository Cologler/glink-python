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
from click.termui import style
from click_anno import click_app
from click_anno.types import flag
import click_log

from .errors import GLinkError, ConflictError
from .core import (
    SyncWays, ConflictPolicies,
    add_link, sync_one, get_all_link_ids, list_, remove_link, push_new_gist
)
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

        for link_id, link_data in list_().items():
            self._logger.info('{link_id}: {remote_name} {way} {local_name}'.format(
                link_id=click.style(link_id, fg='blue'),
                remote_name='{prov}("{repo}")'.format(
                    prov=link_data['prov'],
                    repo=click.style(link_data['repo'], fg='green')
                ),
                way=SyncWays(link_data['way']).to_symbol(),
                local_name='local("{local_file}")'.format(
                    local_file=click.style(link_data['local_file'], fg='green')
                ),
            ))

    def link(self, ctx: Context, url: str, file: str=None, *, way: SyncWays=SyncWays.twoway):
        'add doc'
        gist_info = parse_gist_url(url)
        if not gist_info:
            return ctx.fail(f'{url} is not a gist url.')

        try:
            link_id = add_link(gist_info, file, way)
            self._logger.info('link id: {}'.format(style(link_id, fg='green')))
            if click.confirm('sync now?', default=True, show_default=True):
                sync_one(link_id)
        except GLinkError as ge:
            ctx.fail(ge.message)

    def unlink(self, link_id: str):
        '''
        remove a link.
        '''
        try:
            remove_link(link_id)
        except KeyError:
            self._logger.error(f'no such link: {link_id}.')
        else:
            self._logger.info(f'unlinked: {link_id}.')

    def push(self, ctx: Context, file: str, user: str=None, public: flag=False):
        'push a file to a new gist'
        if not os.path.isfile(file):
            self._logger.error(f'{file} is not a file.')
        link_id = push_new_gist(file, user=user, public=public)
        self._logger.info('link id: {}'.format(style(link_id, fg='green')))

    def sync(self, link_id: str):
        'sync one link.'

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
        'sync all links.'

        for link_id in get_all_link_ids():
            self.sync(link_id)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        App()
    except Exception:
        traceback.print_exc()
