from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, ClassVar, Dict, Iterable, List, Sequence, Tuple, Type

from pydantic import BaseModel

from simforge.core.asset.asset_type import AssetType
from simforge.core.semantics import Semantics
from simforge.utils import convert_to_snake_case

if TYPE_CHECKING:
    from simforge.core.generator import Generator


class Asset(BaseModel):
    SEMANTICS: ClassVar[Semantics] = Semantics()

    @cached_property
    def name(self) -> str:
        return convert_to_snake_case(self.__class__.__name__)

    @property
    def is_randomizable(self) -> bool:
        return False

    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        pass

    def __new__(cls, *args, **kwargs):
        if cls in (
            Asset,
            *AssetRegistry.base_types.keys(),
            *AssetRegistry.meta_types.keys(),
        ):
            raise TypeError(f"Cannot instantiate abstract class {cls.__name__}")
        return super().__new__(cls)

    def __init_subclass__(
        cls,
        asset_entrypoint: AssetType | None = None,
        asset_metaclass: bool = False,
        asset_generator: Type["Generator"] | None = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        if asset_entrypoint is not None:
            assert isinstance(
                asset_entrypoint, AssetType
            ), f'Class "{cls.__name__}" is marked as an asset entrypoint, but "{asset_entrypoint}" is not a valid {AssetType}'
            assert (
                asset_entrypoint not in AssetRegistry.base_types.keys()
            ), f'Class "{cls.__name__}" is marked as "{asset_entrypoint}" asset entrypoint, but it was already marked by "{AssetRegistry.base_types[asset_entrypoint].__name__}"'
            AssetRegistry.base_types[asset_entrypoint] = cls
        elif asset_metaclass:
            AssetRegistry.meta_types[cls] = asset_generator
        else:
            for asset_type, base in AssetRegistry.base_types.items():
                if issubclass(cls, base):
                    if asset_type not in AssetRegistry.registry.keys():
                        AssetRegistry.registry[asset_type] = []
                    else:
                        assert (
                            convert_to_snake_case(cls.__name__)
                            not in (
                                convert_to_snake_case(asset.__name__)
                                for asset in AssetRegistry.registry[asset_type]
                            )
                        ), f'Cannot register multiple assets with an identical name: "{cls.__module__}:{cls.__name__}" already exists as "{next(asset for asset in AssetRegistry.registry[asset_type] if convert_to_snake_case(cls.__name__) == convert_to_snake_case(asset.__name__)).__module__}:{cls.__name__}"'
                    AssetRegistry.registry[asset_type].append(cls)

    @cached_property
    def asset_type(self) -> AssetType:
        for asset_type, base in AssetRegistry.base_types.items():
            if isinstance(self, base):
                return asset_type
        raise ValueError(f'Class "{self.__class__.__name__}" has unknown asset type')

    @cached_property
    def generator_type(self) -> Type["Generator"]:
        for meta_type, generator in AssetRegistry.meta_types.items():
            if isinstance(self, meta_type):
                if generator is None:
                    raise ValueError(
                        f'Unable to find a generator for class "{self.__class__.__name__}" because its metaclass "{meta_type.__name__}" does not have a registered generator'
                    )
                return generator
        raise ValueError(
            f'Unable to find a generator for class "{self.__class__.__name__}" because it is not a subclass of any asset metaclass'
        )

    @classmethod
    def registry(cls) -> Sequence[Type[Asset]]:
        return list(AssetRegistry.values_inner())


class AssetRegistry:
    registry: ClassVar[Dict[AssetType, List[Type[Asset]]]] = {}
    base_types: ClassVar[Dict[AssetType, Type[Asset]]] = {}
    meta_types: ClassVar[Dict[Type[Asset], Type["Generator"] | None]] = {}

    @classmethod
    def keys(cls) -> Iterable[AssetType]:
        return cls.registry.keys()

    @classmethod
    def items(cls) -> Iterable[Tuple[AssetType, Sequence[Type[Asset]]]]:
        return cls.registry.items()

    @classmethod
    def values(cls) -> Iterable[Iterable[Type[Asset]]]:
        return cls.registry.values()

    @classmethod
    def values_inner(cls) -> Iterable[Type[Asset]]:
        return (asset for assets in cls.registry.values() for asset in assets)

    @classmethod
    def n_assets(cls) -> int:
        return sum(len(assets) for assets in cls.registry.values())

    @classmethod
    def registered_modules(cls) -> Iterable[str]:
        return {
            asset.__module__ for assets in cls.registry.values() for asset in assets
        }

    @classmethod
    def registered_packages(cls) -> Iterable[str]:
        return {module.split(".", maxsplit=1)[0] for module in cls.registered_modules()}

    @classmethod
    def by_name(cls, name: str) -> Type[Asset] | None:
        for asset in cls.values_inner():
            if convert_to_snake_case(asset.__name__) == name:
                return asset
        return None
