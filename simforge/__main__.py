#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
import argparse
import importlib
import inspect
import json
import os
import shutil
import sys
from functools import cache
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, Type

from simforge import SF_CACHE_DIR, Asset, AssetRegistry, AssetType, FileFormat
from simforge.utils import convert_to_snake_case, logging


def main():
    def impl(
        subcommand: Literal["gen", "ls", "clean", "repl", "docs", "test"], **kwargs
    ):
        match subcommand:
            case "gen":
                generate_assets(**kwargs)
            case "ls":
                list_assets(**kwargs)
            case "clean":
                clean_assets(**kwargs)
            case "repl":
                enter_repl(**kwargs)
            case "docs":
                serve_docs(**kwargs)
            case "test":
                run_tests(**kwargs)
            case _:
                raise ValueError(f'Unknown subcommand: "{subcommand}"')

    impl(**vars(parse_cli_args()))


### Generate ###
def generate_assets(
    ## Input
    asset_name: Iterable[str],
    ## Output
    outdir: str,
    ext: Iterable[str],
    ## Generator
    seed: int,
    num_assets: int,
    ## Export
    no_cache: bool,
    export_kwargs: Mapping[str, Any],
    ## Process
    subprocess: bool,
    multiprocessing: bool,
    ## Misc
    forwarded_args: Sequence[str] = (),
):
    if asset_name == "NO_REGISTERED_ASSETS":
        raise RuntimeError("No SimForge assets are registered")

    if "ALL" in asset_name:
        assets = (asset() for asset in _get_registered_assets())
    else:
        assets = []
        for name in set(asset_name):
            name = convert_to_snake_case(name)
            if asset := AssetRegistry.get_by_name(name):
                assets.append(asset())
            else:
                all_names = (
                    f'"{convert_to_snake_case(asset.__name__)}"'
                    for asset in _get_registered_assets()
                )
                raise ValueError(
                    f'Asset "{name}" not found among registered SimForge assets: {", ".join(all_names)}'
                )

    for asset in assets:
        generator = asset.generator_type(
            outdir=Path(outdir),
            seed=seed,
            num_assets=num_assets,
            file_format=[FileFormat.from_ext_any(e) for e in ext],  # type: ignore
            use_cache=not no_cache,
        )
        if subprocess:
            output = generator.generate_subprocess(asset, export_kwargs=export_kwargs)
        elif multiprocessing:
            output = generator.generate_multiprocessing(
                asset, export_kwargs=export_kwargs
            )
        else:
            output = generator.generate(asset, export_kwargs=export_kwargs)

        TRUNCATE_AT = 8
        TRUNCATE_PRINT_N_FIRST = 3
        print_full_output = len(output) <= TRUNCATE_AT
        loggable_output = []
        for i, (filepath, metadata) in enumerate(output):
            if (
                print_full_output
                or i < TRUNCATE_PRINT_N_FIRST
                or i == (len(output) - 1)
            ):
                loggable_output.append(
                    f"{filepath}{(' | ' + str(metadata) if metadata else '')}"
                )
            elif i == TRUNCATE_PRINT_N_FIRST:
                loggable_output.append(
                    f"{f'--- {len(output) - 6} more ---'.center(len(filepath.with_suffix('').as_posix()) - 1)}*"
                )
        logging.debug("\n".join(loggable_output))


### List ###
def list_assets(hash_len: int, forwarded_args: Sequence[str] = ()):
    if AssetRegistry.n_assets() == 0:
        raise ValueError("Cannot list SimForge assets because none are registered")

    if not find_spec("rich"):
        raise ImportError('The "rich" package is required to list SimForge assets')
    from rich import print
    from rich.table import Table

    table = Table(title="SimForge Asset Registry")
    table.add_column("#", justify="right", style="cyan", no_wrap=True)
    table.add_column("Type", justify="center", style="magenta", no_wrap=True)
    table.add_column("Package", justify="center", style="green", no_wrap=True)
    table.add_column("Name", justify="left", style="blue", no_wrap=True)
    table.add_column("Semantics", justify="left", style="red")
    table.add_column("Cached", justify="left", style="yellow")

    i = 0
    for asset_type, asset_classes in AssetRegistry.items():
        cache_dir_for_type = SF_CACHE_DIR.joinpath(str(asset_type))
        for j, asset_class in enumerate(asset_classes):
            i += 1
            asset_name = convert_to_snake_case(asset_class.__name__)
            pkg_name = asset_class.__module__.split(".", 1)[0]
            asset_cache_dir = cache_dir_for_type.joinpath(asset_name)
            asset_cache = {
                path.name: len(
                    [asset for asset in os.listdir(path) if not asset.endswith(".json")]
                )
                for path in (
                    (
                        asset_cache_dir.joinpath(hexdigest)
                        for hexdigest in os.listdir(asset_cache_dir)
                    )
                    if asset_cache_dir.is_dir()
                    else ()
                )
                if path.is_dir()
            }

            table.add_row(
                str(i),
                str(asset_type),
                f"[link=file://{os.path.dirname(inspect.getabsfile(importlib.import_module(pkg_name)))}]{pkg_name}[/link]",
                f"[link=vscode://file/{inspect.getabsfile(asset_class)}:{inspect.getsourcelines(asset_class)[1]}]{asset_name}[/link]",
                str(asset_class.SEMANTICS),
                (
                    ""
                    if not asset_cache
                    else f"[bold][link=file://{asset_cache_dir}]{sum(asset_cache.values())}[/link]:[/bold] "
                    + ", ".join(
                        f"[[link=file://{asset_cache_dir.joinpath(hexdigest)}]{n_assets}|{hexdigest[:hash_len]}[/link]]"
                        for hexdigest, n_assets in sorted(
                            asset_cache.items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                        if n_assets > 0
                    )
                ),
                end_section=(j + 1) == len(asset_classes),
            )

    print(table)


### Clean ###
def clean_assets(yes: bool, forwarded_args: Sequence[str] = ()):
    if not SF_CACHE_DIR.exists():
        logging.error(f"Cache directory {SF_CACHE_DIR} does not exist")
        exit(0)
    cache_size = __get_dir_size_human_readable(SF_CACHE_DIR)

    if not yes:
        logging.warning(
            f"This will remove all SimForge assets cached on your system under {SF_CACHE_DIR} ({cache_size})"
        )
        if find_spec("rich"):
            from rich.prompt import Confirm

            yes = Confirm.ask("Are you sure you want to continue?", default=False)
        else:
            yes = input("Are you sure you want to continue? [y/N] ").lower() in [
                "y",
                "yes",
            ]

    if yes:
        shutil.rmtree(SF_CACHE_DIR, ignore_errors=True)
        logging.info(f"Reclaimed {cache_size}")
    else:
        logging.info("The cache directory was left untouched")


def __get_dir_size_human_readable(start_path: Path) -> str:
    size = __get_dir_size(start_path)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"


def __get_dir_size(start_path: Path) -> int:
    total_size = 0
    for dirpath, _dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size


### REPL ###
def enter_repl(forwarded_args: Sequence[str] = ()):
    if not find_spec("ptpython"):
        raise ImportError(
            'The "ptpython" package is required to enter REPL of SimForge'
        )

    import ptpython

    import simforge  # noqa: F401
    from simforge.utils import logging  # noqa: F401

    # Enter REPL
    ptpython.repl.embed(globals(), locals(), title="SimForge")


### Docs ###
def serve_docs(forwarded_args: Sequence[str] = ()):
    import string
    import subprocess

    from simforge.utils import logging

    if not shutil.which("mdbook"):
        raise FileNotFoundError(
            'The "mdbook" tool is required to serve the docs of SimForge'
        )

    cmd = (
        "mdbook",
        "serve",
        Path(__file__).resolve().parent.parent.joinpath("docs").as_posix(),
        "--open",
        *forwarded_args,
    )
    logging.info(
        "Serving the docs of SimForge with the following command: "
        + " ".join(
            (f'"{arg}"' if any(c in string.whitespace for c in arg) else arg)
            for arg in cmd
        )
    )

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.critical("Serving the docs failed due to the exception above")
        exit(e.returncode)


### Test ###
def run_tests(forwarded_args: Sequence[str] = ()):
    import string
    import subprocess

    from simforge.utils import logging

    if not find_spec("pytest"):
        raise ImportError('The "pytest" package is required to run tests of SimForge')

    cmd = (
        sys.executable,
        "-m",
        "pytest",
        Path(__file__).resolve().parent.parent.as_posix(),
        *forwarded_args,
    )

    logging.info(
        "Running python tests of SimForge with the following command: "
        + " ".join(
            (f'"{arg}"' if any(c in string.whitespace for c in arg) else arg)
            for arg in cmd
        )
    )

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.critical("Running python tests failed due to the exception above")
        exit(e.returncode)


### Utils ###


@cache
def _get_registered_assets() -> Sequence[Type[Asset]]:
    return [
        asset
        for asset_type, assets in AssetRegistry.items()
        for asset in assets
        # Note: Material assets cannot yet be exported
        if asset_type is not AssetType.MATERIAL
    ]


### CLI ###
def parse_cli_args() -> argparse.Namespace:
    """
    Parse command-line arguments for this script.
    """

    parser = argparse.ArgumentParser(
        description="SimForge: Framework for creating diverse virtual environments through procedural generation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        argument_default=argparse.SUPPRESS,
    )
    subparsers = parser.add_subparsers(
        title="Subcommands",
        dest="subcommand",
        required=True,
    )

    ## Generate subcommand
    generate_parser = subparsers.add_parser(
        "gen",
        help="Generate assets",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        argument_default=argparse.SUPPRESS,
    )
    group = generate_parser.add_argument_group("Input")
    asset_names = [
        convert_to_snake_case(asset.__name__) for asset in _get_registered_assets()
    ]
    group.add_argument(
        dest="asset_name",
        type=str,
        help="Name of the asset to export (use 'ALL' to export all assets)",
        nargs="+" if asset_names else "*",
        choices=("ALL", *asset_names) if asset_names else None,
        default=None if asset_names else "NO_REGISTERED_ASSETS",
    )
    group = generate_parser.add_argument_group("Output")
    group.add_argument(
        "-o",
        "--outdir",
        type=str,
        help="The output directory",
        default=SF_CACHE_DIR,
    )
    group.add_argument(
        "-e",
        "--ext",
        type=str,
        nargs="*",
        help="The file extension of the exported assets",
        choices=sorted(map(str, FileFormat.all_formats())),
        default=["png", "mdl", "usdz"],
    )
    group = generate_parser.add_argument_group("Generator")
    group.add_argument(
        "-s",
        "--seed",
        type=int,
        help="The initial seed of the random number generator",
        default=0,
    )
    group.add_argument(
        "-n",
        "--num_assets",
        type=int,
        help="Number of assets to generate",
        default=1,
    )
    group = generate_parser.add_argument_group("Export")
    group.add_argument(
        "--no_cache",
        action="store_true",
        help="Skip generation if the model is already cached",
        default=False,
    )
    group.add_argument(
        "--export_kwargs",
        type=json.loads,
        help="Keyword arguments for the exporter",
        default={},
    )
    group = generate_parser.add_argument_group("Process")
    mutex_group = group.add_mutually_exclusive_group()
    mutex_group.add_argument(
        "--multiprocessing",
        action="store_true",
        help="Run the generation pipeline in a subprocess spawned with the same Python environment",
        default=False,
    )
    mutex_group.add_argument(
        "--subprocess",
        action="store_true",
        help="Run the generation pipeline in a separate subprocess with an independent Python environment",
        default=False,
    )

    ## List subcommand
    list_parser = subparsers.add_parser(
        "ls",
        help="List registered assets"
        + ("" if find_spec("rich") else ' (MISSING: "rich" Python package)'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        argument_default=argparse.SUPPRESS,
    )
    list_parser.add_argument(
        "--hash_len",
        "-l",
        type=int,
        help="Number of characters to show from the cache directory hexdigest",
        default=4,
    )

    ## Clean subcommand
    clean_parser = subparsers.add_parser(
        "clean",
        help="Clean the cache directory",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        argument_default=argparse.SUPPRESS,
    )
    clean_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt",
        default=False,
    )

    ## REPL subcommand
    _repl_parser = subparsers.add_parser(
        "repl",
        help="Enter REPL"
        + ("" if find_spec("ptpython") else ' (MISSING: "ptpython" Python package)'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    ## Docs subcommand
    _docs_parser = subparsers.add_parser(
        "docs",
        help="Serve documentation"
        + ("" if shutil.which("mdbook") else ' (MISSING: "mdbook" tool)'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    ## Test subcommand
    _test_parser = subparsers.add_parser(
        "test",
        help="Run tests"
        + ("" if find_spec("pytest") else ' (MISSING: "pytest" Python package)'),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Trigger argcomplete
    if find_spec("argcomplete"):
        import argcomplete

        argcomplete.autocomplete(parser)

    # Allow separation of arguments meant for other purposes
    if "--" in sys.argv:
        forwarded_args = sys.argv[(sys.argv.index("--") + 1) :]
        sys.argv = sys.argv[: sys.argv.index("--")]
    else:
        forwarded_args = []

    # Parse arguments
    args, unsupported_args = parser.parse_known_args()

    # Add forwarded arguments
    args.forwarded_args = forwarded_args

    # Detect any unsupported arguments
    if unsupported_args:
        import string

        raise ValueError(
            f"Unsupported CLI argument{'s' if len(unsupported_args) > 1 else ''}: "
            + ", ".join(
                f'"{arg}"' if any(c in string.whitespace for c in arg) else arg
                for arg in unsupported_args
            )
            + (
                (
                    '\nUse "--" to separate arguments meant for spawned processes: '
                    + " ".join(
                        f'"{arg}"' if any(c in string.whitespace for c in arg) else arg
                        for arg in sys.argv
                        if arg not in unsupported_args and arg != "--"
                    )
                    + " -- "
                    + " ".join(
                        f'"{arg}"' if any(c in string.whitespace for c in arg) else arg
                        for arg in unsupported_args
                    )
                )
                if args.subcommand in ("docs", "test")
                else ""
            )
        )

    return args


if __name__ == "__main__":
    main()
