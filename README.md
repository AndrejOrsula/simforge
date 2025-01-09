<h1 align="center">SimForge</h1>

[![PyPi](https://img.shields.io/pypi/v/simforge.svg)](https://pypi.python.org/pypi/simforge)
[![Python](https://github.com/AndrejOrsula/simforge/actions/workflows/python.yml/badge.svg)](https://github.com/AndrejOrsula/simforge/actions/workflows/python.yml)
[![Docker](https://github.com/AndrejOrsula/simforge/actions/workflows/docker.yml/badge.svg)](https://github.com/AndrejOrsula/simforge/actions/workflows/docker.yml)
[![Docs](https://github.com/AndrejOrsula/simforge/actions/workflows/docs.yml/badge.svg)](https://github.com/AndrejOrsula/simforge/actions/workflows/docs.yml)
[![Codecov](https://codecov.io/gh/AndrejOrsula/simforge/graph/badge.svg)](https://codecov.io/gh/AndrejOrsula/simforge)

**SimForge** is a framework for creating diverse virtual environments through procedural generation.

## Overview

The framework implements a modular approach with three primary concepts: **Assets**, **Generators**, and **Integrations**.

### Assets

Assets are the registered building blocks that range from simple images and meshes to complex articulated models. Their definitions reside in external repositories that can be shared and reused across projects. Example: [SimForge Foundry](https://github.com/AndrejOrsula/simforge_foundry)

### Generators

Generators are responsible for automating the creation of **Assets** from their definitions in a deterministic manner. They interface with external tools and libraries to produce the desired output. Example: [Blender](https://AndrejOrsula.github.io/simforge/generators/blender.html)

### Integrations

Integrations seamlessly bridge the gap between the **Generators** and external frameworks such as game engines or physics simulators. These modules leverage domain-specific APIs to import and configure the generated **Assets**. Example: [Isaac Lab](https://AndrejOrsula.github.io/simforge/integrations/isaaclab.html)

## Documentation

The full documentation is available in its raw form inside the [docs](docs) directory. The compiled version is hosted [online](https://AndrejOrsula.github.io/simforge) in a more accessible format.

<a href="https://AndrejOrsula.github.io/simforge"> <img alt="HTML" src="https://github.com/AndrejOrsula/awesome-space-robotics/assets/22929099/3c8accf7-5acb-4bcd-9553-bf49cc622abe" width="96" height="96"></a>

## License

This project is dual-licensed under either the [MIT](LICENSE-MIT) or [Apache 2.0](LICENSE-APACHE) licenses.
