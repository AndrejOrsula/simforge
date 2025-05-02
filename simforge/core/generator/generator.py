import concurrent.futures
import importlib
import importlib.metadata
import json
import multiprocessing
import multiprocessing.context
import pickle
import subprocess
import sys
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Mapping, Sequence, Tuple

from pydantic import (
    BaseModel,
    Field,
    InstanceOf,
    NonNegativeInt,
    PositiveInt,
    StrictBool,
    computed_field,
)

import simforge
from simforge._typing import ExporterConfig, FileFormatConfig
from simforge.core.asset import (
    Articulation,
    Asset,
    AssetType,
    Geometry,
    Image,
    Material,
    Model,
)
from simforge.core.baker import Baker
from simforge.core.exporter import Exporter, FileFormat, ModelExporter
from simforge.utils import SF_CACHE_DIR, logging, md5_hexdigest_from_pydantic


class Generator(BaseModel):
    EXPORTERS: ClassVar[ExporterConfig]
    BAKER: ClassVar[InstanceOf[Baker]]
    SUBPROC_PYTHON_EXPR: ClassVar[Sequence[str]] = [sys.executable, "-c"]
    SUBPROC_INSTALL_SF_EXTRAS: ClassVar[str] = ",".join(("assets", "tracing"))
    __IS_SUBPROC_SF_ENSURED: ClassVar[bool] = False

    outdir: Path = SF_CACHE_DIR
    num_assets: PositiveInt = 1
    seed: NonNegativeInt = 0
    file_format: FileFormatConfig = Field(default=None, frozen=True)
    use_cache: StrictBool = False
    cfg_basename: str | None = "cfg"

    @computed_field
    @cached_property
    def exporters(self) -> Mapping[AssetType, Exporter]:
        if isinstance(self.EXPORTERS, Exporter):
            exporters = {
                asset_type: self.EXPORTERS
                for asset_type in self.EXPORTERS.SUPPORTED_ASSETS
            }
        elif isinstance(self.EXPORTERS, Sequence):
            exporters = {
                asset_type: exporter
                for exporter in self.EXPORTERS
                for asset_type in exporter.SUPPORTED_ASSETS
            }
        elif isinstance(self.EXPORTERS, Mapping):
            exporters = self.EXPORTERS
        else:
            raise TypeError(
                f'Unsupported type "{type(self.EXPORTERS)}" used for exporters: {self.EXPORTERS}'
            )

        # Override the file formats
        if isinstance(self.file_format, FileFormat):
            for exporter in exporters.values():
                if isinstance(exporter.file_format, type(self.file_format)):
                    exporter.file_format = self.file_format
        elif isinstance(self.file_format, Sequence):
            for file_format in self.file_format:
                for exporter in exporters.values():
                    if isinstance(exporter.file_format, type(file_format)):
                        exporter.file_format = file_format

        return exporters

    @cached_property
    def model_exporter_supports_material(self) -> bool:
        return all(
            exporter.supports_material
            for exporter in self.exporters.values()
            if isinstance(exporter, ModelExporter)
        )

    def __new__(cls, *args, **kwargs):
        if cls == Generator:
            raise TypeError(f"Cannot instantiate abstract class {cls.__name__}")
        return super().__new__(cls)

    def preprocess_asset(self, asset: Asset):
        if not self.BAKER.enabled and isinstance(asset, Model):
            asset.texture_resolution = 0

    def generate(
        self, asset: Asset, export_kwargs: Mapping[str, Any] = {}, **kwargs
    ) -> Sequence[Tuple[Path, Mapping[str, Any]]]:
        # Preprocess the asset
        self.preprocess_asset(asset)

        logging.info(
            f'Requested {self.num_assets} "{asset.name()}" asset{"s" if self.num_assets > 1 else ""} at {self.__asset_filepath_base(asset)}'
        )

        # Map asset type to callables
        match asset.asset_type:
            case AssetType.ARTICULATION:
                fn_setup = self._setup_articulation
                fn_generate = self._generate_articulation
                fn_export = self._export_articulation
                fn_cleanup = self._cleanup_articulation
            case AssetType.GEOMETRY:
                fn_setup = self._setup_geometry
                fn_generate = self._generate_geometry
                fn_export = self._export_geometry
                fn_cleanup = self._cleanup_geometry
            case AssetType.IMAGE:
                fn_setup = self._setup_image
                fn_generate = self._generate_image
                fn_export = self._export_image
                fn_cleanup = self._cleanup_image
            case AssetType.MATERIAL:
                fn_setup = self._setup_material
                fn_generate = self._generate_material
                fn_export = self._export_material
                fn_cleanup = self._cleanup_material
            case AssetType.MODEL:
                if self.BAKER.enabled:
                    self.BAKER.setup()
                fn_setup = self._setup_model
                fn_generate = self._generate_model
                fn_export = self._export_model
                fn_cleanup = self._cleanup_model

        # Write a configuration file
        if self.cfg_basename:
            cfg_filepath = (
                self.__asset_filepath_base(asset)
                .joinpath(self.cfg_basename)
                .with_suffix(".json")
            )
            if not cfg_filepath.exists():
                cfg_filepath.parent.mkdir(parents=True, exist_ok=True)
                cfg_filepath.write_text(asset.model_dump_json())

        # Setup
        setup_kwargs = fn_setup(
            asset=asset,  # type: ignore
            **kwargs,
        )

        # Check if multiple variants should be generated
        original_seed_range = None
        if not asset.is_randomizable and (self.num_assets != 1 or self.seed != 0):
            if cached_res := self.__check_cache(asset, 0):
                logging.info(
                    f'Cached non-randomizable "{asset.name()}" asset from {self.__asset_filepath_base(asset)}'
                )
                return [cached_res]
            logging.warning(
                f'Non-randomizable asset "{asset.name()}" will be generated only once with the seed of 0'
            )
            original_seed_range = (self.seed, self.num_assets)
            self.seed = 0
            self.num_assets = 1

        # Iterate over all exported seeds
        output = []
        n_cached = 0
        for i, seed in enumerate(range(self.seed, self.seed + self.num_assets)):
            # Check the cache
            if self.use_cache and (cached_res := self.__check_cache(asset, seed)):
                filepath, metadata = cached_res
                output.append((filepath, metadata))
                logging.debug(f"Skipping generation of a cached asset: {filepath.name}")
                n_cached += 1
                continue

            # Generate
            generate_kwargs = fn_generate(
                asset=asset,  # type: ignore
                seed=seed,
                **setup_kwargs,
            )

            # Export
            filepath, metadata = fn_export(
                asset=asset,  # type: ignore
                seed=seed,
                export_kwargs=export_kwargs,
                **generate_kwargs,
            )

            # Cache metadata
            metadata_filepath = self.__metadata_filepath(filepath)
            if metadata:
                metadata_filepath.write_text(
                    json.dumps(metadata, separators=(",", ":"))
                )
            elif metadata_filepath.exists():
                metadata_filepath.unlink()

            # Append the results to the output
            output.append((filepath, metadata))
            logging.info(
                f"Generated asset ({str(i + 1).rjust(self.__num_assets_width)}/{self.num_assets}): {filepath.name}"
            )

        # Clean-up
        fn_cleanup(
            asset=asset,  # type: ignore
        )

        # Revert any potential config changes
        if original_seed_range := original_seed_range:
            seed, num_assets = original_seed_range
            self.seed = seed
            self.num_assets = num_assets

        match n_cached:
            case 0:
                logging.info(
                    f'Generated {self.num_assets} "{asset.name()}" asset{"s" if self.num_assets > 1 else ""} at {self.__asset_filepath_base(asset)}'
                )
            case _all if n_cached == self.num_assets:
                logging.info(
                    f'Cached {n_cached} "{asset.name()}" asset{"s" if n_cached > 1 else ""} from {self.__asset_filepath_base(asset)}'
                )
            case _:
                logging.info(
                    f'Cached {n_cached} and generated {self.num_assets - n_cached} "{asset.name()}" assets at {self.__asset_filepath_base(asset)}'
                )

        return output

    @cached_property
    def mp_context(self) -> multiprocessing.context.BaseContext:
        mp_context = multiprocessing.get_context("spawn")
        mp_context.set_executable(self.SUBPROC_PYTHON_EXPR[0])
        return mp_context

    def generate_multiprocessing(
        self, asset: Asset, export_kwargs: Mapping[str, Any] = {}, **kwargs
    ) -> Sequence[Tuple[Path, Mapping[str, Any]]]:
        with concurrent.futures.ProcessPoolExecutor(
            mp_context=self.mp_context
        ) as executor:
            return next(executor.map(self.generate, (asset,), (export_kwargs,)))

    def generate_subprocess(
        self, asset: Asset, export_kwargs: Mapping[str, Any] = {}, **kwargs
    ) -> Sequence[Tuple[Path, Mapping[str, Any]]]:
        # Preprocess the asset
        self.preprocess_asset(asset)

        # Check the cache first before running the subprocess
        if self.use_cache:
            output = []
            for seed in range(self.seed, self.seed + self.num_assets):
                if cached_res := self.__check_cache(asset, seed):
                    output.append(cached_res)
                else:
                    break
            if len(output) == self.num_assets:
                logging.info(
                    f'Cached {self.num_assets} "{asset.name()}" asset{"s" if self.num_assets > 1 else ""} from {self.__asset_filepath_base(asset)}'
                )
                return output

        # Ensure that the simforge package is installed
        self.__subprocess_ensure_sf_installed()

        # Run the subprocess
        self.__subprocess_run(self._subprocess_expr(asset, export_kwargs, **kwargs))

        # Extract the output from the cache
        output = []
        for seed in range(self.seed, self.seed + self.num_assets):
            if cached_res := self.__check_cache(asset, seed):
                output.append(cached_res)
            else:
                if cached_res := self.__check_cache(asset, 0):
                    return [cached_res]
                else:
                    raise ChildProcessError(
                        f'Subprocess failed to generate "{asset.name()}" asset for seed {seed}'
                    )
        return output

    def _subprocess_expr(
        self, asset: Asset, export_kwargs: Mapping[str, Any] = {}, **kwargs
    ) -> List[str]:
        return [
            "import pickle",
            f"(generator,asset,export_kwargs,kwargs)=pickle.loads({pickle.dumps((self, asset, export_kwargs, kwargs))})",
            "generator.generate(asset,export_kwargs,**kwargs)",
        ]

    @classmethod
    def __subprocess_ensure_sf_installed(cls):
        if cls.__IS_SUBPROC_SF_ENSURED:
            return
        cls.__IS_SUBPROC_SF_ENSURED = True

        extras = (
            f"[{cls.SUBPROC_INSTALL_SF_EXTRAS}]"
            if cls.SUBPROC_INSTALL_SF_EXTRAS
            else ""
        )
        for src_path in simforge.__path__:
            project_path = Path(src_path).parent
            if project_path.joinpath("pyproject.toml").exists():
                install_args = (
                    "-e",
                    project_path.as_posix() + extras,
                )
                break
        else:
            install_args = (
                "simforge" + extras + f"=={importlib.metadata.version('simforge')}",
            )

        expr = [
            "from importlib.util import find_spec",
            'exit(0) if find_spec("simforge") else ()',
            "from subprocess import check_call",
            "from sys import executable",
            'check_call([executable,"-m","pip","install","--no-input","--no-cache-dir","-I",'
            + ",".join(f'"{arg}"' for arg in install_args)
            + "])",
        ]

        cls.__subprocess_run(expr)

    @classmethod
    def __subprocess_run(cls, expr: List[str]):
        try:
            subprocess.run([*cls.SUBPROC_PYTHON_EXPR, ";".join(expr)], check=True)
        except subprocess.CalledProcessError as e:
            logging.critical("SimForge subprocess failed due to the exception above")
            exit(e.returncode)

    @cached_property
    def __num_assets_width(self) -> int:
        return len(str(self.num_assets))

    def __asset_filepath(
        self,
        asset: Asset,
        seed: int,
    ) -> Path:
        return (
            self.__asset_filepath_base(asset)
            .joinpath(asset.name() + str(seed))
            .with_suffix(self.exporters[asset.asset_type].file_format.ext)
        )

    def __asset_filepath_base(self, asset: Asset) -> Path:
        return (
            self.outdir.joinpath(str(asset.asset_type))
            .joinpath(asset.name())
            .joinpath(
                md5_hexdigest_from_pydantic(
                    self.BAKER, self.exporters[asset.asset_type], asset
                )
            )
        )

    def __metadata_filepath(self, asset_filepath: Path) -> Path:
        return asset_filepath.with_suffix(".json")

    def __export(
        self,
        asset: Asset,
        seed: int,
        **export_kwargs,
    ) -> Path:
        return self.exporters[asset.asset_type].export(
            self.__asset_filepath(asset, seed), **export_kwargs
        )

    def __check_cache(
        self, asset: Asset, seed: int
    ) -> Tuple[Path, Dict[str, Any]] | None:
        filepath = self.__asset_filepath(asset, seed)
        if not filepath.exists():
            return None
        metadata_filepath = self.__metadata_filepath(filepath)
        metadata = (
            json.loads(metadata_filepath.read_text())
            if metadata_filepath.exists()
            else {}
        )
        return (filepath, metadata)

    # Articulation

    def _setup_articulation(
        self,
        asset: Articulation,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_articulation(
        self,
        asset: Articulation,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_articulation(
        self,
        asset: Articulation,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_articulation(
        self,
        asset: Articulation,
    ):
        asset.cleanup()

    # Geometry

    def _setup_geometry(
        self,
        asset: Geometry,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_geometry(
        self,
        asset: Geometry,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_geometry(
        self,
        asset: Geometry,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_geometry(
        self,
        asset: Geometry,
    ):
        asset.cleanup()

    # Image

    def _setup_image(
        self,
        asset: Image,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_image(
        self,
        asset: Image,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_image(
        self,
        asset: Image,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_image(
        self,
        asset: Image,
    ):
        asset.cleanup()

    # Material

    def _setup_material(
        self,
        asset: Material,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_material(
        self,
        asset: Material,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_material(
        self,
        asset: Material,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_material(
        self,
        asset: Material,
    ):
        asset.cleanup()

    # Model

    def _setup_model(
        self,
        asset: Model,
        **kwargs,
    ) -> Dict[str, Any]:
        return kwargs

    def _generate_model(
        self,
        asset: Model,
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        raise NotImplementedError

    def _export_model(
        self,
        asset: Model,
        seed: int,
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        return self.__export(asset=asset, seed=seed, **export_kwargs), generate_kwargs

    def _cleanup_model(
        self,
        asset: Model,
    ):
        asset.cleanup()
