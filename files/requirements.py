"""Find installed Python interpreters and install requirements in each one."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

from installer import (
    Pip,
    Python,
    display,
    iterate_pythons,
    str_to_version,
)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('context')

    args = parser.parse_args()
    context = args.context

    base_directory = os.path.dirname(os.path.abspath(__file__))
    freeze_directory = os.path.join(base_directory, context, 'freeze')
    requirements_directory = os.path.join(base_directory, context, 'requirements')

    if len([name for name in os.listdir(freeze_directory) if not name.startswith('.')]):
        source_directory = freeze_directory
        final = True
    else:
        source_directory = requirements_directory
        final = False

    for python in iterate_pythons():
        setup_python(python, source_directory, final)


def setup_python(python: Python, source_directory: str, final: bool) -> None:
    """Setup the specified Python interpreter."""
    display.section(f'Started setup of Python {python.version}')
    display.info(python.path)

    display.section(f'Finding requirements and constraints for Python {python.version}')
    display.info(source_directory)

    requirements_list = []

    if final:
        constraints = f'{python.version}.txt'

        requirements_list.append(constraints)
    else:
        constraints = 'constraints.txt'

        for filename in sorted(os.listdir(source_directory)):
            name, ext = os.path.splitext(filename)

            if ext != '.txt' or name == 'constraints':
                continue

            if not filename.startswith('ansible-test.') and not filename.startswith('units.') and str_to_version(python.version) < (3, 8):
                continue

            requirements_list.append(filename)

    pip = Pip(python)

    for requirements in requirements_list:
        display.section(f'Installing requirements for Python {python.version} ({requirements})')
        pip.install(['-r', os.path.join(source_directory, requirements), '-c', os.path.join(source_directory, constraints)])

    if len(requirements_list) > 1:
        display.section(f'Checking for requirements conflicts for Python {python.version}')
        expected = pip.list()

        for requirements in requirements_list:
            pip.install(['-r', os.path.join(source_directory, requirements), '-c', os.path.join(source_directory, constraints)])
            actual = pip.list()

            if expected != actual:
                display.error(f'Conflicts detected in requirements for Python {python.version} ({requirements})')
                display.error('>>> Expected')

                for name, version in expected:
                    display.error(f'{name} {version}')

                display.error('>>> Actual')

                for name, version in actual:
                    display.error(f'{name} {version}')

                sys.exit(1)

    display.section(f'Checking pip integrity for Python {python.version}')
    pip.check()

    display.section(f'Checking PyYAML for libyaml support for Python {python.version}')

    result = subprocess.run([python.path, '-c', 'from yaml import CLoader'], capture_output=True)

    if result.returncode:
        display.error('PyYAML was not compiled with libyaml support.')
        sys.exit(1)

    display.section(f'Checking coverage C extension support for Python {python.version}')

    result = subprocess.run([python.path, '-m', 'coverage', '--version'], capture_output=True, check=True, text=True)

    if 'with C extension' not in result.stdout:
        display.error(f'The coverage module does not have a working C extension:\n{result.stdout}')
        sys.exit(1)

    display.section(f'Listing installed packages for Python {python.version}')

    for name, version in pip.list():
        display.info(f'{name} {version}')

    display.section(f'Completed setup of Python {python.version}')


if __name__ == '__main__':
    main()
