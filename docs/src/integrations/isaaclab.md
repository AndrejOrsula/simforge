# Integration — Isaac Lab

[Isaac Lab](https://isaac-sim.github.io/IsaacLab) is a robot learning framework built on top of [Isaac Sim](https://developer.nvidia.com/isaac/sim). SimForge integrates with Isaac Lab through **`SimforgeAssetCfg`** to configure the spawning of assets within interactive scenes.

## Requirements

- [Isaac Lab 2.0](https://isaac-sim.github.io/IsaacLab/v2.0.0/source/setup/installation/index.html)

## `SimforgeAssetCfg`

The `SimforgeAssetCfg` class is a `SpawnerCfg` (`FileCfg`) subclass that streamlines the generation and spawning of SimForge assets within Isaac Lab. The primary attributes include:

- `assets`: Sequence of asset types to spawn
- `num_assets`: The number of asset variants distributed among `assets` to generate (default: `1`)
- `seed`: The initial seed used to generate the first variant of `assets` (default: `0`)
- `use_cache`: Use cached assets instead of generating new ones (default: `True`)
- `random_choice`: Randomly select variants instead of sequentially (default: `False`)

Example:

```py
from isaaclab import sim as sim_utils
from isaaclab.assets import AssetBaseCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from simforge import AssetRegistry
from simforge.integrations.isaaclab import SimforgeAssetCfg
from simforge_foundry import ExampleModel


@configclass
class ExampleSceneCfg(InteractiveSceneCfg):
    num_envs: int = 64

    asset1: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/asset1",
        spawn=SimforgeAssetCfg(
            assets=[
                AssetRegistry.get_by_name("example_geo"),
                AssetRegistry.get_by_name("example_model"),
            ],
            num_assets=64,
            collision_props=sim_utils.CollisionPropertiesCfg(),
        ),
    )
    asset2: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/asset2",
        spawn=SimforgeAssetCfg(
            assets=[ExampleModel],
            num_assets=8,
            seed=42,
            collision_props=sim_utils.CollisionPropertiesCfg(),
            rigid_props=sim_utils.RigidBodyPropertiesCfg(),
            mass_props=sim_utils.MassPropertiesCfg(),
        ),
    )
```
