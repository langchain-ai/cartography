from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.nodes import ExtraNodeLabels
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher
from cartography.models.ontology.labels import TENANT


@dataclass(frozen=True)
class WorkshopTenantProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("id", description="Operator-configured tenant scope.")
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkshopTenantSchema(CartographyNodeSchema):
    """A Workshop tenant scope bound by the operator to one API origin and key."""

    label: str = "WorkshopTenant"
    properties: WorkshopTenantProperties = WorkshopTenantProperties()
    extra_node_labels: ExtraNodeLabels = ExtraNodeLabels([TENANT])


@dataclass(frozen=True)
class WorkshopRelationshipProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class WorkshopTenantResource(CartographyRelSchema):
    """Contains a configured Workshop resource within its tenant scope."""

    target_node_label: str = "WorkshopTenant"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("TENANT_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: WorkshopRelationshipProperties = WorkshopRelationshipProperties()


@dataclass(frozen=True)
class WorkshopClientModeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="JSON tuple of tenant scope and mode."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Operator-configured tenant scope."
    )
    name: PropertyRef = PropertyRef(
        "name",
        description="Configured vendor enum; UNKNOWN_CLIENT_MODE means unspecified.",
    )


@dataclass(frozen=True)
class WorkshopClientModeSchema(CartographyNodeSchema):
    """A tenant-scoped configured client mode, not an effective host policy."""

    label: str = "WorkshopClientMode"
    properties: WorkshopClientModeProperties = WorkshopClientModeProperties()
    sub_resource_relationship: WorkshopTenantResource = WorkshopTenantResource()


@dataclass(frozen=True)
class WorkshopConfiguredClientMode(CartographyRelSchema):
    """Links a tag to its configured mode without resolving precedence or host state."""

    target_node_label: str = "WorkshopClientMode"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("mode_id")},
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "CONFIGURED_CLIENT_MODE"
    properties: WorkshopRelationshipProperties = WorkshopRelationshipProperties()


@dataclass(frozen=True)
class WorkshopTagProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id", description="JSON tuple of tenant scope and tag."
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)
    tenant_id: PropertyRef = PropertyRef(
        "TENANT_ID", set_in_kwargs=True, description="Operator-configured tenant scope."
    )
    tag: PropertyRef = PropertyRef("tag", description="Literal ListSyncSettings tag.")


@dataclass(frozen=True)
class WorkshopTagSchema(CartographyNodeSchema):
    """A configured tag; complete reads replace stale edges only in this tenant."""

    label: str = "WorkshopTag"
    properties: WorkshopTagProperties = WorkshopTagProperties()
    sub_resource_relationship: WorkshopTenantResource = WorkshopTenantResource()
    other_relationships: OtherRelationships = OtherRelationships(
        [WorkshopConfiguredClientMode()],
    )
