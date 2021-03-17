# -*- coding: utf-8 -*-
#
# Copyright (c) 2020~2999 - Cologler <skyoflw@gmail.com>
# ----------
#
# ----------

from glink.abc import RemoteFileInfo
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
    GLinkApi, SyncWays, ConflictPolicies
)

class _CliLoggerHandler(click_log.ClickHandler):
    def emit(self, record):
        super().emit(record)
        if record.levelno == logging.ERROR:
            click.get_current_context().abort()

@click_app
class App:
    def __init__(self, debug: flag=False, conf_root: str=None) -> None:
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
        self._api = GLinkApi(conf_root)

    def list_(self):
        '''
        list all links.
        '''

        items = self._api.get_links().items()
        if items:
            for link_id, link_data in items:
                self._logger.info('{link_id}: {remote_name} {way} {local_name}'.format(
                    link_id=click.style(link_id, fg='blue'),
                    remote_name='{prov}("{repo}#{remote_file}")'.format(
                        prov=link_data['prov'],
                        repo=click.style(link_data['repo'], fg='green'),
                        remote_file=click.style(link_data['remote_file'], fg='green'),
                    ),
                    way=SyncWays(link_data['way']).to_symbol(),
                    local_name='local("{local_file}")'.format(
                        local_file=click.style(link_data['local_file'], fg='green')
                    ),
                ))
        else:
            self._logger.info('~ here is empty ~')

    def link(self, ctx: Context, url: str, file: str=None, *, way: SyncWays=SyncWays.twoway):
        'link a remote file to local.'
        try:
            link_id = self._api.add_link(url, file, way)
            self._logger.info('link id: {}'.format(style(link_id, fg='green')))
            if click.confirm('sync now?', default=True, show_default=True):
                self._api.sync_one(link_id)
        except GLinkError as ge:
            ctx.fail(ge.message)

    def unlink(self, ctx: Context, link_id: str):
        '''
        remove a link.
        '''
        try:
            self._api.remove_link(link_id)
        except KeyError:
            self._logger.error(f'no such link: {link_id}.')
        except GLinkError as ge:
            ctx.fail(ge.message)
        else:
            self._logger.info(f'unlinked: {link_id}.')

    def push(self, ctx: Context, file: str, user: str=None, public: flag=False):
        'push the file as a new gist.'
        if not os.path.isfile(file):
            self._logger.error(f'{file} is not a file.')
        try:
            link_id = self._api.push_new_gist(file, user=user, public=public)
        except GLinkError as ge:
            ctx.fail(ge.message)
        else:
            self._logger.info('link id: {}'.format(style(link_id, fg='green')))

    def sync(self, link_id: str):
        'sync one link.'

        try:
            self._api.sync_one(link_id)
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
            self._api.remove_link(link_id)
        elif policy == str(ConflictPolicies.skip):
            pass
        else:
            self._api.sync_one(link_id, options[policy])

    def sync_all(self):
        'sync all links.'

        for link_id in self._api.get_all_link_ids():
            self.sync(link_id)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        App()
    except Exception:
        traceback.print_exc()
