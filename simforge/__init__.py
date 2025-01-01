from simforge.utils.importer import import_simforge_asset_modules
from simforge.utils.tracing import with_logfire, with_rich

## Enable rich traceback
with_rich()

## Enable logfire instrumentation
with_logfire()


## Re-export common modules
from simforge._typing import TexResConfig  # noqa: E402
from simforge.core import (  # noqa: E402
    Articulation,
    Asset,
    AssetRegistry,
    AssetType,
    Baker,
    BakeType,
    Exporter,
    FileFormat,
    FileFormatConfig,
    Generator,
    Geometry,
    Image,
    ImageExporter,
    ImageFileFormat,
    Material,
    MaterialExporter,
    MaterialFileFormat,
    Model,
    ModelExporter,
    ModelFileFormat,
    OpType,
    ProcOp,
    Renderer,
    SemanticClass,
    Semantics,
    SemanticTag,
)
from simforge.generators import (  # noqa: E402
    BlArticulation,
    BlGeometry,
    BlGeometryModifier,
    BlGeometryNodesModifier,
    BlImage,
    BlMaterial,
    BlModel,
    BlNodes,
    BlNodesFromPython,
    BlShader,
)

__all__ = (
    "Articulation",
    "Asset",
    "AssetRegistry",
    "AssetType",
    "Baker",
    "BakeType",
    "BlArticulation",
    "BlGeometry",
    "BlGeometryModifier",
    "BlGeometryNodesModifier",
    "BlImage",
    "BlMaterial",
    "BlModel",
    "BlNodes",
    "BlNodesFromPython",
    "BlShader",
    "Exporter",
    "FileFormat",
    "FileFormatConfig",
    "Generator",
    "Geometry",
    "Image",
    "ImageExporter",
    "ImageFileFormat",
    "Material",
    "MaterialExporter",
    "MaterialFileFormat",
    "Model",
    "ModelExporter",
    "ModelFileFormat",
    "OpType",
    "ProcOp",
    "Renderer",
    "SemanticClass",
    "Semantics",
    "SemanticTag",
    "TexResConfig",
)


## Import modules with SimForge assets
import_simforge_asset_modules()
