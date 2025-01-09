# New Generators

Implementing a new [Generator](../generators/index.md) is an involved process that requires inheriting from the core SimForge classes and implementing the necessary methods. Once you know which external tool or library you want to leverage, you can start by creating a new Python module and defining the following classes:

- Generation \[required\]:

  - `ExModelExporter(ModelExporter)` - Class that exports generated model assets
  - `ExGenerator(Generator)` - The main class that handles the generation of assets

- Generation \[optional\]:

  - `ExBaker(Baker)` - Class that bakes textures for the generated assets

- Assets \[standard\]:

  - `ExGeometry(Geometry)` - Class for geometry assets
  - `ExMaterial(Material)` - Class for material assets
  - `ExModel(Model)` - Class for model assets

- Assets \[extra\]:

  - `ExImage(Image)` - Class for image assets
  - `ExArticulation(Articulation)` - Class for articulation assets

First, make sure to read the documentation of the external tool or library you want to integrate with SimForge. This will help you understand the API and any limitations or constraints that you need to consider. Then, take a look at the existing generators in the SimForge codebase to get an idea of how you could structure your generator.

Template:

```py
from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Dict, Mapping, Tuple

from simforge import (
    Articulation,
    Baker,
    BakeType,
    Generator,
    Geometry,
    Image,
    Material,
    Model,
    ModelExporter,
)
from simforge._typing import ExporterConfig


class ExModelExporter(ModelExporter):
    def export(self, filepath: Path | str, **kwargs) -> Path:
        raise NotImplementedError


class ExBaker(Baker):
    def setup(self):
        pass

    def bake(self, texture_resolution: int | Dict[BakeType, int]):
        if self.enabled:
            raise NotImplementedError

    def cleanup(self):
        pass


class ExGenerator(Generator):
    EXPORTERS: ClassVar[ExporterConfig] = ExModelExporter()
    BAKER: ClassVar[ExBaker] = ExBaker()

    def _setup_articulation(
        self,
        asset: ExArticulation,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_articulation(
        self,
        asset: ExArticulation,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_articulation(
        self,
        asset: ExArticulation,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_articulation(
        self,
        asset: ExArticulation,
    ):
        asset.cleanup()

    def _setup_geometry(
        self,
        asset: ExGeometry,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_geometry(
        self,
        asset: ExGeometry,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_geometry(
        self,
        asset: ExGeometry,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_geometry(
        self,
        asset: ExGeometry,
    ):
        asset.cleanup()

    def _setup_image(
        self,
        asset: ExImage,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_image(
        self,
        asset: ExImage,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_image(
        self,
        asset: ExImage,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_image(
        self,
        asset: ExImage,
    ):
        asset.cleanup()

    def _setup_material(
        self,
        asset: ExMaterial,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_material(
        self,
        asset: ExMaterial,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_material(
        self,
        asset: ExMaterial,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_material(
        self,
        asset: ExMaterial,
    ):
        asset.cleanup()

    def _setup_model(
        self,
        asset: ExModel,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_model(
        self,
        asset: ExModel,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_model(
        self,
        asset: ExModel,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_model(
        self,
        asset: ExModel,
    ):
        asset.cleanup()


class ExArticulation(Articulation, asset_metaclass=True, asset_generator=ExGenerator):
    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        pass


class ExGeometry(Geometry, asset_metaclass=True, asset_generator=ExGenerator):
    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        pass


class ExImage(Image, asset_metaclass=True, asset_generator=ExGenerator):
    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        pass


class ExMaterial(Material, asset_metaclass=True, asset_generator=ExGenerator):
    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        pass


class ExModel(Model, asset_metaclass=True, asset_generator=ExGenerator):
    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        pass
```

If you have any questions regarding a specific generator, feel free to [open a new issue](https://github.com/AndrejOrsula/simforge/issues/new).
