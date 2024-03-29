#!/usr/bin/env python
"""Update requirements from the ansible/ansible repository."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request


def main() -> None:
    """Main program entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--branch')
    parser.add_argument('--ref')

    args = parser.parse_args()
    branch = args.branch
    ref = args.ref

    if not branch:
        with open('files/ansible-test-branch.txt') as file:
            branch = file.read().strip()

    if not ref:
        with urllib.request.urlopen(f'https://api.github.com/repos/ansible/ansible/branches/{branch}') as response:
            data = json.load(response)

        ref = data['commit']['sha']

    with open('files/ansible-test-branch.txt', 'w') as file:
        file.write(f'{branch}\n')

    with open('files/ansible-test-ref.txt', 'w') as file:
        file.write(f'{ref}\n')

    with urllib.request.urlopen(f'https://api.github.com/repos/ansible/ansible/contents/test/lib/ansible_test/_data/requirements?ref={ref}') as response:
        files = json.loads(response.read().decode())

    files.append(dict(
        name='constants.py',
        download_url=f'https://raw.githubusercontent.com/ansible/ansible/{ref}/test/lib/ansible_test/_util/target/common/constants.py',
    ))

    requirements_dir = 'requirements'
    untouched_paths = set(os.path.join(requirements_dir, file) for file in os.listdir(requirements_dir))

    for file in files:
        name = file['name']
        download_url = file['download_url']

        if name.startswith('sanity.') and (name.endswith('.txt') or name.endswith('.in')):
            continue  # sanity test requirements are installed by ansible-test's --prime-venvs option

        path = os.path.join(requirements_dir, name)

        if path in untouched_paths:
            untouched_paths.remove(path)

        with urllib.request.urlopen(download_url) as response:
            latest_contents = response.read().decode()

        if os.path.exists(path):
            with open(path, 'r') as contents_fd:
                current_contents = contents_fd.read()
        else:
            current_contents = ''

        if latest_contents == current_contents:
            print('%s: current' % path)
            continue

        with open(path, 'w') as contents_fd:
            contents_fd.write(latest_contents)

        print('%s: updated' % path)

    for path in untouched_paths:
        os.unlink(path)

        print('%s: deleted' % path)


if __name__ == '__main__':
    main()
