# Installation

All releases of SimForge are available at [PyPI](https://pypi.org/project/simforge) and can be installed using your preferred Python package manager:

```bash
# Install SimForge with all extras
pip install simforge[all]
```

## Extras

SimForge specifies several optional dependencies to enhance its functionality. These can be specified as extras:

- **`all`** - Include all other SimForge extras (recommended)
- **`assets`** - Primary collection of SimForge assets
- **`bpy`** - Enable Blender generator via its Python API
- **`cli`** - Utilities for enhancing the CLI experience
- **`dev`** - Utilities for development and testing

Multiple extras can be specified at once by separating them with commas:

```bash
# Install SimForge with assets and CLI extras
pip install simforge[assets,cli]
```

## Docker

> - [Docker Engine](https://docs.docker.com/engine) is required to use SimForge in a containerized environment.
> - [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit) is recommended to automatically utilize available NVIDIA GPUs for workloads such as texture baking.
>
> For convenience, [`install_docker.bash`](https://github.com/AndrejOrsula/simforge/blob/main/.docker/host/install_docker.bash) script is included to setup Docker on a Linux host.

A minimal [Dockerfile](https://github.com/AndrejOrsula/simforge/blob/main/Dockerfile) is provided for convenience with `all` extras included. Pre-built images for every release are available on [Docker Hub](https://hub.docker.com/r/andrejorsula/simforge/tags) and [GitHub Container Registry](https://github.com/AndrejOrsula/simforge/pkgs/container/simforge) for easy access:

```bash
# Docker Hub
docker pull andrejorsula/simforge
```

```bash
# [ALTERNATIVE] GitHub Container Registry
docker pull ghcr.io/andrejorsula/simforge
```

For convenience, [`.docker/run.bash`](https://github.com/AndrejOrsula/simforge/blob/main/.docker/run.bash) script is included to run the Docker container with appropriate arguments, environment variables, and volumes for persistent cache storage:

```bash
# Path to a cloned repository
simforge/.docker/run.bash $TAG $CMD
```

```bash
# [ALTERNATIVE] Raw content via wget
WITH_DEV_VOLUME=false bash -c "$(wget -qO - https://raw.githubusercontent.com/AndrejOrsula/simforge/refs/heads/main/.docker/run.bash)" -- $TAG $CMD
```

```bash
# [ALTERNATIVE] Raw content via curl
WITH_DEV_VOLUME=false bash -c "$(curl -fsSL https://raw.githubusercontent.com/AndrejOrsula/simforge/refs/heads/main/.docker/run.bash)" -- $TAG $CMD
```
