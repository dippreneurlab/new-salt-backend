-- Salt XC Quote Hub - Supabase Database Setup
-- This SQL script sets up the complete database schema for the Salt XC Quote Hub application

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. USERS TABLE (extends Supabase auth.users)
-- =====================================================
CREATE TABLE public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin', 'pm')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 2. PIPELINE OPPORTUNITIES TABLE
-- =====================================================
CREATE TABLE public.pipeline_opportunities (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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
    revenue DECIMAL(12,2) DEFAULT 0,
    total_fees DECIMAL(12,2) DEFAULT 0,
    status TEXT DEFAULT 'open' CHECK (status IN ('confirmed', 'open', 'high-pitch', 'medium-pitch', 'low-pitch', 'whitespace', 'cancelled')),
    
    -- Department Fees
    accounts_fees DECIMAL(12,2) DEFAULT 0,
    creative_fees DECIMAL(12,2) DEFAULT 0,
    design_fees DECIMAL(12,2) DEFAULT 0,
    strategic_planning_fees DECIMAL(12,2) DEFAULT 0,
    media_fees DECIMAL(12,2) DEFAULT 0,
    creator_fees DECIMAL(12,2) DEFAULT 0,
    social_fees DECIMAL(12,2) DEFAULT 0,
    omni_fees DECIMAL(12,2) DEFAULT 0,
    digital_fees DECIMAL(12,2) DEFAULT 0,
    finance_fees DECIMAL(12,2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES public.users(id),
    updated_by UUID REFERENCES public.users(id)
);

-- =====================================================
-- 3. QUOTES TABLE
-- =====================================================
CREATE TABLE public.quotes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_number TEXT NOT NULL,
    client_name TEXT NOT NULL,
    client_category TEXT,
    brand TEXT,
    project_name TEXT NOT NULL,
    brief_date DATE,
    in_market_date DATE,
    project_completion_date DATE,
    total_program_budget DECIMAL(12,2),
    rate_card TEXT,
    currency TEXT DEFAULT 'CAD' CHECK (currency IN ('CAD', 'USD')),
    phases JSONB DEFAULT '[]'::jsonb,
    phase_settings JSONB DEFAULT '{}'::jsonb,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'in_progress', 'completed', 'cancelled')),
    
    -- Link to pipeline opportunity
    pipeline_opportunity_id UUID REFERENCES public.pipeline_opportunities(id),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES public.users(id),
    updated_by UUID REFERENCES public.users(id)
);

-- =====================================================
-- 4. EDIT REQUESTS TABLE
-- =====================================================
CREATE TABLE public.edit_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id UUID REFERENCES public.pipeline_opportunities(id) ON DELETE CASCADE,
    project_code TEXT NOT NULL,
    field_name TEXT NOT NULL,
    current_value JSONB,
    requested_value JSONB,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    
    -- Request tracking
    requested_by UUID REFERENCES public.users(id) NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_by UUID REFERENCES public.users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 5. PROJECT MANAGEMENT WORKBACK SECTIONS TABLE
-- =====================================================
CREATE TABLE public.workback_sections (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    quote_id UUID REFERENCES public.quotes(id) ON DELETE CASCADE,
    phase TEXT NOT NULL CHECK (phase IN ('planning', 'production', 'post-production')),
    section_name TEXT NOT NULL,
    section_order INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 6. WORKBACK TASKS TABLE
-- =====================================================
CREATE TABLE public.workback_tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    section_id UUID REFERENCES public.workback_sections(id) ON DELETE CASCADE,
    task_name TEXT NOT NULL,
    task_order INTEGER DEFAULT 0,
    assigned_to TEXT,
    start_date DATE,
    end_date DATE,
    duration INTEGER, -- in days
    status TEXT DEFAULT 'not-started' CHECK (status IN ('not-started', 'in-progress', 'completed', 'blocked')),
    notes TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 7. AUDIT LOG TABLE
-- =====================================================
CREATE TABLE public.audit_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    user_id UUID REFERENCES public.users(id),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 8. INDEXES FOR PERFORMANCE
-- =====================================================

-- Pipeline opportunities indexes
CREATE INDEX idx_pipeline_opportunities_project_code ON public.pipeline_opportunities(project_code);
CREATE INDEX idx_pipeline_opportunities_client ON public.pipeline_opportunities(client);
CREATE INDEX idx_pipeline_opportunities_owner ON public.pipeline_opportunities(owner);
CREATE INDEX idx_pipeline_opportunities_status ON public.pipeline_opportunities(status);
CREATE INDEX idx_pipeline_opportunities_region ON public.pipeline_opportunities(region);

-- Quotes indexes
CREATE INDEX idx_quotes_project_number ON public.quotes(project_number);
CREATE INDEX idx_quotes_client_name ON public.quotes(client_name);
CREATE INDEX idx_quotes_status ON public.quotes(status);
CREATE INDEX idx_quotes_pipeline_opportunity_id ON public.quotes(pipeline_opportunity_id);

-- Edit requests indexes
CREATE INDEX idx_edit_requests_project_id ON public.edit_requests(project_id);
CREATE INDEX idx_edit_requests_status ON public.edit_requests(status);
CREATE INDEX idx_edit_requests_requested_by ON public.edit_requests(requested_by);

-- Workback sections and tasks indexes
CREATE INDEX idx_workback_sections_quote_id ON public.workback_sections(quote_id);
CREATE INDEX idx_workback_tasks_section_id ON public.workback_tasks(section_id);

-- =====================================================
-- 9. ROW LEVEL SECURITY (RLS) POLICIES
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pipeline_opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.edit_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workback_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workback_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view their own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Pipeline opportunities policies
CREATE POLICY "Everyone can view pipeline opportunities" ON public.pipeline_opportunities
    FOR SELECT USING (true);

CREATE POLICY "Admins can insert pipeline opportunities" ON public.pipeline_opportunities
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Admins can update pipeline opportunities" ON public.pipeline_opportunities
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Quotes policies
CREATE POLICY "Users can view all quotes" ON public.quotes
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own quotes" ON public.quotes
    FOR INSERT WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Users can update their own quotes" ON public.quotes
    FOR UPDATE USING (auth.uid() = created_by OR auth.uid() = updated_by);

-- Edit requests policies
CREATE POLICY "Users can view all edit requests" ON public.edit_requests
    FOR SELECT USING (true);

CREATE POLICY "Users can create edit requests" ON public.edit_requests
    FOR INSERT WITH CHECK (auth.uid() = requested_by);

CREATE POLICY "Admins can update edit requests" ON public.edit_requests
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- Workback sections and tasks policies
CREATE POLICY "Users can view workback sections for their quotes" ON public.workback_sections
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.quotes 
            WHERE id = quote_id AND (created_by = auth.uid() OR updated_by = auth.uid())
        )
    );

CREATE POLICY "Users can manage workback sections for their quotes" ON public.workback_sections
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.quotes 
            WHERE id = quote_id AND (created_by = auth.uid() OR updated_by = auth.uid())
        )
    );

CREATE POLICY "Users can view workback tasks for their quotes" ON public.workback_tasks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.quotes q
            JOIN public.workback_sections ws ON ws.quote_id = q.id
            WHERE ws.id = section_id AND (q.created_by = auth.uid() OR q.updated_by = auth.uid())
        )
    );

CREATE POLICY "Users can manage workback tasks for their quotes" ON public.workback_tasks
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.quotes q
            JOIN public.workback_sections ws ON ws.quote_id = q.id
            WHERE ws.id = section_id AND (q.created_by = auth.uid() OR q.updated_by = auth.uid())
        )
    );

-- Audit log policies (admin only)
CREATE POLICY "Admins can view audit log" ON public.audit_log
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- =====================================================
-- 10. FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_opportunities_updated_at BEFORE UPDATE ON public.pipeline_opportunities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON public.quotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_edit_requests_updated_at BEFORE UPDATE ON public.edit_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically calculate total_fees from department fees
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
$$ language 'plpgsql';

-- Apply total_fees calculation trigger
CREATE TRIGGER calculate_pipeline_total_fees BEFORE INSERT OR UPDATE ON public.pipeline_opportunities
    FOR EACH ROW EXECUTE FUNCTION calculate_total_fees();

-- Function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO public.audit_log (table_name, record_id, action, old_values, user_id)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD), auth.uid());
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO public.audit_log (table_name, record_id, action, old_values, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW), auth.uid());
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO public.audit_log (table_name, record_id, action, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW), auth.uid());
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Apply audit triggers to key tables
CREATE TRIGGER audit_pipeline_opportunities AFTER INSERT OR UPDATE OR DELETE ON public.pipeline_opportunities
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_quotes AFTER INSERT OR UPDATE OR DELETE ON public.quotes
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_edit_requests AFTER INSERT OR UPDATE OR DELETE ON public.edit_requests
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- =====================================================
-- 11. VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for pipeline summary statistics
CREATE OR REPLACE VIEW pipeline_summary AS
SELECT 
    status,
    COUNT(*) as project_count,
    SUM(revenue) as total_revenue,
    SUM(total_fees) as total_fees,
    AVG(revenue) as avg_revenue
FROM public.pipeline_opportunities
GROUP BY status;

-- View for department fee analysis
CREATE OR REPLACE VIEW department_fees_summary AS
SELECT 
    'accounts' as department,
    SUM(accounts_fees) as total_fees,
    COUNT(CASE WHEN accounts_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'creative' as department,
    SUM(creative_fees) as total_fees,
    COUNT(CASE WHEN creative_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'design' as department,
    SUM(design_fees) as total_fees,
    COUNT(CASE WHEN design_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'strategic_planning' as department,
    SUM(strategic_planning_fees) as total_fees,
    COUNT(CASE WHEN strategic_planning_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'media' as department,
    SUM(media_fees) as total_fees,
    COUNT(CASE WHEN media_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'creator' as department,
    SUM(creator_fees) as total_fees,
    COUNT(CASE WHEN creator_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'social' as department,
    SUM(social_fees) as total_fees,
    COUNT(CASE WHEN social_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'omni' as department,
    SUM(omni_fees) as total_fees,
    COUNT(CASE WHEN omni_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'digital' as department,
    SUM(digital_fees) as total_fees,
    COUNT(CASE WHEN digital_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities
UNION ALL
SELECT 
    'finance' as department,
    SUM(finance_fees) as total_fees,
    COUNT(CASE WHEN finance_fees > 0 THEN 1 END) as projects_with_fees
FROM public.pipeline_opportunities;

-- =====================================================
-- 12. INITIAL DATA SETUP
-- =====================================================

-- Insert admin user (you'll need to replace with actual user ID after authentication)
-- This is just a placeholder - you'll need to get the actual UUID from Supabase auth
/*
INSERT INTO public.users (id, email, full_name, role)
VALUES (
    'your-admin-user-uuid-here',
    'admin@saltxc.com',
    'Admin User',
    'admin'
);
*/

-- =====================================================
-- 13. HELPFUL QUERIES FOR TESTING
-- =====================================================

-- Check if everything was created successfully
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN (
        'users', 'pipeline_opportunities', 'quotes', 'edit_requests', 
        'workback_sections', 'workback_tasks', 'audit_log'
    )
ORDER BY tablename;

-- Check RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies 
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- Test pipeline summary view
-- SELECT * FROM pipeline_summary;

-- Test department fees summary view  
-- SELECT * FROM department_fees_summary ORDER BY department;

COMMENT ON TABLE public.pipeline_opportunities IS 'Main table for pipeline opportunities/projects with financial tracking';
COMMENT ON TABLE public.quotes IS 'Quote management system for project quotes and proposals';
COMMENT ON TABLE public.edit_requests IS 'Approval workflow for pipeline opportunity edits';
COMMENT ON TABLE public.workback_sections IS 'Project management workback schedule sections';
COMMENT ON TABLE public.workback_tasks IS 'Individual tasks within workback schedule sections';
COMMENT ON TABLE public.audit_log IS 'Comprehensive audit trail for all data changes';

