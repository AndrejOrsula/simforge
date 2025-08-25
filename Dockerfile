## Base <https://hub.docker.com/_/python>
ARG PYTHON_TAG="3.11"
FROM python:${PYTHON_TAG}

## Use bash as the default shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

## Define the workspace of the project
ARG SF_PATH="/root/ws"
WORKDIR "${SF_PATH}"

## Install system dependencies
# hadolint ignore=DL3008
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    bash-completion \
    libgl1 \
    libxfixes3 \
    libxi6 \
    libxkbcommon-x11-0 && \
    rm -rf /var/lib/apt/lists/*

## Install Python dependencies
# hadolint ignore=DL3013,SC2046
RUN --mount=type=bind,source=pyproject.toml,target="${SF_PATH}/pyproject.toml" \
    python -m pip install --no-input --no-cache-dir --upgrade pip && \
    python -m pip install --no-input --no-cache-dir toml~=0.10 && \
    python -m pip install --no-input --no-cache-dir $(python -c "f='${SF_PATH}/pyproject.toml'; from toml import load; print(' '.join(filter(lambda d: not d.startswith(p['name'] + '['), (*p.get('dependencies', ()), *(d for ds in p.get('optional-dependencies', {}).values() for d in ds)))) if (p := load(f).get('project', None)) else '')")

## Copy the project
COPY . "${SF_PATH}"

## Install the project
RUN python -m pip install --no-input --no-cache-dir --no-deps --editable "${SF_PATH}[all]"

## Assets
ARG DEV=false
ARG SIMFORGE_FOUNDRY_DEV=true
ARG SIMFORGE_FOUNDRY_PATH="/root/simforge_foundry"
ARG SIMFORGE_FOUNDRY_REMOTE="https://github.com/AndrejOrsula/simforge_foundry.git"
ARG SIMFORGE_FOUNDRY_BRANCH="dev"
RUN if [[ "${DEV,,}" = true && "${SIMFORGE_FOUNDRY_DEV,,}" = true ]]; then \
    git clone "${SIMFORGE_FOUNDRY_REMOTE}" "${SIMFORGE_FOUNDRY_PATH}" --branch "${SIMFORGE_FOUNDRY_BRANCH}" && \
    python -m pip install --no-input --no-cache-dir --editable "${SIMFORGE_FOUNDRY_PATH}" ; \
    fi

## Configure argcomplete
RUN echo "source /etc/bash_completion" >> "/etc/bash.bashrc" && \
    register-python-argcomplete simforge > "/etc/bash_completion.d/simforge"

## Set the default command
CMD ["bash"]

############
### Misc ###
############

## Downgrade numpy to suppress warnings
RUN python -m pip install --no-input --no-cache-dir numpy~=1.26

## Skip writing Python bytecode to the disk to avoid polluting mounted host volume with `__pycache__` directories
ENV PYTHONDONTWRITEBYTECODE=1
