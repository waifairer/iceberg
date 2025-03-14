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
from copy import copy
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)
from uuid import UUID, uuid4

from pydantic import Field, root_validator

from pyiceberg.exceptions import ValidationError
from pyiceberg.schema import Schema
from pyiceberg.table.partitioning import PartitionSpec
from pyiceberg.table.refs import MAIN_BRANCH, SnapshotRef, SnapshotRefType
from pyiceberg.table.snapshots import Snapshot
from pyiceberg.table.sorting import UNSORTED_SORT_ORDER, UNSORTED_SORT_ORDER_ID, SortOrder
from pyiceberg.utils.iceberg_base_model import IcebergBaseModel

INITIAL_SEQUENCE_NUMBER = 0
INITIAL_SPEC_ID = 0
DEFAULT_SCHEMA_ID = 0


def check_schemas(values: Dict[str, Any]) -> Dict[str, Any]:
    """Validator to check if the current-schema-id is actually present in schemas"""
    current_schema_id = values["current_schema_id"]

    for schema in values["schemas"]:
        if schema.schema_id == current_schema_id:
            return values

    raise ValidationError(f"current-schema-id {current_schema_id} can't be found in the schemas")


def check_partition_specs(values: Dict[str, Any]) -> Dict[str, Any]:
    """Validator to check if the default-spec-id is present in partition-specs"""
    default_spec_id = values["default_spec_id"]

    partition_specs: List[PartitionSpec] = values["partition_specs"]
    for spec in partition_specs:
        if spec.spec_id == default_spec_id:
            return values

    raise ValidationError(f"default-spec-id {default_spec_id} can't be found")


def check_sort_orders(values: Dict[str, Any]) -> Dict[str, Any]:
    """Validator to check if the default_sort_order_id is present in sort-orders"""
    default_sort_order_id: int = values["default_sort_order_id"]

    if default_sort_order_id != UNSORTED_SORT_ORDER_ID:
        sort_orders: List[SortOrder] = values["sort_orders"]
        for sort_order in sort_orders:
            if sort_order.order_id == default_sort_order_id:
                return values

        raise ValidationError(f"default-sort-order-id {default_sort_order_id} can't be found in {sort_orders}")
    return values


class TableMetadataCommonFields(IcebergBaseModel):
    """Metadata for an Iceberg table as specified in the Apache Iceberg
    spec (https://iceberg.apache.org/spec/#iceberg-table-spec)"""

    def current_schema(self) -> Schema:
        return next(schema for schema in self.schemas if schema.schema_id == self.current_schema_id)

    @root_validator(pre=True)
    def cleanup_snapshot_id(cls, data: Dict[str, Any]):
        if data.get("current-snapshot-id") == -1:
            # We treat -1 and None the same, by cleaning this up
            # in a pre-validator, we can simplify the logic later on
            data["current-snapshot-id"] = None
        return data

    @root_validator(skip_on_failure=True)
    def construct_refs(cls, data: Dict[str, Any]):
        # This is going to be much nicer as soon as refs is an actual pydantic object
        if current_snapshot_id := data.get("current_snapshot_id"):
            data["refs"] = {MAIN_BRANCH: SnapshotRef(snapshot_id=current_snapshot_id, snapshot_ref_type=SnapshotRefType.BRANCH)}
        return data

    location: str = Field()
    """The table’s base location. This is used by writers to determine where
    to store data files, manifest files, and table metadata files."""

    table_uuid: Optional[UUID] = Field(alias="table-uuid")
    """A UUID that identifies the table, generated when the table is created.
    Implementations must throw an exception if a table’s UUID does not match
    the expected UUID after refreshing metadata."""

    last_updated_ms: int = Field(alias="last-updated-ms")
    """Timestamp in milliseconds from the unix epoch when the table
    was last updated. Each table metadata file should update this
    field just before writing."""

    last_column_id: int = Field(alias="last-column-id")
    """An integer; the highest assigned column ID for the table.
    This is used to ensure fields are always assigned an unused ID
    when evolving schemas."""

    schemas: List[Schema] = Field(default_factory=list)
    """A list of schemas, stored as objects with schema-id."""

    current_schema_id: int = Field(alias="current-schema-id", default=DEFAULT_SCHEMA_ID)
    """ID of the table’s current schema."""

    partition_specs: List[PartitionSpec] = Field(alias="partition-specs", default_factory=list)
    """A list of partition specs, stored as full partition spec objects."""

    default_spec_id: int = Field(alias="default-spec-id", default=INITIAL_SPEC_ID)
    """ID of the “current” spec that writers should use by default."""

    last_partition_id: int = Field(alias="last-partition-id")
    """An integer; the highest assigned partition field ID across all
    partition specs for the table. This is used to ensure partition fields
    are always assigned an unused ID when evolving specs."""

    properties: Dict[str, str] = Field(default_factory=dict)
    """	A string to string map of table properties. This is used to
    control settings that affect reading and writing and is not intended
    to be used for arbitrary metadata. For example, commit.retry.num-retries
    is used to control the number of commit retries."""

    current_snapshot_id: Optional[int] = Field(alias="current-snapshot-id")
    """ID of the current table snapshot."""

    snapshots: List[Snapshot] = Field(default_factory=list)
    """A list of valid snapshots. Valid snapshots are snapshots for which
    all data files exist in the file system. A data file must not be
    deleted from the file system until the last snapshot in which it was
    listed is garbage collected."""

    snapshot_log: List[Dict[str, Any]] = Field(alias="snapshot-log", default_factory=list)
    """A list (optional) of timestamp and snapshot ID pairs that encodes
    changes to the current snapshot for the table. Each time the
    current-snapshot-id is changed, a new entry should be added with the
    last-updated-ms and the new current-snapshot-id. When snapshots are
    expired from the list of valid snapshots, all entries before a snapshot
    that has expired should be removed."""

    metadata_log: List[Dict[str, Any]] = Field(alias="metadata-log", default_factory=list)
    """A list (optional) of timestamp and metadata file location pairs that
    encodes changes to the previous metadata files for the table. Each time
    a new metadata file is created, a new entry of the previous metadata
    file location should be added to the list. Tables can be configured to
    remove oldest metadata log entries and keep a fixed-size log of the most
    recent entries after a commit."""

    sort_orders: List[SortOrder] = Field(alias="sort-orders", default_factory=list)
    """A list of sort orders, stored as full sort order objects."""

    default_sort_order_id: int = Field(alias="default-sort-order-id", default=UNSORTED_SORT_ORDER_ID)
    """Default sort order id of the table. Note that this could be used by
    writers, but is not used when reading because reads use the specs stored
     in manifest files."""

    refs: Dict[str, SnapshotRef] = Field(default_factory=dict)
    """A map of snapshot references.
    The map keys are the unique snapshot reference names in the table,
    and the map values are snapshot reference objects.
    There is always a main branch reference pointing to the
    current-snapshot-id even if the refs map is null."""


class TableMetadataV1(TableMetadataCommonFields, IcebergBaseModel):
    """Represents version 1 of the Table Metadata

    More information about the specification:
    https://iceberg.apache.org/spec/#version-1-analytic-data-tables
    """

    # When we read a V1 format-version, we'll make sure to populate the fields
    # for V2 as well. This makes it easier downstream because we can just
    # assume that everything is a TableMetadataV2.
    # When writing, we should stick to the same version that it was,
    # because bumping the version should be an explicit operation that is up
    # to the owner of the table.

    @root_validator(pre=True)
    def set_v2_compatible_defaults(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sets default values to be compatible with the format v2

        Set some sensible defaults for V1, so we comply with the schema
        this is in pre=True, meaning that this will be done before validation.
        We don't want to make the fields optional, since they are required for V2

        Args:
            data: The raw arguments when initializing a V1 TableMetadata

        Returns:
            The TableMetadata with the defaults applied
        """
        if "schema-id" not in data["schema"]:
            data["schema"]["schema-id"] = DEFAULT_SCHEMA_ID
        if "last-partition-id" not in data:
            data["last-partition-id"] = max(spec["field-id"] for spec in data["partition-spec"])
        if "table-uuid" not in data:
            data["table-uuid"] = uuid4()
        return data

    @root_validator(skip_on_failure=True)
    def construct_schemas(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts the schema into schemas

        For V1 schemas is optional, and if they aren't set, we'll set them
        in this validator. This was we can always use the schemas when reading
        table metadata, and we don't have to worry if it is a v1 or v2 format.

        Args:
            data: The raw data after validation, meaning that the aliases are applied

        Returns:
            The TableMetadata with the schemas set, if not provided
        """
        if not data.get("schemas"):
            schema = data["schema_"]
            data["schemas"] = [schema]
        else:
            check_schemas(data["schemas"])
        return data

    @root_validator(skip_on_failure=True)
    def construct_partition_specs(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts the partition_spec into partition_specs

        For V1 partition_specs is optional, and if they aren't set, we'll set them
        in this validator. This was we can always use the partition_specs when reading
        table metadata, and we don't have to worry if it is a v1 or v2 format.

        Args:
            data: The raw data after validation, meaning that the aliases are applied

        Returns:
            The TableMetadata with the partition_specs set, if not provided
        """
        if not data.get("partition_specs"):
            fields = data["partition_spec"]
            data["partition_specs"] = [PartitionSpec(spec_id=INITIAL_SPEC_ID, fields=fields)]
        else:
            check_partition_specs(data["partition_specs"])
        return data

    @root_validator(skip_on_failure=True)
    def set_sort_orders(cls, data: Dict[str, Any]):
        """Sets the sort_orders if not provided

        For V1 sort_orders is optional, and if they aren't set, we'll set them
        in this validator.

        Args:
            data: The raw data after validation, meaning that the aliases are applied

        Returns:
            The TableMetadata with the sort_orders set, if not provided
        """
        if sort_orders := data.get("sort_orders"):
            check_sort_orders(sort_orders)
        else:
            data["sort_orders"] = [UNSORTED_SORT_ORDER]
        return data

    def to_v2(self) -> "TableMetadataV2":
        metadata = copy(self.dict())
        metadata["format_version"] = 2
        return TableMetadataV2(**metadata)

    format_version: Literal[1] = Field(alias="format-version")
    """An integer version number for the format. Currently, this can be 1 or 2
    based on the spec. Implementations must throw an exception if a table’s
    version is higher than the supported version."""

    schema_: Schema = Field(alias="schema")
    """The table’s current schema. (Deprecated: use schemas and
    current-schema-id instead)"""

    partition_spec: List[Dict[str, Any]] = Field(alias="partition-spec")
    """The table’s current partition spec, stored as only fields.
    Note that this is used by writers to partition data, but is
    not used when reading because reads use the specs stored in
    manifest files. (Deprecated: use partition-specs and default-spec-id
    instead)"""


class TableMetadataV2(TableMetadataCommonFields, IcebergBaseModel):
    """Represents version 2 of the Table Metadata

    This extends Version 1 with row-level deletes, and adds some additional
    information to the schema, such as all the historical schemas, partition-specs,
    sort-orders.

    For more information:
    https://iceberg.apache.org/spec/#version-2-row-level-deletes
    """

    @root_validator(skip_on_failure=True)
    def check_schemas(cls, values: Dict[str, Any]):
        return check_schemas(values)

    @root_validator
    def check_partition_specs(cls, values: Dict[str, Any]):
        return check_partition_specs(values)

    @root_validator(skip_on_failure=True)
    def check_sort_orders(cls, values: Dict[str, Any]):
        return check_sort_orders(values)

    format_version: Literal[2] = Field(alias="format-version")
    """An integer version number for the format. Currently, this can be 1 or 2
    based on the spec. Implementations must throw an exception if a table’s
    version is higher than the supported version."""

    table_uuid: UUID = Field(alias="table-uuid")
    """A UUID that identifies the table, generated when the table is created.
    Implementations must throw an exception if a table’s UUID does not match
    the expected UUID after refreshing metadata."""

    last_sequence_number: int = Field(alias="last-sequence-number", default=INITIAL_SEQUENCE_NUMBER)
    """The table’s highest assigned sequence number, a monotonically
    increasing long that tracks the order of snapshots in a table."""


class TableMetadata:
    """Helper class for parsing TableMetadata"""

    # Once this has been resolved, we can simplify this: https://github.com/samuelcolvin/pydantic/issues/3846
    # TableMetadata = Annotated[Union[TableMetadataV1, TableMetadataV2], Field(alias="format-version", discriminator="format-version")]

    @staticmethod
    def parse_obj(data: dict) -> Union[TableMetadataV1, TableMetadataV2]:
        if "format-version" not in data:
            raise ValidationError(f"Missing format-version in TableMetadata: {data}")

        format_version = data["format-version"]

        if format_version == 1:
            return TableMetadataV1(**data)
        elif format_version == 2:
            return TableMetadataV2(**data)
        else:
            raise ValidationError(f"Unknown format version: {format_version}")
