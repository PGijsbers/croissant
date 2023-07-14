"""FileSet module."""

import dataclasses

from ml_croissant._src.structure_graph.base_node import Node


@dataclasses.dataclass(frozen=True, repr=False)
class FileSet(Node):
    """Nodes to describe a dataset FileSet (distribution)."""

    contained_in: tuple[str, ...] = ()
    description: str | None = None
    encoding_format: str = ""
    includes: str = ""
    name: str = ""

    def check(self):
        self.assert_has_mandatory_properties("includes", "encoding_format", "name")
