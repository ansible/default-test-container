"""Prime ansible-test sanity virtual environments."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from installer import (
    display,
)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('context')

    args = parser.parse_args()
    context = args.context

    base_directory = os.path.dirname(os.path.abspath(__file__))
    freeze_directory = os.path.join(base_directory, context, 'freeze')

    if len([name for name in os.listdir(freeze_directory) if not name.startswith('.')]):
        setup_sanity_venvs(context)


def setup_sanity_venvs(context: str) -> None:
    """Setup the sanity test virtual environments."""
    base_directory = '/tmp/sanity'
    clone_directory = os.path.join(base_directory, 'ansible')
    prime = [sys.executable, os.path.join(clone_directory, 'bin', 'ansible-test'), 'sanity', '--prime-venvs', '-v', '--color', '--allow-disabled']
    working_directory = clone_directory
    repo = 'https://github.com/ansible/ansible'

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ansible-test-ref.txt')) as file:
        ref = file.read().strip()

    # NOTE: Redirection of stderr to stdout below prevents Docker from making stderr output red.

    display.section('Cloning Ansible')
    subprocess.run(['git', 'clone', '--depth', '500', '--branch', 'devel', repo, clone_directory], check=True, stderr=subprocess.STDOUT)
    subprocess.run(['git', 'reset', '--hard', ref], cwd=clone_directory, check=True)

    if context == 'default':
        working_directory = os.path.join(base_directory, 'ansible_collections', 'ns', 'col')

        os.makedirs(working_directory)

        with open(os.path.join(working_directory, 'placeholder.txt'), 'w'):
            pass

        display.section('Priming Sanity Virtual Environments (import 2.6 with coverage)')
        import26 = ['--python', '2.6', '--test', 'import', '--coverage', '--pypi-proxy', '--pypi-endpoint', 'https://d2c8fqinjk13kw.cloudfront.net/simple/']
        subprocess.run(prime + import26, cwd=working_directory, check=True, stderr=subprocess.STDOUT)

    display.section('Priming Sanity Virtual Environments (without coverage)')
    subprocess.run(prime, cwd=working_directory, check=True, stderr=subprocess.STDOUT)

    display.section('Priming Sanity Virtual Environments (with coverage)')
    subprocess.run(prime + ['--coverage'], cwd=working_directory, check=True, stderr=subprocess.STDOUT)

    display.section('Cleaning Up')
    shutil.rmtree(base_directory)
    shutil.rmtree(os.path.expanduser('~/.cache/pip'))


if __name__ == '__main__':
    main()
