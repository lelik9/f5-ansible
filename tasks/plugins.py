#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import glob

from .lib.common import BASE_DIR
from .lib.common import cmp_dir

from invoke.exceptions import Exit
from invoke import task


HELP1 = dict(
    collection="The collection name to which the plugins are upstreamed, default: 'f5_modules'."
)


def purge_upstreamed_files(c, target_dir, collection):
    if not os.path.exists(collection):
        return
    if not os.path.exists(target_dir):
        return
    if len(os.listdir(target_dir)) > 0:
        print("Purging contents from {0}.".format(target_dir))
        with c.cd(target_dir):
            c.run('rm -f *')


def files_upstream(c, plugin_dir, target_dir):
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    cmd = [
        'cp', '{0}/*.py'.format(plugin_dir),
        target_dir
    ]
    c.run(' '.join(cmd))


def upstream_plugin(c, plugin, collection='f5_modules'):
    plugin_dir = '{0}/library/plugins/{1}/'.format(BASE_DIR, plugin)
    target_dir = '{0}/local/ansible_collections/f5networks/{1}/plugins/{2}/'.format(BASE_DIR, collection, plugin)
    coll_dest = '{0}/local/ansible_collections/f5networks/{1}'.format(BASE_DIR, collection)
    if not os.path.exists(plugin_dir):
        print("No plugin type {0} directory found ...skipping.".format(plugin))
        return
    if len(list(glob.glob('{0}/*.py'.format(plugin_dir)))) == 0:
        print("No plugin type {0} files found ...skipping.".format(plugin))
        return

    purge_upstreamed_files(c, target_dir, coll_dest)
    files_upstream(c, plugin_dir, target_dir)

    retries = 0
    while not cmp_dir(plugin_dir, target_dir):
        purge_upstreamed_files(c, target_dir, coll_dest)
        files_upstream(c, plugin_dir, target_dir)
        retries = retries + 1

    if retries > 2:
        raise Exit('Failed to upstream plugin type: {0}, exiting.'.format(plugin))

    print("Copy of plugin type {0} complete!".format(plugin))


@task(optional=['collection'], help=HELP1)
def upstream(c, collection='f5_modules'):
    """Copy all plugins, to the local/ansible_collections/f5networks/collection_name directory.
    """
    coll_dest = '{0}/local/ansible_collections/f5networks/{1}/'.format(BASE_DIR, collection)
    if not os.path.exists(coll_dest):
        print("The required collection directory does not exist, creating...")
        c.run('mkdir -p {0}'.format(coll_dest))
        print("Collection directory created.")

    upstream_plugin(c, 'action')
    upstream_plugin(c, 'connection')
    upstream_plugin(c, 'filter')
    upstream_plugin(c, 'httpapi')
    upstream_plugin(c, 'lookup')
    upstream_plugin(c, 'terminal')

    print("Plugins copy complete.")
