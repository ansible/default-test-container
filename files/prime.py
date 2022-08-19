"""Prime ansible-test sanity virtual environments."""
from __future__ import annotations

import argparse
import pathlib
import os
import shutil
import subprocess
import sys

from installer import (
    Pip,
    display,
    get_default_python,
)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('context')

    args = parser.parse_args()
    context = args.context

    base_directory = os.path.dirname(os.path.abspath(__file__))
    freeze_directory = os.path.join(base_directory, context, 'freeze')

    tmp = pathlib.Path('/tmp')

    if unexpected := list(tmp.iterdir()):
        raise Exception(f'Unexpected temporary files: {unexpected}')

    if len([name for name in os.listdir(freeze_directory) if not name.startswith('.')]):
        setup_sanity_venvs(context)

    for path in tmp.iterdir():
        display.info(f'Removing temporary file: {path}')
        path.unlink()


def setup_sanity_venvs(context: str) -> None:
    """Setup the sanity test virtual environments."""
    base_directory = '/tmp/sanity'
    clone_directory = os.path.join(base_directory, 'ansible')
    prime = [sys.executable, os.path.join(clone_directory, 'bin', 'ansible-test'), 'sanity', '--prime-venvs', '-v', '--color', '--allow-disabled']
    working_directory = clone_directory
    repo = 'https://github.com/ansible/ansible'

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ansible-test-branch.txt')) as file:
        branch = file.read().strip()

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ansible-test-ref.txt')) as file:
        ref = file.read().strip()

    # NOTE: Redirection of stderr to stdout below prevents Docker from making stderr output red.

    display.section('Cloning Ansible')
    subprocess.run(['git', 'clone', '--depth', '500', '--branch', branch, repo, clone_directory], check=True, stderr=subprocess.STDOUT)
    subprocess.run(['git', 'reset', '--hard', ref], cwd=clone_directory, check=True)

    if context == 'default':
        working_directory = os.path.join(base_directory, 'ansible_collections', 'ns', 'col')

        os.makedirs(working_directory)

        with open(os.path.join(working_directory, 'placeholder.txt'), 'w'):
            pass

        # The 'sanity.import' environment is needed for all collection import sanity tests.
        # However, since the PyPI proxy endpoint is static, it may not have the required packages.
        # If any version requires use of the proxy, first install the 'sanity.import' requirements using the default Python version.

        if Pip.PIP_PROXY_VERSIONS:
            version = get_default_python().version

            display.section(f'Priming Sanity Virtual Environments (import {version})')
            import_cmd = ['--python', version, '--test', 'import']
            subprocess.run(prime + import_cmd, cwd=working_directory, check=True, stderr=subprocess.STDOUT)

        for version in Pip.PIP_PROXY_VERSIONS:
            display.section(f'Priming Sanity Virtual Environments (import {version} with coverage)')
            import_cmd = ['--python', version, '--test', 'import', '--coverage', '--pypi-proxy', '--pypi-endpoint', Pip.PIP_INDEX]
            subprocess.run(prime + import_cmd, cwd=working_directory, check=True, stderr=subprocess.STDOUT)

    display.section('Priming Sanity Virtual Environments (without coverage)')
    subprocess.run(prime, cwd=working_directory, check=True, stderr=subprocess.STDOUT)

    display.section('Priming Sanity Virtual Environments (with coverage)')
    subprocess.run(prime + ['--coverage'], cwd=working_directory, check=True, stderr=subprocess.STDOUT)

    display.section('Cleaning Up')
    shutil.rmtree(base_directory)
    shutil.rmtree(os.path.expanduser('~/.cache/pip'))


if __name__ == '__main__':
    main()
