from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass

from fastapi import Header, HTTPException


DEMO_COMPANY_ID = "demo-ai-enterprise"
DEMO_ACTOR_ID = "demo-risk-operator"
GATEWAY_SECRET_ENV = "RISK_GATEWAY_IDENTITY_SECRET"


@dataclass(frozen=True)
class EnterpriseActor:
    actor_id: str
    company_id: str
    roles: frozenset[str]


def require_enterprise_actor(
    x_risk_identity: str | None = Header(default=None),
    x_risk_identity_signature: str | None = Header(default=None),
) -> EnterpriseActor:
    """Accept a gateway-signed identity. Local demonstration traffic is fixed, not caller-selected."""
    secret = os.getenv(GATEWAY_SECRET_ENV)
    if not x_risk_identity:
        if os.getenv("RISK_DEMO_IDENTITY_ENABLED", "false").lower() == "true":
            return EnterpriseActor(DEMO_ACTOR_ID, DEMO_COMPANY_ID, frozenset({
                "risk_viewer", "risk_operator", "risk_reviewer", "risk_decision_maker",
            }))
        raise HTTPException(status_code=401, detail="trusted enterprise identity is required")
    if not secret or not x_risk_identity_signature:
        raise HTTPException(status_code=401, detail="gateway-signed enterprise identity is required")
    expected = hmac.new(secret.encode("utf-8"), x_risk_identity.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, x_risk_identity_signature):
        raise HTTPException(status_code=401, detail="enterprise identity signature is invalid")
    parts = x_risk_identity.split("|", 2)
    if len(parts) != 3 or not all(parts):
        raise HTTPException(status_code=401, detail="enterprise identity format is invalid")
    actor_id, company_id, role_text = parts
    return EnterpriseActor(actor_id, company_id, frozenset(role for role in role_text.split(",") if role))


def require_company(actor: EnterpriseActor, company_id: str | None = None) -> str:
    if company_id and company_id != actor.company_id:
        raise HTTPException(status_code=403, detail="enterprise scope is not authorized")
    return actor.company_id


def require_role(actor: EnterpriseActor, *roles: str) -> None:
    if not set(roles).intersection(actor.roles):
        raise HTTPException(status_code=403, detail="the current enterprise role is not authorized for this action")
