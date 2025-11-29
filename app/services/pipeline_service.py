from calendar import monthrange
from datetime import date, datetime
from typing import Iterable, List, Optional, Sequence

from ..core.database import execute, fetch, fetchrow
from ..models.pipeline import PipelineChange, PipelineEntry


def _normalize_status(status: Optional[str]) -> str:
    raw = (status or "open").lower().strip()
    mapping = {
        "open": "open",
        "high pitch": "high-pitch",
        "high-pitch": "high-pitch",
        "medium pitch": "medium-pitch",
        "medium-pitch": "medium-pitch",
        "low pitch": "low-pitch",
        "low-pitch": "low-pitch",
        "confirmed": "confirmed",
        "whitespace": "whitespace",
        "cancelled": "cancelled",
        "canceled": "cancelled",
        "in plan": "open",
        "in-plan": "open",
        "planning": "open",
    }
    return mapping.get(raw, "open")


def _parse_date(value: Optional[str], is_end: bool) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()

    if len(trimmed) == 10 and trimmed[4] == "-" and trimmed[7] == "-":
        return trimmed

    parsed_month_year: Optional[datetime] = None
    parts = trimmed.split()
    if len(parts) == 2 and parts[1].isdigit():
        for fmt in ("%b %Y", "%B %Y"):
            try:
                parsed_month_year = datetime.strptime(trimmed, fmt)
                break
            except ValueError:
                continue

    if parsed_month_year:
        y, m = parsed_month_year.year, parsed_month_year.month
        last_day = monthrange(y, m)[1]
        target_day = last_day if is_end else 1
        return date(y, m, target_day).isoformat()

    try:
        parsed = datetime.fromisoformat(trimmed)
        return parsed.date().isoformat()
    except ValueError:
        return None


def _normalize_month(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    trimmed = value.strip()
    try:
        date = datetime.fromisoformat(trimmed)
        return date.strftime("%b %Y")
    except ValueError:
        pass
    if any(char.isdigit() for char in trimmed):
        return trimmed
    return trimmed


def _iso_or_none(value: Optional[object]) -> Optional[str]:
    """Normalize DB date/datetime to ISO string for Pydantic/JSON."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


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


def _to_db_row(user_id: str, entry: PipelineEntry) -> dict:
    if not entry.projectCode:
        raise ValueError("projectCode is required")
    return {
        "project_code": entry.projectCode,
        "owner": entry.owner,
        "client": entry.client,
        "program_name": entry.programName,
        "program_type": entry.programType or "Integrated",
        "region": entry.region or "Canada",
        "start_date": _parse_date(entry.startMonth, False),
        "end_date": _parse_date(entry.endMonth, True),
        "start_month": _normalize_month(entry.startMonth),
        "end_month": _normalize_month(entry.endMonth),
        "revenue": entry.revenue or 0,
        "total_fees": entry.totalFees or 0,
        "status": _normalize_status(entry.status),
        "accounts_fees": entry.accounts or 0,
        "creative_fees": entry.creative or 0,
        "design_fees": entry.design or 0,
        "strategic_planning_fees": entry.strategy or 0,
        "media_fees": entry.media or 0,
        "creator_fees": entry.creator or 0,
        "social_fees": entry.social or 0,
        "omni_fees": entry.omni or 0,
        "digital_fees": entry.studio or 0,
        "finance_fees": entry.finance or 0,
        "created_by": user_id,
        "updated_by": user_id,
    }


def _from_db_row(row: dict) -> PipelineEntry:
    return PipelineEntry(
        projectCode=row.get("project_code"),
        owner=row.get("owner"),
        client=row.get("client"),
        programName=row.get("program_name"),
        programType=row.get("program_type"),
        region=row.get("region"),
        startMonth=row.get("start_month") or "",
        endMonth=row.get("end_month") or "",
        startDate=_iso_or_none(row.get("start_date")),
        endDate=_iso_or_none(row.get("end_date")),
        revenue=float(row.get("revenue") or 0),
        totalFees=float(row.get("total_fees") or 0),
        status=row.get("status"),
        accounts=float(row.get("accounts_fees") or 0),
        creative=float(row.get("creative_fees") or 0),
        design=float(row.get("design_fees") or 0),
        strategy=float(row.get("strategic_planning_fees") or 0),
        media=float(row.get("media_fees") or 0),
        studio=float(row.get("digital_fees") or 0),
        creator=float(row.get("creator_fees") or 0),
        social=float(row.get("social_fees") or 0),
        omni=float(row.get("omni_fees") or 0),
        finance=float(row.get("finance_fees") or 0),
        createdBy=row.get("created_by"),
        updatedBy=row.get("updated_by"),
        createdByEmail=row.get("created_by_email"),
        updatedByEmail=row.get("updated_by_email"),
        createdAt=row.get("created_at"),
        updatedAt=row.get("updated_at"),
    )


def build_pipeline_changelog(entries: Iterable[PipelineEntry], user_email: str) -> List[PipelineChange]:
    changes: List[PipelineChange] = []
    for entry in entries:
        date = entry.updatedAt or entry.createdAt or datetime.utcnow()
        changes.append(
            PipelineChange(
                type="addition",
                projectCode=entry.projectCode,
                projectName=entry.programName,
                client=entry.client,
                description="Added/updated from Cloud SQL",
                date=str(date),
                user=entry.updatedByEmail or entry.createdByEmail or user_email or "system",
            )
        )
    return sorted(changes, key=lambda c: c.date, reverse=True)


async def replace_pipeline_entries(user_id: str, entries: Sequence[PipelineEntry], email: Optional[str]):
    await _ensure_user(user_id, email)
    for entry in entries:
        row = _to_db_row(user_id, entry)
        await execute(
            """
            INSERT INTO pipeline_opportunities (
                project_code, owner, client, program_name, program_type, region,
                start_date, end_date, start_month, end_month, revenue, total_fees, status,
                accounts_fees, creative_fees, design_fees, strategic_planning_fees, media_fees,
                creator_fees, social_fees, omni_fees, digital_fees, finance_fees,
                created_by, updated_by
            )
            VALUES (
                %(project_code)s, %(owner)s, %(client)s, %(program_name)s, %(program_type)s, %(region)s,
                %(start_date)s, %(end_date)s, %(start_month)s, %(end_month)s, %(revenue)s, %(total_fees)s, %(status)s,
                %(accounts_fees)s, %(creative_fees)s, %(design_fees)s, %(strategic_planning_fees)s, %(media_fees)s,
                %(creator_fees)s, %(social_fees)s, %(omni_fees)s, %(digital_fees)s, %(finance_fees)s,
                %(created_by)s, %(updated_by)s
            )
            ON CONFLICT (project_code) DO UPDATE SET
                owner = EXCLUDED.owner,
                client = EXCLUDED.client,
                program_name = EXCLUDED.program_name,
                program_type = EXCLUDED.program_type,
                region = EXCLUDED.region,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                start_month = EXCLUDED.start_month,
                end_month = EXCLUDED.end_month,
                revenue = EXCLUDED.revenue,
                total_fees = EXCLUDED.total_fees,
                status = EXCLUDED.status,
                accounts_fees = EXCLUDED.accounts_fees,
                creative_fees = EXCLUDED.creative_fees,
                design_fees = EXCLUDED.design_fees,
                strategic_planning_fees = EXCLUDED.strategic_planning_fees,
                media_fees = EXCLUDED.media_fees,
                creator_fees = EXCLUDED.creator_fees,
                social_fees = EXCLUDED.social_fees,
                omni_fees = EXCLUDED.omni_fees,
                digital_fees = EXCLUDED.digital_fees,
                finance_fees = EXCLUDED.finance_fees,
                updated_at = now(),
                updated_by = EXCLUDED.updated_by
            """,
            row,
        )

    codes = [entry.projectCode for entry in entries]
    if codes:
        placeholders = ", ".join(["%s"] * len(codes))
        await execute(
            f"DELETE FROM pipeline_opportunities WHERE created_by = %s AND project_code NOT IN ({placeholders})",
            [user_id, *codes],
        )
    else:
        await execute("DELETE FROM pipeline_opportunities WHERE created_by = %s", [user_id])


async def get_pipeline_entries_for_user(user_id: Optional[str]) -> List[PipelineEntry]:
    rows = await fetch(
        """
        SELECT po.*,
               cu.email AS created_by_email,
               uu.email AS updated_by_email
        FROM pipeline_opportunities po
        LEFT JOIN users cu ON cu.id = po.created_by
        LEFT JOIN users uu ON uu.id = po.updated_by
        ORDER BY po.project_code ASC
        """
    )
    return [_from_db_row(r) for r in rows]


async def upsert_pipeline_entry(user_id: str, entry: PipelineEntry, email: Optional[str]) -> PipelineEntry:
    await _ensure_user(user_id, email)
    row = _to_db_row(user_id, entry)
    saved = await fetchrow(
        """
        INSERT INTO pipeline_opportunities (
            project_code, owner, client, program_name, program_type, region,
            start_date, end_date, start_month, end_month, revenue, total_fees, status,
            accounts_fees, creative_fees, design_fees, strategic_planning_fees, media_fees,
            creator_fees, social_fees, omni_fees, digital_fees, finance_fees,
            created_by, updated_by
        )
        VALUES (
            %(project_code)s, %(owner)s, %(client)s, %(program_name)s, %(program_type)s, %(region)s,
            %(start_date)s, %(end_date)s, %(start_month)s, %(end_month)s, %(revenue)s, %(total_fees)s, %(status)s,
            %(accounts_fees)s, %(creative_fees)s, %(design_fees)s, %(strategic_planning_fees)s, %(media_fees)s,
            %(creator_fees)s, %(social_fees)s, %(omni_fees)s, %(digital_fees)s, %(finance_fees)s,
            %(created_by)s, %(updated_by)s
        )
        ON CONFLICT (project_code) DO UPDATE SET
            owner = EXCLUDED.owner,
            client = EXCLUDED.client,
            program_name = EXCLUDED.program_name,
            program_type = EXCLUDED.program_type,
            region = EXCLUDED.region,
            start_date = EXCLUDED.start_date,
            end_date = EXCLUDED.end_date,
            start_month = EXCLUDED.start_month,
            end_month = EXCLUDED.end_month,
            revenue = EXCLUDED.revenue,
            total_fees = EXCLUDED.total_fees,
            status = EXCLUDED.status,
            accounts_fees = EXCLUDED.accounts_fees,
            creative_fees = EXCLUDED.creative_fees,
            design_fees = EXCLUDED.design_fees,
            strategic_planning_fees = EXCLUDED.strategic_planning_fees,
            media_fees = EXCLUDED.media_fees,
            creator_fees = EXCLUDED.creator_fees,
            social_fees = EXCLUDED.social_fees,
            omni_fees = EXCLUDED.omni_fees,
            digital_fees = EXCLUDED.digital_fees,
            finance_fees = EXCLUDED.finance_fees,
            updated_at = now(),
            updated_by = EXCLUDED.updated_by
        RETURNING *
        """,
        row,
    )
    if not saved:
        raise RuntimeError("Failed to upsert pipeline entry")
    return _from_db_row(saved)


async def delete_pipeline_entry(project_code: str):
    await execute("DELETE FROM pipeline_opportunities WHERE project_code = %s", [project_code])


async def get_next_project_code(year: str) -> str:
    row = await fetchrow(
        """
        SELECT project_code FROM pipeline_opportunities
        WHERE project_code LIKE %s
        ORDER BY project_code DESC
        LIMIT 1
        """,
        [f"P____-{year}"],
    )
    if not row:
        return f"P0001-{year}"
    latest = row.get("project_code", "")
    prefix = latest[1:5] if len(latest) >= 5 else "0000"
    try:
        num = int(prefix) + 1
    except ValueError:
        num = 1
    return f"P{str(num).zfill(4)}-{year}"
