"""Concatenate operation module."""

import dataclasses
import os

import pandas as pd

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.source import FileProperty


@dataclasses.dataclass(frozen=True, repr=False)
class Concatenate(Operation):
    """Concatenates several pd.DataFrames into one."""

    node: FileSet

    def __call__(self, *paths: Path) -> pd.DataFrame:
        """See class' docstring."""
        assert len(paths) > 0, "No path to concatenate."
        return pd.DataFrame(
            {
                FileProperty.filepath: [os.fspath(path.filepath) for path in paths],
                FileProperty.filename: [path.filename for path in paths],
                FileProperty.fullpath: [os.fspath(path.fullpath) for path in paths],
            }
        )
