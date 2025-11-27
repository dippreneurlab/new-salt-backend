from typing import List, Sequence

from ..core.database import execute, fetch, fetchrow
from ..models.overhead import OverheadEmployee

overhead_tables_ready = False


async def _ensure_table():
    global overhead_tables_ready
    if overhead_tables_ready:
        return
    await execute(
        """
        CREATE EXTENSION IF NOT EXISTS "pgcrypto";
        CREATE TABLE IF NOT EXISTS overhead_employees (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id TEXT NOT NULL,
          department TEXT NOT NULL,
          employee_name TEXT NOT NULL,
          role TEXT NOT NULL,
          location TEXT,
          annual_salary NUMERIC NOT NULL,
          allocation_percent NUMERIC NOT NULL,
          start_date DATE,
          end_date DATE,
          monthly_allocations JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          created_by TEXT,
          updated_by TEXT
        );
        CREATE INDEX IF NOT EXISTS overhead_user_idx ON overhead_employees(user_id);
        CREATE INDEX IF NOT EXISTS overhead_department_idx ON overhead_employees(department);
        """
    )
    overhead_tables_ready = True


def _to_employee(row: dict) -> OverheadEmployee:
    return OverheadEmployee(**row)


async def list_overhead_employees(user_id: str) -> List[OverheadEmployee]:
    await _ensure_table()
    rows = await fetch(
        "SELECT * FROM overhead_employees WHERE user_id = %s ORDER BY department ASC, employee_name ASC",
        [user_id],
    )
    return [_to_employee(r) for r in rows]


async def upsert_overhead_employees(user_id: str, employees: Sequence[OverheadEmployee], actor: str | None) -> List[OverheadEmployee]:
    await _ensure_table()
    results: List[OverheadEmployee] = []
    for emp in employees:
        data = emp.model_dump()
        saved = await fetchrow(
            """
            INSERT INTO overhead_employees (
              id, user_id, department, employee_name, role, location,
              annual_salary, allocation_percent, start_date, end_date,
              monthly_allocations, created_by, updated_by
            )
            VALUES (
              COALESCE(%(id)s, gen_random_uuid()), %(user_id)s, %(department)s, %(employee_name)s, %(role)s, %(location)s,
              %(annual_salary)s, %(allocation_percent)s, %(start_date)s, %(end_date)s,
              %(monthly_allocations)s, %(created_by)s, %(updated_by)s
            )
            ON CONFLICT (id) DO UPDATE SET
              department = EXCLUDED.department,
              employee_name = EXCLUDED.employee_name,
              role = EXCLUDED.role,
              location = EXCLUDED.location,
              annual_salary = EXCLUDED.annual_salary,
              allocation_percent = EXCLUDED.allocation_percent,
              start_date = EXCLUDED.start_date,
              end_date = EXCLUDED.end_date,
              monthly_allocations = EXCLUDED.monthly_allocations,
              updated_at = now(),
              updated_by = EXCLUDED.updated_by
            RETURNING *;
            """,
            {
                "id": data.get("id"),
                "user_id": user_id,
                "department": data.get("department"),
                "employee_name": data.get("employee_name"),
                "role": data.get("role"),
                "location": data.get("location"),
                "annual_salary": data.get("annual_salary"),
                "allocation_percent": data.get("allocation_percent"),
                "start_date": data.get("start_date"),
                "end_date": data.get("end_date"),
                "monthly_allocations": data.get("monthly_allocations") or {},
                "created_by": data.get("created_by") or actor,
                "updated_by": actor or data.get("updated_by") or data.get("created_by"),
            },
        )
        if saved:
            results.append(_to_employee(saved))
    return results


async def delete_overhead_employee(user_id: str, emp_id: str):
    await _ensure_table()
    await execute("DELETE FROM overhead_employees WHERE user_id = %s AND id = %s", [user_id, emp_id])
