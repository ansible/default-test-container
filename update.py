#!/usr/bin/env python3
"""Update requirements from the ansible/ansible repository."""

import json
import os
import sys
import urllib.request


def main():
    """Main program entry point."""

    # Dictionary of URLs containing a mapping of existing file names to their new file name
    # Example: 'url': {'current-filename.txt', 'new-filename.txt'}
    source_requirements = {
        'https://api.github.com/repos/ansible/ansible/contents/test/lib/ansible_test/_data/requirements/': {},
    }

    files = []
    untouched_mappings = {}
    for url, mapping in source_requirements.items():
        untouched_mappings[url] = set(mapping)
        with urllib.request.urlopen(url) as response:
            content = json.loads(response.read().decode())
            if not isinstance(content, list):
                content = [content]

            purge = []

            # If we have a rename mapping, rename the file
            for i in content:
                name = i['name']

                # skip "cloud" requirements files
                if name.startswith('integration.cloud.'):
                    purge.append(i)
                    continue

                if mapping.get(name):
                    untouched_mappings[url].remove(name)
                    i['name'] = mapping.get(name)

            for item in purge:
                content.remove(item)

            files.extend(content)

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

        if name == 'constraints.txt':
            original = latest_contents.splitlines()
            updated = []

            for line in original:
                updated.append(line)

                if line.startswith("cryptography < 2.2 ; python_version < '2.7' "):
                    updated.append("cryptography < 3.4 ; python_version >= '2.7' # limit cryptography to the latest version ansible-test will accept")

            latest_contents = '\n'.join(updated) + '\n'

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

    # Error on any rename mappings that were not used to catch typos in the mapping or files that no longer exist
    for url in untouched_mappings:
        for m in untouched_mappings[url]:
            print('ERROR: Unable to rename %s from %s' % (m, url))

    if any(untouched_mappings[url] for url in untouched_mappings):
        sys.exit(1)


if __name__ == '__main__':
    main()
