#!/bin/bash -eu

python_version="$1"

echo "==> Selecting requirements for python ${python_version} ..."

freeze_dir="$(dirname "$0")/freeze"
requirements_dir="$(dirname "$0")/requirements"
constraints="${requirements_dir}/constraints.txt"

if [ "$(ls "${freeze_dir}")" ]; then
    echo "Using requirements directory: ${freeze_dir}"
    cd "${freeze_dir}"

    version_requirements=("${python_version}.txt")
else
    echo "Using requirements directory: ${requirements_dir}"
    cd "${requirements_dir}"

    requirements=()

    for requirement in *.txt; do
        if [ "${requirement}" != "constraints.txt" ]; then
            requirements+=("${requirement}")
        fi
    done

    version_requirements=()

    for requirement in "${requirements[@]}"; do
        case "${python_version}" in
            "2.6")
                case "${requirement}" in
                    "integration.cloud.azure.txt") continue ;;
                esac
        esac

        version_requirements+=("${requirement}")
    done
fi

if [ "${python_version}" = "2.6" ]; then
    get_pip="/tmp/get-pip2.6.py"
else
    get_pip="/tmp/get-pip.py"
fi

echo "==> Installing pip for python ${python_version} ..."

set -x
"python${python_version}" --version
"python${python_version}" "${get_pip}" --disable-pip-version-check -c "${constraints}" 'pip==9.0.2'
"pip${python_version}" --version --disable-pip-version-check
set +x

echo "==> Installing requirements for python ${python_version} ..."

for requirement in "${version_requirements[@]}"; do
    set -x
    "pip${python_version}" install --disable-pip-version-check -c "${constraints}" -r "${requirement}"
    set +x
done

echo "==> Checking for requirements conflicts for ${python_version} ..."

after=$("pip${python_version}" list --disable-pip-version-check --format=columns)

for requirement in "${version_requirements[@]}"; do
    before="${after}"

    set -x
    "pip${python_version}" install --disable-pip-version-check -c "${constraints}" -r "${requirement}"
    set +x

    after=$("pip${python_version}" list --disable-pip-version-check --format=columns)

    if [ "${before}" != "${after}" ]; then
        echo "==> Conflicts detected in requirements for python ${python_version}: ${requirement}"
        echo ">>> Before"
        echo "${before}"
        echo ">>> After"
        echo "${after}"
        exit 1
    fi
done

echo "==> Finished with requirements for python ${python_version}."
