"""Find installed Python interpreters and install requirements in each one."""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import tempfile

from installer import (
    Pip,
    Python,
    display,
    iterate_pythons,
    str_to_version,
)

from default.requirements.constants import (
    CONTROLLER_PYTHON_VERSIONS,
)

CONTROLLER_MIN_PYTHON_STR = CONTROLLER_PYTHON_VERSIONS[0]
CONTROLLER_MIN_PYTHON = str_to_version(CONTROLLER_MIN_PYTHON_STR)


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

    display.section(f'Setting up Python requirements')
    display.info(f'Python {CONTROLLER_MIN_PYTHON_STR} is the minimum version supported by the Ansible controller.')

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

            if not filename.startswith('ansible-test.') and not filename.startswith('units.') and str_to_version(python.version) < CONTROLLER_MIN_PYTHON:
                continue

            requirements_list.append(filename)

    pip = Pip(python)

    pre_build_path = pathlib.Path(__file__).parent / 'pre-build' / f'{python.version}.txt'

    if pre_build_path.exists():
        for pre_build in parse_pre_build_instructions(pre_build_path.read_text()):
            display.section(f'Pre-building a wheel for Python {python.version} ({pre_build.requirement})')
            pre_build.execute(pip)

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

    pip.purge_cache()


class PreBuild:
    """Parsed pre-build instructions."""

    def __init__(self, requirement: str) -> None:
        self.requirement = requirement
        self.constraints: list[str] = []

    def execute(self, pip: Pip) -> None:
        """Execute these pre-build instructions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            constraints = '\n'.join(self.constraints) + '\n'
            constraints_path = pathlib.Path(temp_dir, 'constraints.txt')

            pathlib.Path(constraints_path).write_text(constraints)

            pip.wheel([self.requirement], constraints=constraints_path)


def parse_pre_build_instructions(requirements):  # type: (str) -> list[PreBuild]
    """Parse the given pip requirements and return a list of extracted pre-build instructions."""
    pre_build_prefix = '# pre-build '
    pre_build_requirement_prefix = pre_build_prefix + 'requirement: '
    pre_build_constraint_prefix = pre_build_prefix + 'constraint: '

    lines = requirements.splitlines()
    pre_build_lines = [line for line in lines if line.startswith(pre_build_prefix)]

    instructions = []  # type: list[PreBuild]

    for line in pre_build_lines:
        if line.startswith(pre_build_requirement_prefix):
            instructions.append(PreBuild(line[len(pre_build_requirement_prefix):]))
        elif line.startswith(pre_build_constraint_prefix):
            instructions[-1].constraints.append(line[len(pre_build_constraint_prefix):])
        else:
            raise RuntimeError('Unsupported pre-build comment: ' + line)

    return instructions


if __name__ == '__main__':
    main()
