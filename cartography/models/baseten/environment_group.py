from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class BasetenEnvironmentGroupNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef(
        "id",
        description="Synthetic ID built from the team ID and the environment name.",
    )
    name: PropertyRef = PropertyRef(
        "name",
        extra_index=True,
        description=(
            "Environment name, such as `production`. The group governs that "
            "environment on every model and Chain in the team."
        ),
    )
    team_id: PropertyRef = PropertyRef(
        "team_id",
        description="ID of the team that the environment group belongs to.",
    )
    team_name: PropertyRef = PropertyRef(
        "team_name",
        description="Name of the team that the environment group belongs to.",
    )
    is_restricted: PropertyRef = PropertyRef(
        "is_restricted",
        description=(
            "Whether only designated users can manage the environment. When "
            "`false`, any team member can change deployments, autoscaling, and "
            "promotions in it."
        ),
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class BasetenEnvironmentGroupToOrganizationRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenOrganization)-[:RESOURCE]->(:BasetenEnvironmentGroup)
class BasetenEnvironmentGroupToOrganizationRel(CartographyRelSchema):
    """The organization contains the environment group."""

    target_node_label: str = "BasetenOrganization"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("ORG_ID", set_in_kwargs=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenEnvironmentGroupToOrganizationRelProperties = (
        BasetenEnvironmentGroupToOrganizationRelProperties()
    )


@dataclass(frozen=True)
class BasetenEnvironmentGroupToTeamRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenTeam)-[:RESOURCE]->(:BasetenEnvironmentGroup)
class BasetenEnvironmentGroupToTeamRel(CartographyRelSchema):
    """The team owns the environment group."""

    target_node_label: str = "BasetenTeam"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("team_id")},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: BasetenEnvironmentGroupToTeamRelProperties = (
        BasetenEnvironmentGroupToTeamRelProperties()
    )


@dataclass(frozen=True)
class BasetenEnvironmentGroupToUserRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:BasetenUser)-[:CAN_MANAGE]->(:BasetenEnvironmentGroup)
class BasetenEnvironmentGroupToUserRel(CartographyRelSchema):
    """
    The user can manage the restricted environment. Baseten lists these users only
    while the environment is restricted, and includes organization and team admins.
    """

    target_node_label: str = "BasetenUser"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("manager_user_ids", one_to_many=True)},
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CAN_MANAGE"
    properties: BasetenEnvironmentGroupToUserRelProperties = (
        BasetenEnvironmentGroupToUserRelProperties()
    )


@dataclass(frozen=True)
class BasetenEnvironmentGroupSchema(CartographyNodeSchema):
    """
    A Baseten environment group: the restriction settings for one environment name,
    such as `production`, across every model and Chain in a team.

    When an environment is restricted, only the users that Baseten lists can modify
    deployments, autoscaling, and promotions in it. Cartography reads each accessible
    team's groups from `GET /v1/teams/{team_id}/environment_groups`.
    """

    label: str = "BasetenEnvironmentGroup"
    properties: BasetenEnvironmentGroupNodeProperties = (
        BasetenEnvironmentGroupNodeProperties()
    )
    sub_resource_relationship: BasetenEnvironmentGroupToOrganizationRel = (
        BasetenEnvironmentGroupToOrganizationRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [BasetenEnvironmentGroupToTeamRel(), BasetenEnvironmentGroupToUserRel()],
    )
