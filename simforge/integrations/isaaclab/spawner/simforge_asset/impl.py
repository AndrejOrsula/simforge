from typing import TYPE_CHECKING, Tuple

from omni.isaac.lab.sim.spawners.wrappers import MultiAssetSpawnerCfg, spawn_multi_asset
from pxr import Usd

from simforge import ModelFileFormat
from simforge.integrations.isaaclab.spawner.from_files import UsdFileCfg
from simforge.utils import logging

if TYPE_CHECKING:
    from simforge.integrations.isaaclab.spawner.simforge_asset.cfg import (
        SimforgeAssetCfg,
    )

IGNORED_SPAWN_ATTRIBUTES = (
    "func",
    "assets",
    "export_kwargs",
    "num_assets",
    "seed",
    "use_cache",
    "random_choice",
)


def spawn_simforge_assets(
    prim_path: str,
    cfg: "SimforgeAssetCfg",
    translation: Tuple[float, float, float] | None = None,
    orientation: Tuple[float, float, float, float] | None = None,
) -> Usd.Prim:
    # Generate the assets
    logging.debug(f'Spawning SimForge assets for "{prim_path}"')
    (num_assets_base, num_assets_rem) = (
        cfg.num_assets // len(cfg.assets),
        cfg.num_assets % len(cfg.assets),
    )
    generator_output = [
        asset.generator_type(
            num_assets=num_assets_base + int(i < num_assets_rem),
            seed=cfg.seed,
            file_format=ModelFileFormat.USDZ,
            use_cache=cfg.use_cache,
        ).generate_subprocess(asset, export_kwargs=cfg.export_kwargs)
        for i, asset in enumerate(cfg.assets)
    ]

    # Create a prototype configuration
    proto_cfg = UsdFileCfg(
        **{
            attr_name: attr_value
            for attr_name, attr_value in cfg.__dict__.items()
            if attr_name not in IGNORED_SPAWN_ATTRIBUTES
        },
    )

    # Additional non-standard properties
    proto_cfg.mesh_collision_props = cfg.mesh_collision_props  # type: ignore

    # Create and spawn multi-asset configuration
    return spawn_multi_asset(
        prim_path=prim_path,
        cfg=MultiAssetSpawnerCfg(
            assets_cfg=[
                proto_cfg.replace(  # type: ignore
                    usd_path=filepath.as_posix(),
                    # semantic_tags=...,  # TODO: Extract semantics from assets
                )
                for output in generator_output
                for filepath, _ in output  # TODO: Extract metadata from assets
            ],
            random_choice=cfg.random_choice,
        ),
        translation=translation,
        orientation=orientation,
    )
