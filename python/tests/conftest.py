# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
# pylint:disable=redefined-outer-name
"""This contains global pytest configurations.

Fixtures contained in this file will be automatically used if provided as an argument
to any pytest function.

In the case where the fixture must be used in a pytest.mark.parametrize decorator, the string representation can be used
and the built-in pytest fixture request should be used as an additional argument in the function. The fixture can then be
retrieved using `request.getfixturevalue(fixture_name)`.
"""
import os
from tempfile import TemporaryDirectory
from typing import Any, Dict, Union
from urllib.parse import urlparse

import pytest

from pyiceberg import schema
from pyiceberg.io.base import (
    FileIO,
    InputFile,
    OutputFile,
    OutputStream,
)
from pyiceberg.schema import Schema
from pyiceberg.types import (
    BinaryType,
    BooleanType,
    DoubleType,
    FloatType,
    IntegerType,
    ListType,
    LongType,
    MapType,
    NestedField,
    StringType,
    StructType,
)
from tests.catalog.test_base import InMemoryCatalog
from tests.io.test_io_base import LocalInputFile


class FooStruct:
    """An example of an object that abides by StructProtocol"""

    def __init__(self):
        self.content = {}

    def get(self, pos: int) -> Any:
        return self.content[pos]

    def set(self, pos: int, value) -> None:
        self.content[pos] = value


@pytest.fixture(scope="session")
def table_schema_simple():
    return schema.Schema(
        NestedField(field_id=1, name="foo", field_type=StringType(), required=False),
        NestedField(field_id=2, name="bar", field_type=IntegerType(), required=True),
        NestedField(field_id=3, name="baz", field_type=BooleanType(), required=False),
        schema_id=1,
        identifier_field_ids=[1],
    )


@pytest.fixture(scope="session")
def table_schema_nested():
    return schema.Schema(
        NestedField(field_id=1, name="foo", field_type=StringType(), required=False),
        NestedField(field_id=2, name="bar", field_type=IntegerType(), required=True),
        NestedField(field_id=3, name="baz", field_type=BooleanType(), required=False),
        NestedField(
            field_id=4,
            name="qux",
            field_type=ListType(element_id=5, element_type=StringType(), element_required=True),
            required=True,
        ),
        NestedField(
            field_id=6,
            name="quux",
            field_type=MapType(
                key_id=7,
                key_type=StringType(),
                value_id=8,
                value_type=MapType(key_id=9, key_type=StringType(), value_id=10, value_type=IntegerType(), value_required=True),
                value_required=True,
            ),
            required=True,
        ),
        NestedField(
            field_id=11,
            name="location",
            field_type=ListType(
                element_id=12,
                element_type=StructType(
                    NestedField(field_id=13, name="latitude", field_type=FloatType(), required=False),
                    NestedField(field_id=14, name="longitude", field_type=FloatType(), required=False),
                ),
                element_required=True,
            ),
            required=True,
        ),
        NestedField(
            field_id=15,
            name="person",
            field_type=StructType(
                NestedField(field_id=16, name="name", field_type=StringType(), required=False),
                NestedField(field_id=17, name="age", field_type=IntegerType(), required=True),
            ),
            required=False,
        ),
        schema_id=1,
        identifier_field_ids=[1],
    )


@pytest.fixture(scope="session")
def foo_struct():
    return FooStruct()


@pytest.fixture(scope="session")
def all_avro_types() -> Dict[str, Any]:
    return {
        "type": "record",
        "name": "all_avro_types",
        "fields": [
            {"name": "primitive_string", "type": "string", "field-id": 100},
            {"name": "primitive_int", "type": "int", "field-id": 200},
            {"name": "primitive_long", "type": "long", "field-id": 300},
            {"name": "primitive_float", "type": "float", "field-id": 400},
            {"name": "primitive_double", "type": "double", "field-id": 500},
            {"name": "primitive_bytes", "type": "bytes", "field-id": 600},
            {
                "type": "record",
                "name": "Person",
                "fields": [
                    {"name": "name", "type": "string", "field-id": 701},
                    {"name": "age", "type": "long", "field-id": 702},
                    {"name": "gender", "type": ["string", "null"], "field-id": 703},
                ],
                "field-id": 700,
            },
            {
                "name": "array_with_string",
                "type": {
                    "type": "array",
                    "items": "string",
                    "default": [],
                    "element-id": 801,
                },
                "field-id": 800,
            },
            {
                "name": "array_with_optional_string",
                "type": [
                    "null",
                    {
                        "type": "array",
                        "items": ["string", "null"],
                        "default": [],
                        "element-id": 901,
                    },
                ],
                "field-id": 900,
            },
            {
                "name": "array_with_optional_record",
                "type": [
                    "null",
                    {
                        "type": "array",
                        "items": [
                            "null",
                            {
                                "type": "record",
                                "name": "person",
                                "fields": [
                                    {"name": "name", "type": "string", "field-id": 1002},
                                    {"name": "age", "type": "long", "field-id": 1003},
                                    {"name": "gender", "type": ["string", "null"], "field-id": 1004},
                                ],
                            },
                        ],
                        "element-id": 1001,
                    },
                ],
                "field-id": 1000,
            },
            {
                "name": "map_with_longs",
                "type": {
                    "type": "map",
                    "values": "long",
                    "default": {},
                    "key-id": 1101,
                    "value-id": 1102,
                },
                "field-id": 1000,
            },
        ],
    }


@pytest.fixture
def catalog() -> InMemoryCatalog:
    return InMemoryCatalog("test.in.memory.catalog", {"test.key": "test.value"})


manifest_entry_records = [
    {
        "status": 1,
        "snapshot_id": 8744736658442914487,
        "data_file": {
            "file_path": "/home/iceberg/warehouse/nyc/taxis_partitioned/data/VendorID=null/00000-633-d8a4223e-dc97-45a1-86e1-adaba6e8abd7-00001.parquet",
            "file_format": "PARQUET",
            "partition": {"VendorID": None},
            "record_count": 19513,
            "file_size_in_bytes": 388872,
            "block_size_in_bytes": 67108864,
            "column_sizes": [
                {"key": 1, "value": 53},
                {"key": 2, "value": 98153},
                {"key": 3, "value": 98693},
                {"key": 4, "value": 53},
                {"key": 5, "value": 53},
                {"key": 6, "value": 53},
                {"key": 7, "value": 17425},
                {"key": 8, "value": 18528},
                {"key": 9, "value": 53},
                {"key": 10, "value": 44788},
                {"key": 11, "value": 35571},
                {"key": 12, "value": 53},
                {"key": 13, "value": 1243},
                {"key": 14, "value": 2355},
                {"key": 15, "value": 12750},
                {"key": 16, "value": 4029},
                {"key": 17, "value": 110},
                {"key": 18, "value": 47194},
                {"key": 19, "value": 2948},
            ],
            "value_counts": [
                {"key": 1, "value": 19513},
                {"key": 2, "value": 19513},
                {"key": 3, "value": 19513},
                {"key": 4, "value": 19513},
                {"key": 5, "value": 19513},
                {"key": 6, "value": 19513},
                {"key": 7, "value": 19513},
                {"key": 8, "value": 19513},
                {"key": 9, "value": 19513},
                {"key": 10, "value": 19513},
                {"key": 11, "value": 19513},
                {"key": 12, "value": 19513},
                {"key": 13, "value": 19513},
                {"key": 14, "value": 19513},
                {"key": 15, "value": 19513},
                {"key": 16, "value": 19513},
                {"key": 17, "value": 19513},
                {"key": 18, "value": 19513},
                {"key": 19, "value": 19513},
            ],
            "null_value_counts": [
                {"key": 1, "value": 19513},
                {"key": 2, "value": 0},
                {"key": 3, "value": 0},
                {"key": 4, "value": 19513},
                {"key": 5, "value": 19513},
                {"key": 6, "value": 19513},
                {"key": 7, "value": 0},
                {"key": 8, "value": 0},
                {"key": 9, "value": 19513},
                {"key": 10, "value": 0},
                {"key": 11, "value": 0},
                {"key": 12, "value": 19513},
                {"key": 13, "value": 0},
                {"key": 14, "value": 0},
                {"key": 15, "value": 0},
                {"key": 16, "value": 0},
                {"key": 17, "value": 0},
                {"key": 18, "value": 0},
                {"key": 19, "value": 0},
            ],
            "nan_value_counts": [
                {"key": 16, "value": 0},
                {"key": 17, "value": 0},
                {"key": 18, "value": 0},
                {"key": 19, "value": 0},
                {"key": 10, "value": 0},
                {"key": 11, "value": 0},
                {"key": 12, "value": 0},
                {"key": 13, "value": 0},
                {"key": 14, "value": 0},
                {"key": 15, "value": 0},
            ],
            "lower_bounds": [
                {"key": 2, "value": b"2020-04-01 00:00"},
                {"key": 3, "value": b"2020-04-01 00:12"},
                {"key": 7, "value": b"\x03\x00\x00\x00"},
                {"key": 8, "value": b"\x01\x00\x00\x00"},
                {"key": 10, "value": b"\xf6(\\\x8f\xc2\x05S\xc0"},
                {"key": 11, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 13, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 14, "value": b"\x00\x00\x00\x00\x00\x00\xe0\xbf"},
                {"key": 15, "value": b")\\\x8f\xc2\xf5(\x08\xc0"},
                {"key": 16, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 17, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 18, "value": b"\xf6(\\\x8f\xc2\xc5S\xc0"},
                {"key": 19, "value": b"\x00\x00\x00\x00\x00\x00\x04\xc0"},
            ],
            "upper_bounds": [
                {"key": 2, "value": b"2020-04-30 23:5:"},
                {"key": 3, "value": b"2020-05-01 00:41"},
                {"key": 7, "value": b"\t\x01\x00\x00"},
                {"key": 8, "value": b"\t\x01\x00\x00"},
                {"key": 10, "value": b"\xcd\xcc\xcc\xcc\xcc,_@"},
                {"key": 11, "value": b"\x1f\x85\xebQ\\\xe2\xfe@"},
                {"key": 13, "value": b"\x00\x00\x00\x00\x00\x00\x12@"},
                {"key": 14, "value": b"\x00\x00\x00\x00\x00\x00\xe0?"},
                {"key": 15, "value": b"q=\n\xd7\xa3\xf01@"},
                {"key": 16, "value": b"\x00\x00\x00\x00\x00`B@"},
                {"key": 17, "value": b"333333\xd3?"},
                {"key": 18, "value": b"\x00\x00\x00\x00\x00\x18b@"},
                {"key": 19, "value": b"\x00\x00\x00\x00\x00\x00\x04@"},
            ],
            "key_metadata": None,
            "split_offsets": [4],
            "sort_order_id": 0,
        },
    },
    {
        "status": 1,
        "snapshot_id": 8744736658442914487,
        "data_file": {
            "file_path": "/home/iceberg/warehouse/nyc/taxis_partitioned/data/VendorID=1/00000-633-d8a4223e-dc97-45a1-86e1-adaba6e8abd7-00002.parquet",
            "file_format": "PARQUET",
            "partition": {"VendorID": 1},
            "record_count": 95050,
            "file_size_in_bytes": 1265950,
            "block_size_in_bytes": 67108864,
            "column_sizes": [
                {"key": 1, "value": 318},
                {"key": 2, "value": 329806},
                {"key": 3, "value": 331632},
                {"key": 4, "value": 15343},
                {"key": 5, "value": 2351},
                {"key": 6, "value": 3389},
                {"key": 7, "value": 71269},
                {"key": 8, "value": 76429},
                {"key": 9, "value": 16383},
                {"key": 10, "value": 86992},
                {"key": 11, "value": 89608},
                {"key": 12, "value": 265},
                {"key": 13, "value": 19377},
                {"key": 14, "value": 1692},
                {"key": 15, "value": 76162},
                {"key": 16, "value": 4354},
                {"key": 17, "value": 759},
                {"key": 18, "value": 120650},
                {"key": 19, "value": 11804},
            ],
            "value_counts": [
                {"key": 1, "value": 95050},
                {"key": 2, "value": 95050},
                {"key": 3, "value": 95050},
                {"key": 4, "value": 95050},
                {"key": 5, "value": 95050},
                {"key": 6, "value": 95050},
                {"key": 7, "value": 95050},
                {"key": 8, "value": 95050},
                {"key": 9, "value": 95050},
                {"key": 10, "value": 95050},
                {"key": 11, "value": 95050},
                {"key": 12, "value": 95050},
                {"key": 13, "value": 95050},
                {"key": 14, "value": 95050},
                {"key": 15, "value": 95050},
                {"key": 16, "value": 95050},
                {"key": 17, "value": 95050},
                {"key": 18, "value": 95050},
                {"key": 19, "value": 95050},
            ],
            "null_value_counts": [
                {"key": 1, "value": 0},
                {"key": 2, "value": 0},
                {"key": 3, "value": 0},
                {"key": 4, "value": 0},
                {"key": 5, "value": 0},
                {"key": 6, "value": 0},
                {"key": 7, "value": 0},
                {"key": 8, "value": 0},
                {"key": 9, "value": 0},
                {"key": 10, "value": 0},
                {"key": 11, "value": 0},
                {"key": 12, "value": 95050},
                {"key": 13, "value": 0},
                {"key": 14, "value": 0},
                {"key": 15, "value": 0},
                {"key": 16, "value": 0},
                {"key": 17, "value": 0},
                {"key": 18, "value": 0},
                {"key": 19, "value": 0},
            ],
            "nan_value_counts": [
                {"key": 16, "value": 0},
                {"key": 17, "value": 0},
                {"key": 18, "value": 0},
                {"key": 19, "value": 0},
                {"key": 10, "value": 0},
                {"key": 11, "value": 0},
                {"key": 12, "value": 0},
                {"key": 13, "value": 0},
                {"key": 14, "value": 0},
                {"key": 15, "value": 0},
            ],
            "lower_bounds": [
                {"key": 1, "value": b"\x01\x00\x00\x00"},
                {"key": 2, "value": b"2020-04-01 00:00"},
                {"key": 3, "value": b"2020-04-01 00:03"},
                {"key": 4, "value": b"\x00\x00\x00\x00"},
                {"key": 5, "value": b"\x01\x00\x00\x00"},
                {"key": 6, "value": b"N"},
                {"key": 7, "value": b"\x01\x00\x00\x00"},
                {"key": 8, "value": b"\x01\x00\x00\x00"},
                {"key": 9, "value": b"\x01\x00\x00\x00"},
                {"key": 10, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 11, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 13, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 14, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 15, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 16, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 17, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 18, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                {"key": 19, "value": b"\x00\x00\x00\x00\x00\x00\x00\x00"},
            ],
            "upper_bounds": [
                {"key": 1, "value": b"\x01\x00\x00\x00"},
                {"key": 2, "value": b"2020-04-30 23:5:"},
                {"key": 3, "value": b"2020-05-01 00:1:"},
                {"key": 4, "value": b"\x06\x00\x00\x00"},
                {"key": 5, "value": b"c\x00\x00\x00"},
                {"key": 6, "value": b"Y"},
                {"key": 7, "value": b"\t\x01\x00\x00"},
                {"key": 8, "value": b"\t\x01\x00\x00"},
                {"key": 9, "value": b"\x04\x00\x00\x00"},
                {"key": 10, "value": b"\\\x8f\xc2\xf5(8\x8c@"},
                {"key": 11, "value": b"\xcd\xcc\xcc\xcc\xcc,f@"},
                {"key": 13, "value": b"\x00\x00\x00\x00\x00\x00\x1c@"},
                {"key": 14, "value": b"\x9a\x99\x99\x99\x99\x99\xf1?"},
                {"key": 15, "value": b"\x00\x00\x00\x00\x00\x00Y@"},
                {"key": 16, "value": b"\x00\x00\x00\x00\x00\xb0X@"},
                {"key": 17, "value": b"333333\xd3?"},
                {"key": 18, "value": b"\xc3\xf5(\\\x8f:\x8c@"},
                {"key": 19, "value": b"\x00\x00\x00\x00\x00\x00\x04@"},
            ],
            "key_metadata": None,
            "split_offsets": [4],
            "sort_order_id": 0,
        },
    },
]

manifest_file_records = [
    {
        "manifest_path": "/home/iceberg/warehouse/nyc/taxis_partitioned/metadata/0125c686-8aa6-4502-bdcc-b6d17ca41a3b-m0.avro",
        "manifest_length": 7989,
        "partition_spec_id": 0,
        "added_snapshot_id": 9182715666859759686,
        "added_data_files_count": 3,
        "existing_data_files_count": 0,
        "deleted_data_files_count": 0,
        "partitions": [
            {"contains_null": True, "contains_nan": False, "lower_bound": b"\x01\x00\x00\x00", "upper_bound": b"\x02\x00\x00\x00"}
        ],
        "added_rows_count": 237993,
        "existing_rows_count": 0,
        "deleted_rows_count": 0,
    }
]


@pytest.fixture(scope="session")
def avro_schema_manifest_file() -> Dict[str, Any]:
    return {
        "type": "record",
        "name": "manifest_file",
        "fields": [
            {"name": "manifest_path", "type": "string", "doc": "Location URI with FS scheme", "field-id": 500},
            {"name": "manifest_length", "type": "long", "doc": "Total file size in bytes", "field-id": 501},
            {"name": "partition_spec_id", "type": "int", "doc": "Spec ID used to write", "field-id": 502},
            {
                "name": "added_snapshot_id",
                "type": ["null", "long"],
                "doc": "Snapshot ID that added the manifest",
                "default": "null",
                "field-id": 503,
            },
            {
                "name": "added_data_files_count",
                "type": ["null", "int"],
                "doc": "Added entry count",
                "default": "null",
                "field-id": 504,
            },
            {
                "name": "existing_data_files_count",
                "type": ["null", "int"],
                "doc": "Existing entry count",
                "default": "null",
                "field-id": 505,
            },
            {
                "name": "deleted_data_files_count",
                "type": ["null", "int"],
                "doc": "Deleted entry count",
                "default": "null",
                "field-id": 506,
            },
            {
                "name": "partitions",
                "type": [
                    "null",
                    {
                        "type": "array",
                        "items": {
                            "type": "record",
                            "name": "r508",
                            "fields": [
                                {
                                    "name": "contains_null",
                                    "type": "boolean",
                                    "doc": "True if any file has a null partition value",
                                    "field-id": 509,
                                },
                                {
                                    "name": "contains_nan",
                                    "type": ["null", "boolean"],
                                    "doc": "True if any file has a nan partition value",
                                    "default": "null",
                                    "field-id": 518,
                                },
                                {
                                    "name": "lower_bound",
                                    "type": ["null", "bytes"],
                                    "doc": "Partition lower bound for all files",
                                    "default": "null",
                                    "field-id": 510,
                                },
                                {
                                    "name": "upper_bound",
                                    "type": ["null", "bytes"],
                                    "doc": "Partition upper bound for all files",
                                    "default": "null",
                                    "field-id": 511,
                                },
                            ],
                        },
                        "element-id": 508,
                    },
                ],
                "doc": "Summary for each partition",
                "default": "null",
                "field-id": 507,
            },
            {"name": "added_rows_count", "type": ["null", "long"], "doc": "Added rows count", "default": "null", "field-id": 512},
            {
                "name": "existing_rows_count",
                "type": ["null", "long"],
                "doc": "Existing rows count",
                "default": "null",
                "field-id": 513,
            },
            {
                "name": "deleted_rows_count",
                "type": ["null", "long"],
                "doc": "Deleted rows count",
                "default": "null",
                "field-id": 514,
            },
        ],
    }


@pytest.fixture(scope="session")
def avro_schema_manifest_entry() -> Dict[str, Any]:
    return {
        "type": "record",
        "name": "manifest_entry",
        "fields": [
            {"name": "status", "type": "int", "field-id": 0},
            {"name": "snapshot_id", "type": ["null", "long"], "default": "null", "field-id": 1},
            {
                "name": "data_file",
                "type": {
                    "type": "record",
                    "name": "r2",
                    "fields": [
                        {"name": "file_path", "type": "string", "doc": "Location URI with FS scheme", "field-id": 100},
                        {
                            "name": "file_format",
                            "type": "string",
                            "doc": "File format name: avro, orc, or parquet",
                            "field-id": 101,
                        },
                        {
                            "name": "partition",
                            "type": {
                                "type": "record",
                                "name": "r102",
                                "fields": [{"name": "VendorID", "type": ["null", "int"], "default": "null", "field-id": 1000}],
                            },
                            "field-id": 102,
                        },
                        {"name": "record_count", "type": "long", "doc": "Number of records in the file", "field-id": 103},
                        {"name": "file_size_in_bytes", "type": "long", "doc": "Total file size in bytes", "field-id": 104},
                        {"name": "block_size_in_bytes", "type": "long", "field-id": 105},
                        {
                            "name": "column_sizes",
                            "type": [
                                "null",
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "record",
                                        "name": "k117_v118",
                                        "fields": [
                                            {"name": "key", "type": "int", "field-id": 117},
                                            {"name": "value", "type": "long", "field-id": 118},
                                        ],
                                    },
                                    "logicalType": "map",
                                },
                            ],
                            "doc": "Map of column id to total size on disk",
                            "default": "null",
                            "field-id": 108,
                        },
                        {
                            "name": "value_counts",
                            "type": [
                                "null",
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "record",
                                        "name": "k119_v120",
                                        "fields": [
                                            {"name": "key", "type": "int", "field-id": 119},
                                            {"name": "value", "type": "long", "field-id": 120},
                                        ],
                                    },
                                    "logicalType": "map",
                                },
                            ],
                            "doc": "Map of column id to total count, including null and NaN",
                            "default": "null",
                            "field-id": 109,
                        },
                        {
                            "name": "null_value_counts",
                            "type": [
                                "null",
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "record",
                                        "name": "k121_v122",
                                        "fields": [
                                            {"name": "key", "type": "int", "field-id": 121},
                                            {"name": "value", "type": "long", "field-id": 122},
                                        ],
                                    },
                                    "logicalType": "map",
                                },
                            ],
                            "doc": "Map of column id to null value count",
                            "default": "null",
                            "field-id": 110,
                        },
                        {
                            "name": "nan_value_counts",
                            "type": [
                                "null",
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "record",
                                        "name": "k138_v139",
                                        "fields": [
                                            {"name": "key", "type": "int", "field-id": 138},
                                            {"name": "value", "type": "long", "field-id": 139},
                                        ],
                                    },
                                    "logicalType": "map",
                                },
                            ],
                            "doc": "Map of column id to number of NaN values in the column",
                            "default": "null",
                            "field-id": 137,
                        },
                        {
                            "name": "lower_bounds",
                            "type": [
                                "null",
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "record",
                                        "name": "k126_v127",
                                        "fields": [
                                            {"name": "key", "type": "int", "field-id": 126},
                                            {"name": "value", "type": "bytes", "field-id": 127},
                                        ],
                                    },
                                    "logicalType": "map",
                                },
                            ],
                            "doc": "Map of column id to lower bound",
                            "default": "null",
                            "field-id": 125,
                        },
                        {
                            "name": "upper_bounds",
                            "type": [
                                "null",
                                {
                                    "type": "array",
                                    "items": {
                                        "type": "record",
                                        "name": "k129_v130",
                                        "fields": [
                                            {"name": "key", "type": "int", "field-id": 129},
                                            {"name": "value", "type": "bytes", "field-id": 130},
                                        ],
                                    },
                                    "logicalType": "map",
                                },
                            ],
                            "doc": "Map of column id to upper bound",
                            "default": "null",
                            "field-id": 128,
                        },
                        {
                            "name": "key_metadata",
                            "type": ["null", "bytes"],
                            "doc": "Encryption key metadata blob",
                            "default": "null",
                            "field-id": 131,
                        },
                        {
                            "name": "split_offsets",
                            "type": ["null", {"type": "array", "items": "long", "element-id": 133}],
                            "doc": "Splittable offsets",
                            "default": "null",
                            "field-id": 132,
                        },
                        {
                            "name": "sort_order_id",
                            "type": ["null", "int"],
                            "doc": "Sort order ID",
                            "default": "null",
                            "field-id": 140,
                        },
                    ],
                },
                "field-id": 2,
            },
        ],
    }


@pytest.fixture(scope="session")
def simple_struct():
    return StructType(
        NestedField(id=1, name="required_field", field_type=StringType(), required=True, doc="this is a doc"),
        NestedField(id=2, name="optional_field", field_type=IntegerType()),
    )


@pytest.fixture(scope="session")
def simple_list():
    return ListType(element_id=22, element=StringType(), element_required=True)


@pytest.fixture(scope="session")
def simple_map():
    return MapType(key_id=19, key_type=StringType(), value_id=25, value_type=DoubleType(), value_required=False)


class LocalOutputFile(OutputFile):
    """An OutputFile implementation for local files (for test use only)"""

    def __init__(self, location: str):
        parsed_location = urlparse(location)  # Create a ParseResult from the uri
        if parsed_location.scheme and parsed_location.scheme != "file":  # Validate that a uri is provided with a scheme of `file`
            raise ValueError("LocalOutputFile location must have a scheme of `file`")
        elif parsed_location.netloc:
            raise ValueError(f"Network location is not allowed for LocalOutputFile: {parsed_location.netloc}")

        super().__init__(location=location)
        self._path = parsed_location.path

    def __len__(self):
        return os.path.getsize(self._path)

    def exists(self):
        return os.path.exists(self._path)

    def to_input_file(self):
        return LocalInputFile(location=self.location)

    def create(self, overwrite: bool = False) -> OutputStream:
        output_file = open(self._path, "wb" if overwrite else "xb")
        if not issubclass(type(output_file), OutputStream):
            raise TypeError("Object returned from LocalOutputFile.create(...) does not match the OutputStream protocol.")
        return output_file


class LocalFileIO(FileIO):
    """A FileIO implementation for local files (for test use only)"""

    def new_input(self, location: str):
        return LocalInputFile(location=location)

    def new_output(self, location: str):
        return LocalOutputFile(location=location)

    def delete(self, location: Union[str, InputFile, OutputFile]):
        location = location.location if isinstance(location, (InputFile, OutputFile)) else location
        os.remove(location)


@pytest.fixture(scope="session", autouse=True)
def LocalFileIOFixture():
    return LocalFileIO


@pytest.fixture(scope="session")
def generated_manifest_entry_file(avro_schema_manifest_entry):
    from fastavro import parse_schema, writer

    parsed_schema = parse_schema(avro_schema_manifest_entry)

    with TemporaryDirectory() as tmpdir:
        tmp_avro_file = tmpdir + "/manifest.avro"
        with open(tmp_avro_file, "wb") as out:
            writer(out, parsed_schema, manifest_entry_records)
        yield tmp_avro_file


@pytest.fixture(scope="session")
def generated_manifest_file_file(avro_schema_manifest_file):
    from fastavro import parse_schema, writer

    parsed_schema = parse_schema(avro_schema_manifest_file)

    with TemporaryDirectory() as tmpdir:
        tmp_avro_file = tmpdir + "/manifest.avro"
        with open(tmp_avro_file, "wb") as out:
            writer(out, parsed_schema, manifest_file_records)
        yield tmp_avro_file


@pytest.fixture(scope="session")
def iceberg_manifest_entry_schema() -> Schema:
    return Schema(
        NestedField(field_id=0, name="status", field_type=IntegerType(), required=True),
        NestedField(field_id=1, name="snapshot_id", field_type=LongType(), required=False),
        NestedField(
            field_id=2,
            name="data_file",
            field_type=StructType(
                NestedField(
                    field_id=100,
                    name="file_path",
                    field_type=StringType(),
                    doc="Location URI with FS scheme",
                    required=True,
                ),
                NestedField(
                    field_id=101,
                    name="file_format",
                    field_type=StringType(),
                    doc="File format name: avro, orc, or parquet",
                    required=True,
                ),
                NestedField(
                    field_id=102,
                    name="partition",
                    field_type=StructType(
                        NestedField(
                            field_id=1000,
                            name="VendorID",
                            field_type=IntegerType(),
                            required=False,
                        ),
                    ),
                    required=True,
                ),
                NestedField(
                    field_id=103,
                    name="record_count",
                    field_type=LongType(),
                    doc="Number of records in the file",
                    required=True,
                ),
                NestedField(
                    field_id=104,
                    name="file_size_in_bytes",
                    field_type=LongType(),
                    doc="Total file size in bytes",
                    required=True,
                ),
                NestedField(
                    field_id=105,
                    name="block_size_in_bytes",
                    field_type=LongType(),
                    required=True,
                ),
                NestedField(
                    field_id=108,
                    name="column_sizes",
                    field_type=MapType(
                        key_id=117,
                        key_type=IntegerType(),
                        value_id=118,
                        value_type=LongType(),
                        value_required=True,
                    ),
                    doc="Map of column id to total size on disk",
                    required=False,
                ),
                NestedField(
                    field_id=109,
                    name="value_counts",
                    field_type=MapType(
                        key_id=119,
                        key_type=IntegerType(),
                        value_id=120,
                        value_type=LongType(),
                        value_required=True,
                    ),
                    doc="Map of column id to total count, including null and NaN",
                    required=False,
                ),
                NestedField(
                    field_id=110,
                    name="null_value_counts",
                    field_type=MapType(
                        key_id=121,
                        key_type=IntegerType(),
                        value_id=122,
                        value_type=LongType(),
                        value_required=True,
                    ),
                    doc="Map of column id to null value count",
                    required=False,
                ),
                NestedField(
                    field_id=137,
                    name="nan_value_counts",
                    field_type=MapType(
                        key_id=138,
                        key_type=IntegerType(),
                        value_id=139,
                        value_type=LongType(),
                        value_required=True,
                    ),
                    doc="Map of column id to number of NaN values in the column",
                    required=False,
                ),
                NestedField(
                    field_id=125,
                    name="lower_bounds",
                    field_type=MapType(
                        key_id=126,
                        key_type=IntegerType(),
                        value_id=127,
                        value_type=BinaryType(),
                        value_required=True,
                    ),
                    doc="Map of column id to lower bound",
                    required=False,
                ),
                NestedField(
                    field_id=128,
                    name="upper_bounds",
                    field_type=MapType(
                        key_id=129,
                        key_type=IntegerType(),
                        value_id=130,
                        value_type=BinaryType(),
                        value_required=True,
                    ),
                    doc="Map of column id to upper bound",
                    required=False,
                ),
                NestedField(
                    field_id=131,
                    name="key_metadata",
                    field_type=BinaryType(),
                    doc="Encryption key metadata blob",
                    required=False,
                ),
                NestedField(
                    field_id=132,
                    name="split_offsets",
                    field_type=ListType(
                        element_id=133,
                        element_type=LongType(),
                        element_required=True,
                    ),
                    doc="Splittable offsets",
                    required=False,
                ),
                NestedField(
                    field_id=140,
                    name="sort_order_id",
                    field_type=IntegerType(),
                    doc="Sort order ID",
                    required=False,
                ),
            ),
            required=True,
        ),
        schema_id=1,
        identifier_field_ids=[],
    )
