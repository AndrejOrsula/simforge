## Base <https://hub.docker.com/_/python>
ARG PYTHON_TAG="3.11"
FROM python:${PYTHON_TAG}

## Use bash as the default shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

## Define the workspace of the project
ARG SF_PATH="/root/ws"
WORKDIR "${SF_PATH}"

## Install dependencies
# hadolint ignore=DL3013,SC2046
RUN --mount=type=bind,source=pyproject.toml,target="${SF_PATH}/pyproject.toml" \
    python -m pip install --no-input --no-cache-dir --upgrade pip && \
    python -m pip install --no-input --no-cache-dir toml~=0.10 && \
    python -m pip install --no-input --no-cache-dir $(python -c "f='${SF_PATH}/pyproject.toml'; from toml import load; print(' '.join(filter(lambda d: not d.startswith(p['name']), (*p.get('dependencies', ()), *(d for ds in p.get('optional-dependencies', {}).values() for d in ds)))) if (p := load(f).get('project', None)) else '')")

## Copy the project
COPY . "${SF_PATH}"

## Install the project
RUN python -m pip install --no-input --no-cache-dir --no-deps --editable "${SF_PATH}[all]"

## Set the default command
CMD ["bash"]

############
### Misc ###
############

## Skip writing Python bytecode to the disk to avoid polluting mounted host volume with `__pycache__` directories
ENV PYTHONDONTWRITEBYTECODE=1
