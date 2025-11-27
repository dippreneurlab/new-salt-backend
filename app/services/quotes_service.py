import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from ..core.database import execute, fetch
from ..models.quote import QuotePayload


def _normalize_date(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.date().isoformat()
    except ValueError:
        return None


async def _ensure_user(user_id: str, email: Optional[str]):
    safe_email = email or f"{user_id}@placeholder.local"
    await execute(
        """
        INSERT INTO users (id, email)
        VALUES (%s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        [user_id, safe_email],
    )


def parse_quotes_value(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


async def replace_quotes(user_id: str, quotes: Sequence[QuotePayload], email: Optional[str]):
    await _ensure_user(user_id, email)
    for quote in quotes:
        data = quote.model_dump()
        project = data.get("project", {}) or {}
        project_number = data.get("projectNumber") or project.get("projectNumber") or ""
        quote_uid = data.get("id") or f"{project_number or 'quote'}-{user_id}"

        await execute(
            """
            INSERT INTO quotes (
              quote_uid,
              project_number,
              client_name,
              client_category,
              brand,
              project_name,
              brief_date,
              in_market_date,
              project_completion_date,
              total_program_budget,
              rate_card,
              currency,
              phases,
              phase_settings,
              status,
              created_by,
              updated_by,
              full_quote
            )
            VALUES (
              %(quote_uid)s, %(project_number)s, %(client_name)s, %(client_category)s, %(brand)s,
              %(project_name)s, %(brief_date)s, %(in_market_date)s, %(project_completion_date)s,
              %(total_program_budget)s, %(rate_card)s, %(currency)s, %(phases)s, %(phase_settings)s,
              %(status)s, %(created_by)s, %(updated_by)s, %(full_quote)s
            )
            ON CONFLICT (quote_uid) DO UPDATE SET
              project_number = EXCLUDED.project_number,
              client_name = EXCLUDED.client_name,
              client_category = EXCLUDED.client_category,
              brand = EXCLUDED.brand,
              project_name = EXCLUDED.project_name,
              brief_date = EXCLUDED.brief_date,
              in_market_date = EXCLUDED.in_market_date,
              project_completion_date = EXCLUDED.project_completion_date,
              total_program_budget = EXCLUDED.total_program_budget,
              rate_card = EXCLUDED.rate_card,
              currency = EXCLUDED.currency,
              phases = EXCLUDED.phases,
              phase_settings = EXCLUDED.phase_settings,
              status = EXCLUDED.status,
              updated_at = now(),
              updated_by = EXCLUDED.updated_by,
              full_quote = EXCLUDED.full_quote
            """,
            {
                "quote_uid": quote_uid,
                "project_number": project_number,
                "client_name": data.get("clientName") or "",
                "client_category": project.get("clientCategory") or data.get("clientCategory") or "",
                "brand": data.get("brand") or "",
                "project_name": data.get("projectName") or "",
                "brief_date": _normalize_date(project.get("briefDate") or data.get("briefDate")),
                "in_market_date": _normalize_date(project.get("inMarketDate") or data.get("inMarketDate")),
                "project_completion_date": _normalize_date(project.get("projectCompletionDate") or data.get("projectCompletionDate")),
                "total_program_budget": project.get("totalProgramBudget") or data.get("totalRevenue"),
                "rate_card": project.get("rateCard") or data.get("rateCard"),
                "currency": data.get("currency") or project.get("currency") or "CAD",
                "phases": project.get("phases") or [],
                "phase_settings": project.get("phaseSettings") or {},
                "status": data.get("status") or "draft",
                "created_by": user_id,
                "updated_by": user_id,
                "full_quote": data,
            },
        )

    ids = [q.model_dump().get("id") or f"{(q.model_dump().get('projectNumber') or (q.model_dump().get('project') or {}).get('projectNumber') or 'quote')}-{user_id}" for q in quotes]
    if ids:
        placeholders = ", ".join(["%s"] * len(ids))
        await execute(
            f"DELETE FROM quotes WHERE created_by = %s AND quote_uid IS NOT NULL AND quote_uid NOT IN ({placeholders})",
            [user_id, *ids],
        )
    else:
        await execute("DELETE FROM quotes WHERE created_by = %s", [user_id])


async def get_quotes_for_user(user_id: str) -> List[Dict[str, Any]]:
    rows = await fetch(
        """
        SELECT full_quote FROM quotes
        WHERE created_by = %s OR updated_by = %s
        ORDER BY updated_at DESC
        """,
        [user_id, user_id],
    )
    return [r.get("full_quote") or {} for r in rows]
