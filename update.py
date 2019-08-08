#!/usr/bin/env python3
"""Update requirements from the ansible/ansible repository."""

import json
import os
import urllib.request


def main():
    """Main program entry point."""

    # Dictionary of URLs containing a mapping of existing file names to their new file name
    # Example: 'url': {'current-filename.txt', 'new-filename.txt'}
    source_requirements = {
        'https://api.github.com/repos/ansible/ansible/contents/test/sanity/requirements.txt': {
            'requirements.txt': 'ansible-sanity.txt',
        },
        'https://api.github.com/repos/ansible/ansible/contents/test/lib/ansible_test/_data/requirements/': {},
    }

    files = []
    for url, mapping in source_requirements.items():
        untouched_mappings = set(source_requirements[url].keys())
        with urllib.request.urlopen(url) as response:
            content = json.loads(response.read().decode())
            if not isinstance(content, list):
                content = [content]

            # If we have a rename mapping, rename the file
            for i in content:
                name = i['name']
                if mapping.get(name):
                    untouched_mappings.remove(name)
                    i['name'] = mapping.get(name)

            # Warn on any rename mappings that were not used to catch typos in the mapping or files that no longer exist
            for m in untouched_mappings:
                print('WARNING: %s specified for renaming but was not found in list of downloaded files' % m)

            files.extend(content)

    requirements_dir = 'requirements'

    untouched_paths = set(os.path.join(requirements_dir, file) for file in os.listdir(requirements_dir))

    for file in files:
        name = file['name']

        # # Rename sanity test requirements so they do not conflict with ansible-test sanity requirements
        # if 'ansible/contents/test/sanity/requirements.txt' in name:
        #     name = 'ansible-sanity.txt'

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
        os.unlink(path)

        print('%s: deleted' % path)


if __name__ == '__main__':
    main()
