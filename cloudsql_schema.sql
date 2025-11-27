-- Cloud SQL / Postgres schema for Connections Quote Tool
-- All app entry points write to this database (Firebase-authenticated).

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- USERS (Firebase metadata mirror)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY, -- Firebase UID
  email TEXT UNIQUE NOT NULL,
  full_name TEXT,
  role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'pm')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================
-- USER KEY/VALUE STORAGE (used by the app today)
-- =====================================================
CREATE TABLE IF NOT EXISTS user_storage (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  storage_key TEXT NOT NULL,
  storage_value JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, storage_key)
);

CREATE INDEX IF NOT EXISTS user_storage_user_idx ON user_storage(user_id);

-- =====================================================
-- OVERHEAD EMPLOYEES (used by /api/overhead-employees)
-- =====================================================
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
CREATE INDEX IF NOT EXISTS overhead_employee_idx ON overhead_employees(employee_name);

-- =====================================================
-- PIPELINE OPPORTUNITIES
-- =====================================================
CREATE TABLE IF NOT EXISTS pipeline_opportunities (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_code TEXT UNIQUE NOT NULL,
  owner TEXT NOT NULL,
  client TEXT NOT NULL,
  program_name TEXT NOT NULL,
  program_type TEXT DEFAULT 'Integrated' CHECK (program_type IN ('XM', 'Media', 'Integrated')),
  region TEXT DEFAULT 'Canada' CHECK (region IN ('Canada', 'US')),
  start_date DATE,
  end_date DATE,
  start_month TEXT,
  end_month TEXT,
  revenue NUMERIC(12,2) DEFAULT 0,
  total_fees NUMERIC(12,2) DEFAULT 0,
  status TEXT DEFAULT 'open' CHECK (status IN ('confirmed', 'open', 'high-pitch', 'medium-pitch', 'low-pitch', 'whitespace', 'cancelled')),

  accounts_fees NUMERIC(12,2) DEFAULT 0,
  creative_fees NUMERIC(12,2) DEFAULT 0,
  design_fees NUMERIC(12,2) DEFAULT 0,
  strategic_planning_fees NUMERIC(12,2) DEFAULT 0,
  media_fees NUMERIC(12,2) DEFAULT 0,
  creator_fees NUMERIC(12,2) DEFAULT 0,
  social_fees NUMERIC(12,2) DEFAULT 0,
  omni_fees NUMERIC(12,2) DEFAULT 0,
  digital_fees NUMERIC(12,2) DEFAULT 0,
  finance_fees NUMERIC(12,2) DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  created_by TEXT REFERENCES users(id),
  updated_by TEXT REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_opportunities_project_code ON pipeline_opportunities(project_code);
CREATE INDEX IF NOT EXISTS idx_pipeline_opportunities_client ON pipeline_opportunities(client);
CREATE INDEX IF NOT EXISTS idx_pipeline_opportunities_owner ON pipeline_opportunities(owner);
CREATE INDEX IF NOT EXISTS idx_pipeline_opportunities_status ON pipeline_opportunities(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_opportunities_region ON pipeline_opportunities(region);

-- =====================================================
-- QUOTES
-- =====================================================
CREATE TABLE IF NOT EXISTS quotes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  quote_uid TEXT UNIQUE,
  project_number TEXT NOT NULL,
  client_name TEXT NOT NULL,
  client_category TEXT,
  brand TEXT,
  project_name TEXT NOT NULL,
  brief_date DATE,
  in_market_date DATE,
  project_completion_date DATE,
  total_program_budget NUMERIC(12,2),
  rate_card TEXT,
  currency TEXT DEFAULT 'CAD' CHECK (currency IN ('CAD', 'USD')),
  phases JSONB DEFAULT '[]'::jsonb,
  phase_settings JSONB DEFAULT '{}'::jsonb,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'cancelled')),

  pipeline_opportunity_id UUID REFERENCES pipeline_opportunities(id),

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  created_by TEXT REFERENCES users(id),
  updated_by TEXT REFERENCES users(id),
  full_quote JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_quotes_project_number ON quotes(project_number);
CREATE INDEX IF NOT EXISTS idx_quotes_client_name ON quotes(client_name);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_pipeline_opportunity_id ON quotes(pipeline_opportunity_id);

-- =====================================================
-- EDIT REQUESTS
-- =====================================================
CREATE TABLE IF NOT EXISTS edit_requests (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES pipeline_opportunities(id) ON DELETE CASCADE,
  project_code TEXT NOT NULL,
  field_name TEXT NOT NULL,
  current_value JSONB,
  requested_value JSONB,
  reason TEXT NOT NULL,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),

  requested_by TEXT REFERENCES users(id) NOT NULL,
  requested_at TIMESTAMPTZ DEFAULT now(),
  reviewed_by TEXT REFERENCES users(id),
  reviewed_at TIMESTAMPTZ,
  review_notes TEXT,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edit_requests_project_id ON edit_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_edit_requests_status ON edit_requests(status);
CREATE INDEX IF NOT EXISTS idx_edit_requests_requested_by ON edit_requests(requested_by);

-- =====================================================
-- WORKBACK SECTIONS
-- =====================================================
CREATE TABLE IF NOT EXISTS workback_sections (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
  phase TEXT NOT NULL CHECK (phase IN ('planning', 'production', 'post-production')),
  section_name TEXT NOT NULL,
  section_order INTEGER DEFAULT 0,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workback_sections_quote_id ON workback_sections(quote_id);

-- =====================================================
-- WORKBACK TASKS
-- =====================================================
CREATE TABLE IF NOT EXISTS workback_tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  section_id UUID REFERENCES workback_sections(id) ON DELETE CASCADE,
  task_name TEXT NOT NULL,
  task_order INTEGER DEFAULT 0,
  assigned_to TEXT,
  start_date DATE,
  end_date DATE,
  duration INTEGER,
  status TEXT DEFAULT 'not-started' CHECK (status IN ('not-started', 'in-progress', 'completed', 'blocked')),
  notes TEXT,

  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workback_tasks_section_id ON workback_tasks(section_id);

-- =====================================================
-- AUDIT LOG
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  table_name TEXT NOT NULL,
  record_id UUID NOT NULL,
  action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
  old_values JSONB,
  new_values JSONB,
  user_id TEXT REFERENCES users(id),
  timestamp TIMESTAMPTZ DEFAULT now()
);

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_total_fees()
RETURNS TRIGGER AS $$
BEGIN
  NEW.total_fees = COALESCE(NEW.accounts_fees, 0) +
                   COALESCE(NEW.creative_fees, 0) +
                   COALESCE(NEW.design_fees, 0) +
                   COALESCE(NEW.strategic_planning_fees, 0) +
                   COALESCE(NEW.media_fees, 0) +
                   COALESCE(NEW.creator_fees, 0) +
                   COALESCE(NEW.social_fees, 0) +
                   COALESCE(NEW.omni_fees, 0) +
                   COALESCE(NEW.digital_fees, 0) +
                   COALESCE(NEW.finance_fees, 0);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log (table_name, record_id, action, old_values, user_id)
    VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD), current_setting('app.current_user_id', true));
    RETURN OLD;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log (table_name, record_id, action, old_values, new_values, user_id)
    VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW), current_setting('app.current_user_id', true));
    RETURN NEW;
  ELSIF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log (table_name, record_id, action, new_values, user_id)
    VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW), current_setting('app.current_user_id', true));
    RETURN NEW;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pipeline_opportunities_updated_at BEFORE UPDATE ON pipeline_opportunities
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_edit_requests_updated_at BEFORE UPDATE ON edit_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workback_sections_updated_at BEFORE UPDATE ON workback_sections
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workback_tasks_updated_at BEFORE UPDATE ON workback_tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_overhead_employees_updated_at BEFORE UPDATE ON overhead_employees
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- total_fees calculation
CREATE TRIGGER calculate_pipeline_total_fees BEFORE INSERT OR UPDATE ON pipeline_opportunities
  FOR EACH ROW EXECUTE FUNCTION calculate_total_fees();

-- audit triggers
CREATE TRIGGER audit_pipeline_opportunities AFTER INSERT OR UPDATE OR DELETE ON pipeline_opportunities
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_quotes AFTER INSERT OR UPDATE OR DELETE ON quotes
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_edit_requests AFTER INSERT OR UPDATE OR DELETE ON edit_requests
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_overhead_employees AFTER INSERT OR UPDATE OR DELETE ON overhead_employees
  FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Backfill columns if schema was applied before quote_uid/full_quote additions
ALTER TABLE IF EXISTS quotes ADD COLUMN IF NOT EXISTS quote_uid TEXT UNIQUE;
ALTER TABLE IF EXISTS quotes ADD COLUMN IF NOT EXISTS full_quote JSONB DEFAULT '{}'::jsonb;

-- =====================================================
-- OVERHEAD HELPERS
-- =====================================================
CREATE OR REPLACE FUNCTION get_overhead_employees_with_totals()
RETURNS TABLE (
  id UUID,
  department TEXT,
  employee_name TEXT,
  role TEXT,
  annual_salary NUMERIC(12,2),
  allocation_percent NUMERIC,
  start_date DATE,
  end_date DATE,
  monthly_allocations JSONB,
  total_annual_cost NUMERIC(12,2),
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    oe.id,
    oe.department,
    oe.employee_name,
    oe.role,
    oe.annual_salary,
    oe.allocation_percent,
    oe.start_date,
    oe.end_date,
    oe.monthly_allocations,
    (oe.annual_salary * oe.allocation_percent / 100.0) AS total_annual_cost,
    oe.created_at,
    oe.updated_at
  FROM overhead_employees oe
  ORDER BY oe.department, oe.employee_name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_overhead_totals_by_department_month()
RETURNS TABLE (
  department TEXT,
  month_year TEXT,
  total_amount NUMERIC(12,2),
  employee_count INTEGER
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    oe.department,
    key AS month_year,
    SUM((value::text)::numeric) AS total_amount,
    COUNT(DISTINCT oe.id)::integer AS employee_count
  FROM overhead_employees oe,
       jsonb_each(oe.monthly_allocations)
  WHERE value::text ~ '^\\d+(\\.\\d+)?$'
  GROUP BY oe.department, key
  ORDER BY oe.department, key;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS
-- =====================================================
CREATE OR REPLACE VIEW pipeline_summary AS
SELECT
  status,
  COUNT(*) AS project_count,
  SUM(revenue) AS total_revenue,
  SUM(total_fees) AS total_fees,
  AVG(revenue) AS avg_revenue
FROM pipeline_opportunities
GROUP BY status;

CREATE OR REPLACE VIEW department_fees_summary AS
SELECT 'accounts' AS department, SUM(accounts_fees) AS total_fees, COUNT(CASE WHEN accounts_fees > 0 THEN 1 END) AS projects_with_fees FROM pipeline_opportunities
UNION ALL
SELECT 'creative', SUM(creative_fees), COUNT(CASE WHEN creative_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'design', SUM(design_fees), COUNT(CASE WHEN design_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'strategic_planning', SUM(strategic_planning_fees), COUNT(CASE WHEN strategic_planning_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'media', SUM(media_fees), COUNT(CASE WHEN media_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'creator', SUM(creator_fees), COUNT(CASE WHEN creator_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'social', SUM(social_fees), COUNT(CASE WHEN social_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'omni', SUM(omni_fees), COUNT(CASE WHEN omni_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'digital', SUM(digital_fees), COUNT(CASE WHEN digital_fees > 0 THEN 1 END) FROM pipeline_opportunities
UNION ALL
SELECT 'finance', SUM(finance_fees), COUNT(CASE WHEN finance_fees > 0 THEN 1 END) FROM pipeline_opportunities;

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE pipeline_opportunities IS 'Main table for pipeline opportunities/projects with financial tracking';
COMMENT ON TABLE quotes IS 'Quote management system for project quotes and proposals';
COMMENT ON TABLE edit_requests IS 'Approval workflow for pipeline opportunity edits';
COMMENT ON TABLE workback_sections IS 'Project management workback schedule sections';
COMMENT ON TABLE workback_tasks IS 'Individual tasks within workback schedule sections';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all data changes';
COMMENT ON TABLE overhead_employees IS 'Employee overhead information for pipeline financial tracking and resource planning';
COMMENT ON COLUMN overhead_employees.monthly_allocations IS 'JSON object storing monthly allocation amounts, e.g., {\"2024-01\": 5000, \"2024-02\": 5200}';
COMMENT ON COLUMN quotes.full_quote IS 'Full quote payload from app (nested JSON); use quote_uid to correlate with app IDs';
