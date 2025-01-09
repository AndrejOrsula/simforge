# New Integrations

Supporting a new external framework via SimForge [Integration](../integrations/index.md) does not follow a strict pattern, as it depends on the specific requirements of that framework. Before getting started, make sure to read its documentation to understand its API and any limitations or constraints. Then, take a look at the existing integrations in the SimForge codebase to get an idea of how to structure your integration.

In a nutshell, the integration should consume any [Asset](../assets/index.md) definition and generate/export the requested number of asset variants to an intermediate file format supported by the external framework. Then, it should spawn the assets in the framework and optionally configure them based on the metadata provided by the generator. The integration can either be implemented as a Python function or a class, depending on the desired ergonomics.

If the framework requires a specific environment that is not compatible with the generator, consider generating the assets in a subprocess via `Generator.generate_subprocess()` instead of `Generator.generate()`. This way, the generator can run in a separate process with the required environment, and the integration can spawn the assets in the framework without any compatibility issues.

Template:

```py
from simforge import Asset


def spawn_simforge_asset(
    asset: Asset,
    num_assets: int = 1,
    seed: int = 0,
    subprocess: bool = False,
):
    # Select an intermediate model format supported by the framework
    FILE_FORMAT: ModelFileFormat = ...

    # Instantiate the generator associated with the asset
    generator = asset.generator_type(
        num_assets=num_assets,
        seed=seed,
        file_format=FILE_FORMAT,
    )

    # Generate the assets
    if subprocess:
        generator_output = generator.generate_subprocess(asset)
    else:
        generator_output = generator.generate(asset)

    # Iterate over the generator output
    for filepath, metadata in generator_output:
        # TODO: Spawn the asset from filepath
        # TODO: Configure the asset from metadata
```

If you have any questions regarding a specific integration, feel free to [open a new issue](https://github.com/AndrejOrsula/simforge/issues/new).
