-- Overhead Employees Table for Pipeline Management
-- This table stores employee overhead information for pipeline financial tracking

-- =====================================================
-- OVERHEAD EMPLOYEES TABLE
-- =====================================================
CREATE TABLE public.overhead_employees (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    department TEXT NOT NULL,
    employee_name TEXT NOT NULL,
    role TEXT NOT NULL,
    annual_salary DECIMAL(12,2) DEFAULT 0,
    allocation_percent INTEGER DEFAULT 100 CHECK (allocation_percent >= 0 AND allocation_percent <= 100),
    start_date DATE,
    end_date DATE,
    monthly_allocations JSONB DEFAULT '{}'::jsonb, -- Store monthly allocation amounts as JSON
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES public.users(id),
    updated_by UUID REFERENCES public.users(id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================
CREATE INDEX idx_overhead_employees_department ON public.overhead_employees(department);
CREATE INDEX idx_overhead_employees_employee_name ON public.overhead_employees(employee_name);
CREATE INDEX idx_overhead_employees_created_by ON public.overhead_employees(created_by);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================
ALTER TABLE public.overhead_employees ENABLE ROW LEVEL SECURITY;

-- Users can view all overhead employees
CREATE POLICY "Users can view overhead employees" ON public.overhead_employees
    FOR SELECT USING (true);

-- Users can insert overhead employees
CREATE POLICY "Users can insert overhead employees" ON public.overhead_employees
    FOR INSERT WITH CHECK (auth.uid() = created_by);

-- Users can update overhead employees they created or admins can update any
CREATE POLICY "Users can update their overhead employees or admins can update any" ON public.overhead_employees
    FOR UPDATE USING (
        auth.uid() = created_by OR 
        auth.uid() = updated_by OR
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Users can delete overhead employees they created or admins can delete any
CREATE POLICY "Users can delete their overhead employees or admins can delete any" ON public.overhead_employees
    FOR DELETE USING (
        auth.uid() = created_by OR
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Apply updated_at trigger
CREATE TRIGGER update_overhead_employees_updated_at BEFORE UPDATE ON public.overhead_employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply audit trigger
CREATE TRIGGER audit_overhead_employees AFTER INSERT OR UPDATE OR DELETE ON public.overhead_employees
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- =====================================================
-- HELPFUL FUNCTIONS
-- =====================================================

-- Function to get overhead employees with calculated monthly totals
CREATE OR REPLACE FUNCTION get_overhead_employees_with_totals()
RETURNS TABLE (
    id UUID,
    department TEXT,
    employee_name TEXT,
    role TEXT,
    annual_salary DECIMAL(12,2),
    allocation_percent INTEGER,
    start_date DATE,
    end_date DATE,
    monthly_allocations JSONB,
    total_annual_cost DECIMAL(12,2),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
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
        (oe.annual_salary * oe.allocation_percent / 100.0) as total_annual_cost,
        oe.created_at,
        oe.updated_at
    FROM public.overhead_employees oe
    ORDER BY oe.department, oe.employee_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get overhead totals by department and month
CREATE OR REPLACE FUNCTION get_overhead_totals_by_department_month()
RETURNS TABLE (
    department TEXT,
    month_year TEXT,
    total_amount DECIMAL(12,2),
    employee_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        oe.department,
        key as month_year,
        SUM((value::text)::decimal) as total_amount,
        COUNT(DISTINCT oe.id)::integer as employee_count
    FROM public.overhead_employees oe,
         jsonb_each(oe.monthly_allocations)
    WHERE value::text ~ '^\d+(\.\d+)?$' -- Ensure value is numeric
    GROUP BY oe.department, key
    ORDER BY oe.department, key;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS
-- =====================================================
COMMENT ON TABLE public.overhead_employees IS 'Employee overhead information for pipeline financial tracking and resource planning';
COMMENT ON COLUMN public.overhead_employees.monthly_allocations IS 'JSON object storing monthly allocation amounts, e.g., {"2024-01": 5000, "2024-02": 5200}';
COMMENT ON FUNCTION get_overhead_employees_with_totals() IS 'Returns overhead employees with calculated annual cost based on salary and allocation percentage';
COMMENT ON FUNCTION get_overhead_totals_by_department_month() IS 'Returns aggregated overhead totals grouped by department and month';

