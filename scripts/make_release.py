#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    make-release
    ~~~~~~~~~~~~

    Helper script that performs a release.  Does pretty much everything
    automatically for us.

    Originally taken from pallets/flask here:
    https://github.com/pallets/flask/blob/master/scripts/make-release.py

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import print_function

import argparse
import sys
import os
import re

from datetime import datetime, date
from subprocess import Popen, PIPE

_date_clean_re = re.compile(r'(\d+)(st|nd|rd|th)')


def parse_changelog():
    with open('CHANGES') as f:
        lineiter = iter(f)
        for line in lineiter:
            match = re.search('^Version\s+(.*)', line.strip())
            if match is None:
                continue
            version = match.group(1).strip()
            if lineiter.next().count('-') != len(match.group(0)):
                continue
            while 1:
                change_info = lineiter.next().strip()
                if change_info:
                    break

            match = re.search(r'released on (\w+\s+\d+\w+\s+\d+)'
                              r'(?:, codename (.*))?(?i)', change_info)
            if match is None:
                continue

            datestr, codename = match.groups()
            return version, parse_date(datestr), codename


def parse_date(string):
    string = _date_clean_re.sub(r'\1', string)
    return datetime.strptime(string, '%B %d %Y')


def set_filename_version(filename, version_number, pattern):
    changed = []

    def inject_version(match):
        before, old, after = match.groups()
        changed.append(True)
        return before + version_number + after
    with open(filename) as f:
        contents = re.sub(r"^(\s*%s\s*=\s*')(.+?)(')(?sm)" % pattern,
                          inject_version, f.read())

    if not changed:
        fail('Could not find %s in %s', pattern, filename)

    with open(filename, 'w') as f:
        f.write(contents)


def set_init_version(version):
    info('Setting __init__.py version to %s', version)
    set_filename_version('fleaker/__init__.py', version, '__version__')


def build_and_upload(pypi_alias):
    Popen([sys.executable, 'setup.py', 'release', 'sdist', 'bdist_wheel',
           'upload', '-r', pypi_alias]).wait()


def fail(message, *args):
    print('Error:', message % args, file=sys.stderr)
    sys.exit(1)


def info(message, *args):
    print(message % args, file=sys.stderr)


def get_git_tags():
    return set(Popen(['git', 'tag'], stdout=PIPE).communicate()[0].splitlines())


def git_is_clean():
    return Popen(['git', 'diff', '--quiet']).wait() == 0


def make_git_commit(message, *args):
    message = message % args
    Popen(['git', 'commit', '-am', message]).wait()


def make_git_tag(tag):
    info('Tagging "%s"', tag)
    Popen(['git', 'tag', '-s', '-a', tag]).wait()


def update_download_url(filename, version):
    full_url = 'https://github.com/croscon/fleaker/archive/{}.tar.gz'
    full_url = full_url.format(version)
    set_filename_version('setup.py', full_url, 'download_url')


def main():
    parser = argparse.ArgumentParser(description=('Release a new version of'
                                                  ' Fleaker'))
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()

    pypi_alias = 'pypi' if not args.test else 'pypitest'

    os.chdir(os.path.join(os.path.dirname(__file__), '..'))

    rv = parse_changelog()
    if rv is None:
        fail('Could not parse changelog')

    version, release_date, codename = rv
    version = version
    tag_version = 'v' + version
    dev_version = version + '-dev'

    info('Releasing %s (codename %s, release date %s)',
         version, codename, release_date.strftime('%d/%m/%Y'))
    tags = get_git_tags()

    if version in tags:
        fail('Version "%s" is already tagged', version)
    if release_date.date() != date.today():
        fail('Release date is not today (%s != %s)',
             release_date.date(), date.today())

    if not git_is_clean():
        fail('You have uncommitted changes in git')

    set_init_version(version)
    update_download_url('setup.py', tag_version)
    make_git_commit('Bump version number to %s', version)
    make_git_tag(tag_version)
    build_and_upload(pypi_alias)
    set_init_version(dev_version)


if __name__ == '__main__':
    main()
