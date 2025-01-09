# Usage of SimForge

SimForge can be used in two primary ways:

- [**Command Line Interface (CLI)**](../instructions/cli.md) - **Offline** generation and management of assets
- [**Integrations**](../integrations/index.md) - **Online** generation and application-specific configuration of assets

## Command Line Interface (CLI)

The [`simforge` CLI](../instructions/cli.md) is the most straightforward way to get started with SimForge. It allows you to generate and export assets directly from the command line without needing to write any code. You can then use the generated assets in your application by importing them as needed. Furthermore, the CLI provides a convenient way to list and manage the available assets.

The CLI should be used as a starting point. It supports exporting assets in a variety of formats that are compatible with most external applications — even if a direct integration with SimForge is not yet available.

## Integrations

[Integrations](../integrations/index.md) offer a more streamlined experience for using SimForge within a specific game engine or physics simulator. These modules provide APIs that automate the on-demand process of generating, caching and importing assets into external frameworks while abstracting away the underlying complexity.

Integrations are the recommended way to use SimForge for specific applications in the long term, as they provide a more ergonomic and efficient workflow. However, they may require additional setup and configuration to get started.

The number of available integrations is currently limited but expected to grow over time as the framework matures. Contributions are always welcome!
