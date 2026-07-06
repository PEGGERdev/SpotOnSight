from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bson import ObjectId
from fastapi import HTTPException, status

from core.workflows import (
    ActorRegistry,
    AuthorizeActor,
    BuildActor,
    ExecutionContext,
    LoadActor,
    PersistActor,
    ProjectActor,
    WorkflowDefinition,
    WorkflowRuntime,
    WorkflowServices,
    WorkflowStep,
)

from .builders import build_spot_doc
from .ids import as_text, spot_owner_id, viewer_user_id
from .mappers import to_spot_public
from .policies import can_view_spot, is_blocked_pair

if TYPE_CHECKING:
    from .actions import SocialActions


def _build_actor_registry() -> ActorRegistry:
    registry = ActorRegistry()
    registry.register("authorize", AuthorizeActor())
    registry.register("load", LoadActor())
    registry.register("build", BuildActor())
    registry.register("persist", PersistActor())
    registry.register("project", ProjectActor())
    return registry


def _workflow(name: str, *steps: WorkflowStep) -> WorkflowDefinition:
    return WorkflowDefinition(name=name, version=1, steps=list(steps))


SPOT_WORKFLOWS: dict[str, WorkflowDefinition] = {
    "spots.list_visible": _workflow(
        "spots.list_visible",
        WorkflowStep("load", {"loader": "spots.visible_candidates", "store_as": "spot_docs"}),
        WorkflowStep("project", {"projector": "spots.visible_list"}),
    ),
    "spots.create": _workflow(
        "spots.create",
        WorkflowStep("authorize", {"policy": "users.can_post"}),
        WorkflowStep("build", {"builder": "spots.create_document", "store_as": "spot_doc"}),
        WorkflowStep("persist", {"repository": "spots", "operation": "insert_one", "document_key": "spot_doc", "store_as": "created_spot_id"}),
        WorkflowStep("build", {"builder": "spots.created_lookup_query", "store_as": "spot_lookup_query"}),
        WorkflowStep("persist", {"repository": "spots", "operation": "find_one", "query_key": "spot_lookup_query", "store_as": "spot_doc"}),
        WorkflowStep("project", {"projector": "spots.single"}),
    ),
    "spots.update": _workflow(
        "spots.update",
        WorkflowStep("authorize", {"policy": "users.can_post"}),
        WorkflowStep("load", {"loader": "spots.target", "store_as": "target_spot"}),
        WorkflowStep("authorize", {"policy": "spots.owner_access", "detail": "Only owner can edit this spot"}),
        WorkflowStep("build", {"builder": "spots.target_lookup_query", "store_as": "spot_lookup_query"}),
        WorkflowStep("build", {"builder": "spots.updated_document", "store_as": "spot_doc"}),
        WorkflowStep("persist", {"repository": "spots", "operation": "update_fields", "query_key": "spot_lookup_query", "document_key": "spot_doc"}),
        WorkflowStep("persist", {"repository": "spots", "operation": "find_one", "query_key": "spot_lookup_query", "store_as": "spot_doc"}),
        WorkflowStep("project", {"projector": "spots.single"}),
    ),
    "spots.delete": _workflow(
        "spots.delete",
        WorkflowStep("load", {"loader": "spots.target", "store_as": "target_spot"}),
        WorkflowStep("authorize", {"policy": "spots.owner_access", "detail": "Only owner can delete this spot"}),
        WorkflowStep("build", {"builder": "spots.target_lookup_query", "store_as": "spot_lookup_query"}),
        WorkflowStep("build", {"builder": "spots.canonical_keys", "store_as": "spot_keys"}),
        WorkflowStep("build", {"builder": "spots.favorite_cleanup_query", "store_as": "favorites_cleanup_query"}),
        WorkflowStep("build", {"builder": "spots.share_cleanup_query", "store_as": "shares_cleanup_query"}),
        WorkflowStep("build", {"builder": "spots.comment_cleanup_query", "store_as": "comments_cleanup_query"}),
        WorkflowStep("persist", {"repository": "spots", "operation": "delete_one", "query_key": "spot_lookup_query"}),
        WorkflowStep("persist", {"repository": "favorites", "operation": "delete_many", "query_key": "favorites_cleanup_query"}),
        WorkflowStep("persist", {"repository": "shares", "operation": "delete_many", "query_key": "shares_cleanup_query"}),
        WorkflowStep("persist", {"repository": "comments", "operation": "delete_many", "query_key": "comments_cleanup_query"}),
        WorkflowStep("project", {"projector": "ok"}),
    ),
    "spots.user_spots": _workflow(
        "spots.user_spots",
        WorkflowStep("load", {"loader": "users.target_bundle", "store_as": "target_user"}),
        WorkflowStep("authorize", {"policy": "spots.user_spots_access"}),
        WorkflowStep("load", {"loader": "spots.user_candidates", "store_as": "spot_docs"}),
        WorkflowStep("project", {"projector": "spots.visible_list"}),
    ),
}


class SpotWorkflowExecutor:
    def __init__(self, actions: SocialActions) -> None:
        self.actions = actions
        self.runtime = WorkflowRuntime(actors=_build_actor_registry(), services=self._build_services())

    def list_visible_spots(self, current_user: dict[str, Any] | None):
        return self._run("spots.list_visible", principal=current_user).result

    def create_spot(self, req, current_user: dict[str, Any]):
        return self._run("spots.create", principal=current_user, input=req).result

    def update_spot(self, spot_id: str, req, current_user: dict[str, Any]):
        return self._run("spots.update", principal=current_user, input=req, state={"spot_id": spot_id}).result

    def delete_spot(self, spot_id: str, current_user: dict[str, Any]):
        return self._run("spots.delete", principal=current_user, state={"spot_id": spot_id}).result

    def user_spots(self, user_id: str, current_user: dict[str, Any]):
        return self._run("spots.user_spots", principal=current_user, state={"user_id": user_id}).result

    def _run(self, workflow_key: str, *, principal: Any, input: Any = None, state: dict[str, Any] | None = None) -> ExecutionContext:
        definition = SPOT_WORKFLOWS[workflow_key]
        context = ExecutionContext(principal=principal, input=input, state=dict(state or {}))
        return self.runtime.run(definition, context)

    def _build_services(self) -> WorkflowServices:
        repos = {
            "spots": self.actions.repos.spots,
            "favorites": self.actions.repos.favorites,
            "shares": self.actions.repos.shares,
            "comments": self.actions.repos.comments,
        }
        return WorkflowServices(
            repositories=repos,
            loaders={
                "spots.visible_candidates": self._load_visible_candidates,
                "spots.target": self._load_target_spot,
                "spots.user_candidates": self._load_user_candidates,
                "users.target_bundle": self._load_target_user_bundle,
            },
            builders={
                "spots.create_document": self._build_create_document,
                "spots.created_lookup_query": self._build_created_lookup_query,
                "spots.updated_document": self._build_updated_document,
                "spots.target_lookup_query": self._build_target_lookup_query,
                "spots.canonical_keys": self._build_canonical_spot_keys,
                "spots.favorite_cleanup_query": self._build_favorites_cleanup_query,
                "spots.share_cleanup_query": self._build_shares_cleanup_query,
                "spots.comment_cleanup_query": self._build_comments_cleanup_query,
            },
            policies={
                "users.can_post": self._policy_can_post,
                "spots.owner_access": self._policy_owner_access,
                "spots.user_spots_access": self._policy_user_spots_access,
            },
            projectors={
                "spots.visible_list": self._project_visible_spot_list,
                "spots.single": self._project_single_spot,
                "ok": self._project_ok,
            },
        )

    def _policy_can_post(self, context: ExecutionContext, _config: dict[str, Any]) -> None:
        self.actions.ensure_can_post(context.principal)

    def _policy_owner_access(self, context: ExecutionContext, _config: dict[str, Any]) -> None:
        existing = context.get("target_spot") or {}
        me_id = self.actions.me_id(context.principal)
        owner_id = spot_owner_id(existing)
        if owner_id and owner_id != me_id:
            detail = as_text(_config.get("detail")) or "Only owner can modify this spot"
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    def _policy_user_spots_access(self, context: ExecutionContext, _config: dict[str, Any]) -> None:
        target_user = context.get("target_user") or {}
        target_id = as_text(target_user.get("id"))
        me_id = self.actions.me_id(context.principal)
        if not self.actions.is_admin(context.principal) and me_id != target_id and is_blocked_pair(self.actions.repos, me_id, target_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    def _load_visible_candidates(self, _context: ExecutionContext, _config: dict[str, Any]) -> list[dict[str, Any]]:
        return self.actions.repos.spots.find_all_sorted(sort_field="created_at", sort_direction=-1, limit=1500)

    def _load_target_spot(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        return self.actions.spot_or_404(as_text(context.get("spot_id")))

    def _load_target_user_bundle(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        target_id, target = self.actions.user_or_404(as_text(context.get("user_id")))
        return {"id": target_id, "doc": target}

    def _load_user_candidates(self, context: ExecutionContext, _config: dict[str, Any]) -> list[dict[str, Any]]:
        target_user = context.get("target_user") or {}
        target_id = as_text(target_user.get("id"))
        return self.actions.repos.spots.find_many_sorted({"owner_id": target_id}, sort_field="created_at", sort_direction=-1, limit=1200)

    def _build_create_document(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        owner_id = self.actions.me_id(context.principal)
        document = build_spot_doc(context.input, owner_id=owner_id)
        document["moderation_status"] = "visible"
        return document

    def _build_created_lookup_query(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        return {"_id": ObjectId(as_text(context.get("created_spot_id")))}

    def _build_updated_document(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        existing = context.get("target_spot") or {}
        me_id = self.actions.me_id(context.principal)
        owner_id = spot_owner_id(existing) or me_id
        document = build_spot_doc(context.input, owner_id=owner_id, created_at=existing.get("created_at"))
        document["moderation_status"] = self.actions._content_status(existing)
        return document

    def _build_target_lookup_query(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        existing = context.get("target_spot") or {}
        return {"_id": existing.get("_id")}

    def _build_canonical_spot_keys(self, context: ExecutionContext, _config: dict[str, Any]) -> list[str]:
        existing = context.get("target_spot") or {}
        raw_values = [as_text(context.get("spot_id")), as_text(existing.get("_id"))]
        return [value for value in dict.fromkeys([value for value in raw_values if value])]

    def _build_favorites_cleanup_query(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        return {"spot_id": {"$in": context.get("spot_keys", [])}}

    def _build_shares_cleanup_query(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        return {"spot_id": {"$in": context.get("spot_keys", [])}}

    def _build_comments_cleanup_query(self, context: ExecutionContext, _config: dict[str, Any]) -> dict[str, Any]:
        return {"spot_id": {"$in": context.get("spot_keys", [])}}

    def _project_visible_spot_list(self, context: ExecutionContext, _config: dict[str, Any]):
        docs = context.get("spot_docs", []) or []
        me_id = viewer_user_id(context.principal)
        if self.actions.is_admin(context.principal):
            return [to_spot_public(doc) for doc in docs]
        return [
            to_spot_public(doc)
            for doc in docs
            if self.actions._content_status(doc) != "hidden" and can_view_spot(self.actions.repos, me_id, doc)
        ]

    def _project_single_spot(self, context: ExecutionContext, _config: dict[str, Any]):
        doc = context.get("spot_doc")
        if not doc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Spot workflow did not produce a spot")
        return to_spot_public(doc)

    @staticmethod
    def _project_ok(_context: ExecutionContext, _config: dict[str, Any]) -> dict[str, bool]:
        return {"ok": True}
