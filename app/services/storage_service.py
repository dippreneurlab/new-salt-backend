import json
from typing import Any, Dict, List, Optional

from ..core.database import execute, fetch, fetchrow
from ..models.pipeline import PipelineEntry
from ..services.pipeline_service import (
    build_pipeline_changelog,
    get_pipeline_entries_for_user,
    replace_pipeline_entries,
)
from ..services.quotes_service import get_quotes_for_user, parse_quotes_value, replace_quotes
from ..models.quote import QuotePayload

PIPELINE_KEY = "pipeline-entries"
QUOTES_KEY = "saltxc-all-quotes"
PIPELINE_CHANGELOG_KEY = "pipeline-changelog"

storage_table_ready = False


async def _ensure_storage_table():
    global storage_table_ready
    if storage_table_ready:
        return
    await execute(
        """
        CREATE TABLE IF NOT EXISTS user_storage (
          id SERIAL PRIMARY KEY,
          user_id TEXT NOT NULL,
          storage_key TEXT NOT NULL,
          storage_value JSONB NOT NULL DEFAULT '{}'::jsonb,
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          UNIQUE(user_id, storage_key)
        );
        """
    )
    storage_table_ready = True


def _parse_pipeline_value(value: Any) -> List[PipelineEntry]:
    data: List[Any] = []
    if value is None:
        data = []
    elif isinstance(value, list):
        data = value
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
            data = parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            data = []
    entries: List[PipelineEntry] = []
    for item in data:
        try:
            entries.append(PipelineEntry.model_validate(item))
        except Exception:
            continue
    return entries


async def get_storage_value(user_id: str, key: str) -> Optional[Any]:
    if key == PIPELINE_KEY:
        entries = await get_pipeline_entries_for_user(user_id)
        # Ensure datetimes are serialized to ISO strings for CloudStorage consumers
        return json.dumps([e.model_dump(mode="json") for e in entries])
    if key == QUOTES_KEY:
        quotes = await get_quotes_for_user(user_id)
        return json.dumps(quotes)

    await _ensure_storage_table()
    row = await fetchrow(
        "SELECT storage_value FROM user_storage WHERE user_id = %s AND storage_key = %s",
        [user_id, key],
    )
    value = row["storage_value"] if row else None
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


async def set_storage_value(user_id: str, key: str, value: Any, email: Optional[str]) -> Any:
    if key == PIPELINE_KEY:
        entries = _parse_pipeline_value(value)
        await replace_pipeline_entries(user_id, entries, email)
        return value

    if key == QUOTES_KEY:
        quotes_raw = parse_quotes_value(value)
        quotes_models = [QuotePayload.model_validate(q) for q in quotes_raw]
        await replace_quotes(user_id, quotes_models, email)
        return value

    await _ensure_storage_table()
    row = await fetchrow(
        """
        INSERT INTO user_storage (user_id, storage_key, storage_value)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, storage_key)
        DO UPDATE SET storage_value = EXCLUDED.storage_value, updated_at = now()
        RETURNING storage_value;
        """,
        [user_id, key, value],
    )
    return row["storage_value"] if row else value


async def delete_storage_value(user_id: str, key: str):
    if key == PIPELINE_KEY:
        await replace_pipeline_entries(user_id, [], None)
        return
    if key == QUOTES_KEY:
        await replace_quotes(user_id, [], None)
        return

    await _ensure_storage_table()
    await execute("DELETE FROM user_storage WHERE user_id = %s AND storage_key = %s", [user_id, key])


async def list_storage_values(user_id: str) -> Dict[str, Any]:
    await _ensure_storage_table()
    rows = await fetch("SELECT storage_key, storage_value FROM user_storage WHERE user_id = %s", [user_id])

    values: Dict[str, Any] = {}
    for row in rows:
        val = row.get("storage_value")
        values[row["storage_key"]] = val if val is None or isinstance(val, str) else json.dumps(val)

    pipeline_entries = await get_pipeline_entries_for_user(user_id)
    quotes = await get_quotes_for_user(user_id)

    # Use json mode to serialize datetimes as ISO strings
    values[PIPELINE_KEY] = json.dumps([e.model_dump(mode="json") for e in pipeline_entries])
    values[QUOTES_KEY] = json.dumps(quotes)

    changelog = build_pipeline_changelog(pipeline_entries, values.get("email") or user_id)
    values[PIPELINE_CHANGELOG_KEY] = json.dumps([c.model_dump(mode="json") for c in changelog])

    return values
