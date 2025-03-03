from functools import cached_property
from itertools import chain
from typing import Any, Mapping

from pydantic import BaseModel, Field, InstanceOf, computed_field

from simforge.generators.blender.nodes.nodes import BlNodes
from simforge.utils import canonicalize_str

INPUT_BLOCKLIST = {"nodes", "_inputs"}


class BlNodesManager(BaseModel, defer_build=True):
    nodes: InstanceOf[BlNodes] = Field(frozen=True)

    @cached_property
    def is_randomizable(self) -> bool:
        return self.nodes.is_randomizable

    @computed_field(alias="inputs")
    @property
    def _inputs(self) -> Mapping[str, Any]:
        return {
            k: getattr(self, k)
            for k in chain(
                self.__class__.model_fields.keys(), self.model_computed_fields.keys()
            )
            if k not in INPUT_BLOCKLIST
        }

    @property
    def inputs(self) -> Mapping[str, Any]:
        inputs = {canonicalize_str(key): value for key, value in self._inputs.items()}
        for key in inputs.keys():
            assert key in self.nodes.input_mapping.keys(), (
                f'Field "{key}" of "{self.__class__.__name__}" is not a valid input for "{self.nodes.name}" nodes with inputs: {list(self.nodes.input_mapping.keys())}'
            )
        return inputs
