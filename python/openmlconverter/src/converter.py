"""Converting OpenML Datset into a DCF (Croissant) representation.

Typical usage:
  dcf = converter.convert(dataset_json, features_json)
"""

import datetime
import re
from functools import partial
from typing import Callable

import dateutil.parser
import langcodes


REQUIRED_FIELDS = ("name", "description")


def convert(openml_dataset: dict, openml_features: list[dict]) -> dict:
    """
    Convert an openml dataset into a DCF (Croissant) representation.

    Args:
        openml_dataset: A dictionary containing the dataset according to OpenML
        openml_features: A dictionary containing the features of the dataset according to OpenML

    Returns
        a dictionary with the DCF representation of the dataset.
    """
    _ds = partial(_get_field, json_dict=openml_dataset)  # get field from openml_dataset

    missing_fields = [field for field in REQUIRED_FIELDS if _ds(field=field) is None]
    if any(missing_fields):
        raise ValueError(f"Required fields missing: {' '.join(missing_fields)}.")

    # For now, we only add .arff files, not the .pq file, because we do not have a checksum for .pq
    distributions = [
        _file_object(name=_ds(field="name"), url=_ds(field="url"), md5=_ds(field="md5_checksum"))
    ]
    distribution_source = _sanitize_name_string(distributions[0]["name"])
    croissant = {
        "@context": {
            "@vocab": "https://schema.org/",
            "sc": "https://schema.org/",
            "ml": "http://mlcommons.org/schema/",
            "recordSet": "ml:RecordSet",
            "field": "ml:Field",
        },
        "@type": "sc:Dataset",
        "@language": "en",
        "name": _ds(field="name"),
        "description": _ds(field="description"),
        "version": _ds(field="version"),
        "creator": _ds(
            field="creator",
            transform=lambda v: [_person(p) for p in v] if isinstance(v, list) else _person(v),
        ),
        "contributor": _ds(field="contributor", transform=_person),
        "dateCreated": _ds(field="upload_date", transform=dateutil.parser.parse),
        "dateModified": _ds(field="processing_date", transform=dateutil.parser.parse),
        "datePublished": _ds(field="collection_date", transform=_lenient_date_parser),
        "inLanguage": _ds(field="language", transform=lambda v: langcodes.find(v).language),
        "isAccessibleForFree": True,
        "license": _ds(field="licence"),
        "creativeWorkStatus": _ds(field="status"),
        "keywords": _ds(field="tag"),
        "citation": _ds(field="citation"),
        "sameAs": _ds(field="original_data_url"),
        "url": f"https://www.openml.org/search?type=data&id={_ds(field='id')}",
        "distribution": distributions,
        "recordSet": [
            {
                "name": _ds(field="name", transform=_sanitize_name_string) + "_records",
                "@type": "ml:RecordSet",
                "source": f"#{{{distribution_source}}}",
                "key": _row_identifier(openml_features, distribution_source),
                "field": [
                    {
                        "name": _sanitize_name_string(feat["name"]),
                        "@type": "ml:Field",
                        "dataType": _datatype(feat["data_type"], feat.get("nominal_value", None)),
                        "source": f"#{{{distribution_source}/{feat['name']}"
                        # TODO: handling special characters such as '/' in column names
                        "}",
                    }
                    for feat in openml_features
                ],
            }
        ],
    }
    _remove_empty_values(croissant)
    for recordSet in croissant["recordSet"]:
        _remove_empty_values(recordSet)
    return croissant


def _get_field(json_dict: dict, field: str, transform: Callable | None = None):
    """
    Get a field from a dictionary optionally perform the transformation.

    This is a convenience function. If field does not exist, throw an error if the field is
    required, otherwise return None.

    Args:
        json_dict: Any dictionary.
        field: A string containing the field name
        transform: A function to be applied to the resulting value. If None, no transformation
          will be applied.

    Returns:
        The value of the field, whereby the transformation (if any) is applied, or None if the
        field is not present and not required.

    Raises:
        ValueError: Unknown date/datetime formatL: [format].
        ValueError: Unrecognized file extension in url: [url].
        ValueError: Unrecognized datatype: [openml_datatype].
    """
    if field not in json_dict:
        return None
    val = json_dict[field]
    if transform is not None:
        return transform(val)
    return val


def _sanitize_name_string(name: str) -> str:
    """Replace special characters with underscores, and transform to lower case.

    Args:
        name: a name of a json-ld object.

    Returns:
        a sanitized version of the name
    """
    return re.sub("[^A-Za-z0-9]", "_", name).lower()


def _person(name: str) -> dict | None:
    """
    A dictionary with json-ld fields for a https://schema.org/Person

    Args:
        name: The name of the person

    Returns:
        A dictionary with json-ld fields for a schema.org Person, or None if the name is not
        present.
    """
    if name is None or name == "":
        return None
    return {"@context": "https://schema.org", "@type": "sc:Person", "name": name}


def _file_object(name: str, url: str, md5: str) -> dict | None:
    """
    A dictionary with json-ld fields for a FileObject.

    The FileObject is defined in the MLCommons DCF (Croissant) schema and based on
    https://schema.org/CreativeWork.

    Args:
        name: The name of the FileObject
        url: The url of the FileObject
        md5: The md5 checksum of the FileObject

    Returns:
        A dictionary with json-ld fields for a FileObject, or None if the URL is None.

    Raises:
        ValueError: Unrecognized file extension in url: [url].
    """
    if url is None:
        return None

    if url.endswith(".arff"):
        type_ = "arff"
        mimetype = "text/plain"  # No official arff mimetype exists
    elif url.endswith(".pq"):
        type_ = "parquet"
        mimetype = "application/vnd.apache.parquet"  # Not an official mimetype yet
        # see https://issues.apache.org/jira/browse/PARQUET-1889
    else:
        raise ValueError(f"Unrecognized file extension in url: {url}")
    return {
        "name": f"{name}_{type_}",
        "@type": "sc:FileObject",
        "contentUrl": url,
        "encodingFormat": mimetype,
        "md5": md5
        # TODO: add sameAs (other distribution)?
    }


def _datatype(openml_datatype: str, nominal_value: list[str] | None) -> str:
    """
    Convert the datatype according to OpenML to a schema.org datatype.

    In DCF schema.org datatypes are used on default.

    Args:
        openml_datatype: The datatype according to OpenML
        nominal_value: An optional list of strings with the possible values.

    Returns:
        The schema.org datatype.

    Raises:
        ValueError: Unknown datatype: [openml_datatype].
    """
    if nominal_value is not None:
        if set(nominal_value) == {"TRUE", "FALSE"} or set(nominal_value) == {"0", "1"}:
            return "Boolean"
    d_type = {
        "numeric": "Number",
        "string": "Text",
        "nominal": "Text",  # TODO: where to add the possible values?
    }.get(openml_datatype, None)
    if d_type is None:
        raise ValueError(f"Unknown datatype: {openml_datatype}.")
    return d_type


def _row_identifier(
    openml_features: list[dict[str, any]], distribution_source: str
) -> list[str] | str | None:
    """
    Determine the feature names that uniquely identify a row.

    Example features:
    [
        {
            "index": "1",
            "name": "survived",
            "data_type": "nominal",
            "nominal_value": [
                "0",
                "1"
            ],
            "is_target": "true",
            "is_ignore": "false",
            "is_row_identifier": "false",
            "number_of_missing_values": "0"
        }, [...]
    ]


    Args:
        openml_features: A list of dictionaries containing the OpenML description of features.
        distribution_source: The name of the distribution.

    Returns:
        A list of feature names, a single feature name, or None.
    """
    row_identifiers = [
        f"#{{{_sanitize_name_string(f['name'])}}}"
        for f in openml_features
        if f["is_row_identifier"] == "true"
    ]
    if len(row_identifiers) > 1:
        return row_identifiers
    elif len(row_identifiers) == 1:
        return row_identifiers[0]
    return None


def _lenient_date_parser(value: str) -> datetime.date | datetime.datetime:
    """
    Try to parse the value as a date or datetime.

    This can handle any string that dateutil.parser can parse, such as "2000-01-01T00:00:00",
    but also only a year, such as "2000"

    Args:
        value: a date-like string

    Returns:
        A datetime if the date and time are specified, or a date if the time is not specified.

    Raises:
        ValueError: Unknown date/datetime format: [format]
    """
    try:
        dateutil.parser.parse(value)
    except dateutil.parser.ParserError:
        pass
    if len(value) == 4 and (value.startswith("19") or value.startswith("20")):
        year = int(value)
        return datetime.date(year, 1, 1)
    raise ValueError(f"Unknown date/datetime format: {value}")


def _remove_empty_values(dct_: dict):
    """
    In-line function to recursively remove fields that have value None or an empty list/dict.

    Args:
        dct_: a dictionary
    """
    for key, value in list(dct_.items()):
        if isinstance(value, dict):
            _remove_empty_values(value)
        elif value is None:
            del dct_[key]
        elif isinstance(value, list) and len(value) == 0:
            del dct_[key]
