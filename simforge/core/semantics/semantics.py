from typing import List, Tuple

from pydantic import BaseModel

from simforge.core.semantics.semantic_class import SemanticClass
from simforge.core.semantics.semantic_tag import SemanticTag

# TODO: Implement Semantics


class Semantics(BaseModel, defer_build=True):
    tags: List[Tuple[SemanticClass, SemanticTag]] = []

    def __str__(self):
        return ", ".join([f"{tag[0]}: {tag[1]}" for tag in self.tags])
