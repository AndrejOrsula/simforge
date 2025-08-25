# Command Line Interface (CLI)

After [installing SimForge](../getting_started/installation.md), the CLI can be accessed via the following commands:

```bash
# Run as package entrypoint
python3 -m simforge
```

```bash
# Run via installed command
simforge
```

## Subcommands

The CLI provides a number of subcommands that leverage the underlying SimForge API. Each subcommand has its own set of options and arguments that can be accessed via the `-h` or `--help` flag.

### `simforge gen`

Generate variants of registered assets based on the provided arguments (`simforge gen -h`).

#### Examples

Generate a single variant of a registered asset named `"model1"` (exported to `~/.cache/simforge`):

```bash
simforge gen model1
```

Generate `-n 2` variants, starting at random seed `-s 100`, of an asset named `"geo1"`:

```bash
simforge gen -n 2 -s 100 geo1
```

Generate `-n 3` variants for two different assets named `"geo1"` and `"model2"` (3 each) while exporting them to a file format with the extension `-e stl`:

```bash
simforge gen -n 3 geo1 model2 -e stl
```

Generate `-n 5` variants of an asset named `"geo2"` in a custom output directory `-o custom/cache`:

```bash
simforge gen -n 5 geo2 -o custom/cache
```

Use a `--subprocess` to generate `-n 8` variants of `"model1"`:

```bash
simforge gen -n 8 --subprocess model1
```

> Running in a subprocess is especially useful if the generator is non-compatible with the current environment. For example, Blender requires a specific version of Python that might differ from the system's default. The `--subprocess` flag thus allows the generator to run in a separate process with the embedded Python interpreter of the locally-installed Blender application.

Attributes can be overridden during generation using the `--set` flag. The format for each override is `attribute_path=value`, where `attribute_path` is the dot-separated path to the attribute you want to override (e.g., `ops.0.attribute1`). The path does not need to be fully specified if the attribute is unique within the asset (e.g., `attribute2` instead of `ops.0.attribute2`).

```bash
simforge gen model1 --set ops.0.attribute1=4 attribute2=5.5
```

______________________________________________________________________

### `simforge ls`

List all registered assets in a tabular format.

```bash
❯ simforge ls
                SimForge Asset Registry
┏━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ # ┃   Type   ┃ Package  ┃ Name   ┃ Semantics ┃ Cached ┃
┡━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ 1 │ geometry │ package1 │ geo1   │           │        │
│ 2 │ geometry │ package1 │ geo2   │           │        │
├───┼──────────┼──────────┼────────┼───────────┼────────┤
│ 3 │ material │ package2 │ mat1   │           │        │
│ 4 │ material │ package3 │ mat2   │           │        │
├───┼──────────┼──────────┼────────┼───────────┼────────┤
│ 5 │  model   │ package1 │ model1 │           │        │
│ 6 │  model   │ package3 │ model2 │           │        │
└───┴──────────┴──────────┴────────┴───────────┴────────┘
```

> Note: This subcommand requires the [`rich`](https://rich.readthedocs.io) package to be installed (included in the [`cli` extra](../getting_started/installation.md#extras))

______________________________________________________________________

### `simforge info`

Show configurable attributes for registered asset(s).

```bash
❯ simforge info <asset_name>
          Configurable attributes for asset: <asset_name>
┏━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Asset Name   ┃ Attribute Name   ┃ Attribute Type ┃ Default Value ┃
┡━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ <asset_name> │ ops.0.attribute1 │ int            │ 7             │
│              │ ops.0.attribute2 │ float          │ 4.2           │
└──────────────┴──────────────────┴────────────────┴───────────────┘
```

> Note: This subcommand requires the [`rich`](https://rich.readthedocs.io) package to be installed (included in the [`cli` extra](../getting_started/installation.md#extras))

______________________________________________________________________

### `simforge clean`

Remove all generated assets that are cached on the system.

```bash
❯ simforge clean
[HH:MM:SS] WARNING  This will remove all SimForge assets cached on your system under /home/USER/.cache/simforge (X.YZ GB)
Are you sure you want to continue? [y/n] (n):
```
