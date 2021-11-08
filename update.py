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
    parser.add_argument('--ref')

    args = parser.parse_args()
    ref = args.ref

    if not ref:
        with urllib.request.urlopen(f'https://api.github.com/repos/ansible/ansible/branches/stable-2.12') as response:
            data = json.load(response)

        ref = data['commit']['sha']

    with open('files/ansible-test-ref.txt', 'w') as file:
        file.write(f'{ref}\n')

    with urllib.request.urlopen(f'https://api.github.com/repos/ansible/ansible/contents/test/lib/ansible_test/_data/requirements/?ref={ref}') as response:
        files = json.loads(response.read().decode())

    requirements_dir = 'requirements'
    untouched_paths = set(os.path.join(requirements_dir, file) for file in os.listdir(requirements_dir))

    for file in files:
        name = file['name']
        download_url = file['download_url']

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
        if os.path.basename(path) == 'common.txt':
            continue

        os.unlink(path)

        print('%s: deleted' % path)


if __name__ == '__main__':
    main()
