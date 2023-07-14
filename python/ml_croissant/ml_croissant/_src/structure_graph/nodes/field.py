"""Field module."""

import dataclasses

from ml_croissant._src.core import constants
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.record_set import RecordSet
from ml_croissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(frozen=True, repr=False)
class Field(Node):
    """Nodes to describe a dataset Field."""

    description: str | None = None
    # `field_data_type` is different than `node.data_type`. See `data_type` docstring.
    field_data_type: str | None = None
    has_sub_fields: bool | None = None
    name: str = ""
    references: Source = dataclasses.field(default_factory=Source)
    source: Source = dataclasses.field(default_factory=Source)

    def check(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")

    @property
    def data_type(self) -> str | None:
        """Recrusively retrieves the actual data type of the node.

        The data_type can be either directly on the node (`field_data_type`) or on one
        of the parent fields.
        """
        if self.field_data_type is not None:
            return self.field_data_type
        parent = next(self.graph.predecessors(self), None)
        if parent is None or not isinstance(parent, Field):
            self.add_error(
                f"The field does not specify any {constants.ML_COMMONS_DATA_TYPE},"
                " neither does any of its predecessor."
            )
            return None
        return parent.data_type

    @property
    def data(self) -> str | None:
        parent = self.parents[-1]
        if isinstance(parent, RecordSet):
            return parent.data
        return None
