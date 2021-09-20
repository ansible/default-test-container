#!/usr/bin/env python
"""Freeze container requirements for use with a final container build."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import typing as t


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('container')

    args = parser.parse_args()
    container = args.container

    print("Purging existing frozen requirements.")

    for name in os.listdir('freeze'):
        if name != '.freeze.txt':
            os.remove(os.path.join('freeze', name))

    print("Building a container to freeze the requirements.")

    subprocess.run(['docker', 'build', '-t', container, '.'], check=True)

    print('Finding supported Python versions.')

    names = subprocess.run(['docker', 'run', container, 'ls', '/usr/bin'], check=True, capture_output=True, text=True).stdout.splitlines()
    matches = [re.match(r'^python(?P<version>[0-9]+\.[0-9]+)$', name) for name in names]
    versions = [match.group('version') for match in matches if match]

    for version in sorted(versions, key=str_to_version):
        print(f'Freezing requirements for Python {version}.')
        command = ['docker', 'run', container, f'/usr/bin/python{version}', '-m', 'pip.__main__', 'freeze', '-qqq', '--disable-pip-version-check']
        freeze = subprocess.run(command, check=True, capture_output=True, text=True).stdout

        with open(f'freeze/{version}.txt', 'w') as freeze_file:
            freeze_file.write(freeze)

    print("Freezing completed.")


def str_to_version(version: str) -> t.Tuple[int, ...]:
    """Return a version tuple from a version string."""
    return tuple(int(n) for n in version.split('.'))


if __name__ == '__main__':
    main()
