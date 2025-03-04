import tempfile
from pathlib import Path
from typing import Sequence, Type

import pytest

from simforge import (
    Asset,
    AssetRegistry,
    AssetType,
    FileFormatConfig,
    Model,
    ModelFileFormat,
)
from simforge.generators.blender.version import verify_bpy_version

ASSETS: Sequence[Type[Asset]] = tuple(
    asset
    for asset_type, assets in AssetRegistry.items()
    for asset in assets
    if asset_type is not AssetType.MATERIAL
)


@pytest.mark.skipif(not ASSETS, reason="No registered assets")
@pytest.mark.parametrize("asset_type", ASSETS)
def test_gen_asset(asset_type: Type[Asset]):
    _generate_asset(asset_type=asset_type)


@pytest.mark.skipif(not ASSETS, reason="No registered assets")
@pytest.mark.parametrize("num_assets", (2, 4))
def test_gen_num_assets(num_assets: int):
    _generate_asset(asset_type=ASSETS[0], num_assets=num_assets)


@pytest.mark.skipif(not ASSETS, reason="No registered assets")
@pytest.mark.parametrize("seed", (42, 1337))
def test_gen_seed(seed: int):
    _generate_asset(asset_type=ASSETS[0], seed=seed)


@pytest.mark.skipif(not ASSETS, reason="No registered assets")
@pytest.mark.parametrize("ext", map(str, ModelFileFormat))
def test_gen_ext(ext: str):
    file_format = ModelFileFormat.from_ext(ext)
    if file_format in (ModelFileFormat.GLB, ModelFileFormat.GLTF, ModelFileFormat.SDF):
        pytest.xfail("GLTF-based export returns error despite success")
    _generate_asset(asset_type=ASSETS[0], file_format=file_format)


@pytest.mark.skipif(not ASSETS, reason="No registered assets")
def test_gen_cache():
    _generate_asset(asset_type=ASSETS[0], check_use_cache=True)


def _generate_asset(
    asset_type: Type[Asset],
    seed: int = 0,
    num_assets: int = 1,
    file_format: FileFormatConfig = None,
    check_use_cache: bool = False,
    subprocess: bool = not verify_bpy_version(),
):
    with tempfile.TemporaryDirectory(prefix="simforge_") as tmpdir:
        asset_kwargs = {}
        if issubclass(asset_type, Model):
            asset_kwargs["texture_resolution"] = 16
        asset = asset_type(**asset_kwargs)
        generator = asset.generator_type(
            outdir=Path(tmpdir),
            seed=seed,
            num_assets=num_assets,
            file_format=file_format,
            use_cache=check_use_cache,
        )
        output = (
            generator.generate_subprocess(asset)
            if subprocess
            else generator.generate(asset)
        )
        assert len(output) == num_assets

        if check_use_cache:
            output = (
                generator.generate_subprocess(asset)
                if subprocess
                else generator.generate(asset)
            )
            assert len(output) == num_assets
