import tempfile
from typing import Any, Mapping, Type

import pytest

from simforge import Asset, ModelFileFormat
from simforge.__main__ import _get_registered_assets, generate_assets
from simforge.generators.blender.version import verify_bpy_version
from simforge.utils import convert_to_snake_case

SEED: int = 42
NUM_ASSETS: int = 2
NO_CACHE: bool = True
EXPORT_KWARGS: Mapping[str, Any] = {}
SUBPROCESS: bool = not verify_bpy_version()
MULTIPROCESSING: bool = False

asset_types = _get_registered_assets()


@pytest.mark.parametrize("ext", map(str, (ModelFileFormat.USDZ,)))
@pytest.mark.parametrize("asset_type", asset_types)
def test_gen_all_assets(asset_type: Type[Asset], ext: str):
    with tempfile.TemporaryDirectory(prefix="simforge_") as tmpdir:
        generate_assets(
            asset_name=(convert_to_snake_case(asset_type.__name__),),
            outdir=tmpdir,
            ext=(ext,),
            seed=SEED,
            num_assets=NUM_ASSETS,
            no_cache=NO_CACHE,
            export_kwargs=EXPORT_KWARGS,
            subprocess=SUBPROCESS,
            multiprocessing=MULTIPROCESSING,
        )


@pytest.mark.parametrize("ext", map(str, ModelFileFormat))
@pytest.mark.parametrize("asset_type", (asset_types[0],) if asset_types else ())
def test_gen_all_exts(asset_type: Type[Asset], ext: str):
    with tempfile.TemporaryDirectory(prefix="simforge_") as tmpdir:
        generate_assets(
            asset_name=(convert_to_snake_case(asset_type.__name__),),
            outdir=tmpdir,
            ext=(ext,),
            seed=SEED,
            num_assets=NUM_ASSETS,
            no_cache=NO_CACHE,
            export_kwargs=EXPORT_KWARGS,
            subprocess=SUBPROCESS,
            multiprocessing=MULTIPROCESSING,
        )
