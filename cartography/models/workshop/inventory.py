from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.workshop.settings import WorkshopRelationshipProperties
from cartography.models.workshop.settings import WorkshopTenantResource


@dataclass(frozen=True)
class WorkshopUserProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="JSON tuple of tenant scope and directory user ID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tenant_id: PropertyRef = PropertyRef("TENANT_ID", set_in_kwargs=True)
    user_id: PropertyRef = PropertyRef(
        "user_id", description="Opaque directory user ID returned by ListUsers."
    )
    username: PropertyRef = PropertyRef(
        "username",
        description="Vendor-normalized directory username; not assumed to be an email address.",
    )
    manager_email: PropertyRef = PropertyRef("manager_email")
    department_name: PropertyRef = PropertyRef("department_name")
    cost_center_name: PropertyRef = PropertyRef("cost_center_name")
    directory_type: PropertyRef = PropertyRef("directory_type")


@dataclass(frozen=True)
class WorkshopUserSchema(CartographyNodeSchema):
    """A directory user, not a complete workstation-local account inventory."""

    label: str = "WorkshopUser"
    properties: WorkshopUserProperties = WorkshopUserProperties()
    sub_resource_relationship: WorkshopTenantResource = WorkshopTenantResource()


@dataclass(frozen=True)
class WorkshopHostTag(CartographyRelSchema):
    """A tag returned in the host's tags list; no precedence is inferred."""

    target_node_label: str = "WorkshopTag"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("tag_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "HAS_TAG"
    properties: WorkshopRelationshipProperties = WorkshopRelationshipProperties()


@dataclass(frozen=True)
class WorkshopHostPrimaryUser(CartographyRelSchema):
    """Matches the reported primary user to exactly one directory username in this tenant."""

    target_node_label: str = "WorkshopUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("primary_user_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "PRIMARY_USER"
    properties: WorkshopRelationshipProperties = WorkshopRelationshipProperties()


@dataclass(frozen=True)
class WorkshopHostProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="JSON tuple of tenant scope and opaque host UUID."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tenant_id: PropertyRef = PropertyRef("TENANT_ID", set_in_kwargs=True)
    uuid: PropertyRef = PropertyRef("uuid")
    hostname: PropertyRef = PropertyRef("hostname")
    serial: PropertyRef = PropertyRef("serial")
    machine_model: PropertyRef = PropertyRef("machine_model")
    os_version: PropertyRef = PropertyRef("os_version")
    os_build: PropertyRef = PropertyRef("os_build")
    santa_version: PropertyRef = PropertyRef("santa_version")
    last_sync: PropertyRef = PropertyRef(
        "last_sync",
        description="Vendor-reported last communication timestamp, not the Cartography sync time.",
    )
    primary_user: PropertyRef = PropertyRef(
        "primary_user",
        description="Reported primary username retained even without an unambiguous directory match.",
    )
    primary_user_groups: PropertyRef = PropertyRef(
        "primary_user_groups",
        description="Reported group names, not an inferred directory membership graph.",
    )


@dataclass(frozen=True)
class WorkshopHostSchema(CartographyNodeSchema):
    """A workstation inventory record; no effective or reported enforcement mode is inferred."""

    label: str = "WorkshopHost"
    properties: WorkshopHostProperties = WorkshopHostProperties()
    sub_resource_relationship: WorkshopTenantResource = WorkshopTenantResource()
    other_relationships: OtherRelationships = OtherRelationships(
        [WorkshopHostTag(), WorkshopHostPrimaryUser()],
    )
