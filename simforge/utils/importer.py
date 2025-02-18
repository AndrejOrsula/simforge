import importlib
import pkgutil
import sys
from importlib.util import find_spec
from os import environ
from typing import Iterable, List

from simforge.core import AssetRegistry
from simforge.utils import logging

DEFAULT_SF_MODULES = {"simforge_foundry"}


def import_simforge_asset_modules():
    if environ.get("SF_MODULES", "").lower() in ("none", "null", "false", "0"):
        logging.debug("Skipping automatic import of SimForge modules")
        return

    for module in DEFAULT_SF_MODULES.union(
        module
        for module in map(str.strip, environ.get("SF_MODULES", "").split(","))
        if module
    ):
        # Keep track of the number of registered assets before importing the module
        n_assets_old = AssetRegistry.n_assets()

        # Attempt to import the module
        if find_spec(module) is None:
            logging.warning(
                f'Failed to import SimForge assets from "{module}" (module not found)'
            )
            continue
        if environ.get("SF_MODULES_RECURSIVE", "false").lower() in ("true", "1"):
            import_recursively(module)
        else:
            importlib.import_module(module)

        # Log the number of registered assets after importing the module
        n_assets_new = AssetRegistry.n_assets() - n_assets_old
        if n_assets_new > 0:
            logging.debug(
                f'Automatically imported SimForge module "{module}" ({n_assets_new} registered assets)'
            )
        else:
            logging.warning(
                f'Automatically imported SimForge module "{module}" but no new assets were registered'
            )


def import_recursively(module_name: str, ignorelist: List[str] = []):
    package = importlib.import_module(module_name)
    for _ in _import_recursively_impl(
        path=package.__path__, prefix=f"{package.__name__}.", ignorelist=ignorelist
    ):
        pass


def _import_recursively_impl(
    path: Iterable[str],
    prefix: str = "",
    ignorelist: List[str] = [],
) -> Iterable[pkgutil.ModuleInfo]:
    def seen(p, m={}):
        if p in m:
            return True
        m[p] = True

    for info in pkgutil.iter_modules(path, prefix):
        if any(module_name in info.name for module_name in ignorelist):
            continue

        yield info

        if info.ispkg:
            try:
                __import__(info.name)
            except Exception as e:
                logging.critical(f'Failed to import "{info.name}"')
                raise e
            else:
                paths = getattr(sys.modules[info.name], "__path__", None) or []
                paths = [path for path in paths if not seen(path)]
                yield from _import_recursively_impl(paths, f"{info.name}.", ignorelist)
