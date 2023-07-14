"""datasets_test module."""

import json

from etils import epath
from ml_croissant._src import datasets
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.tests.records import record_to_python
import pytest


# End-to-end tests on real data. The data is in `tests/end-to-end/*.json`.
@pytest.mark.parametrize(
    ["filename", "error"],
    [
        # Metadata.
        [
            "metadata_missing_property_name.json",
            'Property "https://schema.org/name" is mandatory, but does not exist.',
        ],
        [
            "metadata_bad_type.json",
            "No metadata is defined in the dataset",
        ],
        # Distribution.
        [
            "distribution_missing_property_content_url.json",
            (
                'Property "https://schema.org/contentUrl" is mandatory, but does not '
                "exist."
            ),
        ],
        [
            "distribution_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "distribution_bad_contained_in.json",
            (
                'There is a reference to node named "THISDOESNOTEXIST" in node'
                ' "a-csv-table", but this node doesn\'t exist.'
            ),
        ],
        [
            # When the name misses, the context should still appear without the name.
            "distribution_missing_name.json",
            (
                r"\[dataset\(mydataset\) \> distribution\(\)\] Property "
                r'"https://schema.org/name" is mandatory'
            ),
        ],
        # Record set.
        [
            "recordset_missing_property_name.json",
            'Property "https://schema.org/name" is mandatory, but does not exist.',
        ],
        [
            "recordset_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "recordset_missing_context_for_datatype.json",
            "The field does not specify any http://mlcommons.org/schema/dataType",
        ],
        # ML field.
        [
            "mlfield_missing_property_name.json",
            'Property "https://schema.org/name" is mandatory, but does not exist.',
        ],
        [
            "mlfield_bad_type.json",
            'Node should have an attribute `"@type" in',
        ],
        [
            "mlfield_missing_source.json",
            'Node "a-record-set/first-field" is a field and has no source.',
        ],
        [
            "mlfield_bad_source.json",
            "Malformed source data: #{THISDOESNOTEXIST#field}.",
        ],
    ],
)
def test_static_analysis(filename, error):
    base_path = epath.Path(__file__).parent / "tests/graphs"
    with pytest.raises(ValidationError, match=error):
        datasets.Dataset(base_path / filename)


# IF THIS TEST FAILS OR YOU ADD A NEW DATASET:
# You can regenerate .pkl files by launching
# ```bash
# python scripts/load.py \
#   --file {{dataset_name}} \
#   --record_set {{record_set_name}} \
#   --update_output \
#   --num_records -1
# ```
@pytest.mark.parametrize(
    ["dataset_name", "record_set_name"],
    [
        ["pass-mini", "images"],
        ["simple-join", "publications_by_user"],
        ["titanic", "passengers"],
    ],
)
def test_loading(dataset_name, record_set_name):
    print(
        f"Update JSONL with: `python scripts/load.py --file {dataset_name} --record_set"
        f" {record_set_name} --update_output --num_records -1`"
    )
    dataset_folder = (
        epath.Path(__file__).parent.parent.parent.parent.parent
        / "datasets"
        / dataset_name
    )
    config = dataset_folder / "metadata.json"
    pkl_file = dataset_folder / "output.jsonl"
    with pkl_file.open("rb") as f:
        lines = f.readlines()
        expected_records = [json.loads(line) for line in lines]
    dataset = datasets.Dataset(config)
    records = dataset.records(record_set_name)
    records = iter(records)
    length = 0
    for i, record in enumerate(records):
        record = record_to_python(record)
        assert record == expected_records[i]
        length += 1
    assert len(expected_records) == length
