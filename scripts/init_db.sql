-- Database initialization for UCL testing

-- Global Contexts table
CREATE TABLE IF NOT EXISTS global_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(255) NOT NULL,
    shared_knowledge JSONB DEFAULT '{}',
    shared_conventions JSONB DEFAULT '{}',
    shared_resources JSONB DEFAULT '[]',
    common_patterns TEXT[] DEFAULT '{}',
    cross_platform_insights JSONB DEFAULT '{}',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Platform Contexts table
CREATE TABLE IF NOT EXISTS platform_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform_type VARCHAR(100) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    global_context_id UUID REFERENCES global_contexts(id),
    platform_specific_data JSONB DEFAULT '{}',
    learned_preferences JSONB DEFAULT '{}',
    interaction_history JSONB DEFAULT '[]',
    custom_prompts TEXT[] DEFAULT '{}',
    platform_conventions JSONB DEFAULT '{}',
    performance_metrics JSONB DEFAULT '{}',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Domain Contexts table (existing, just ensure it exists)
CREATE TABLE IF NOT EXISTS domain_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(255) NOT NULL,
    domain_type VARCHAR(100) NOT NULL,
    technologies TEXT[] DEFAULT '{}',
    file_patterns TEXT[] DEFAULT '{}',
    key_files TEXT[] DEFAULT '{}',
    apis JSONB DEFAULT '[]',
    dependencies TEXT[] DEFAULT '{}',
    conventions JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Contexts table (updated)
CREATE TABLE IF NOT EXISTS project_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    technologies TEXT[] DEFAULT '{}',
    team_members TEXT[] DEFAULT '{}',
    documentation_urls TEXT[] DEFAULT '{}',
    global_context_id UUID REFERENCES global_contexts(id),
    platform_contexts TEXT[] DEFAULT '{}', -- Array of platform context IDs
    global_context JSONB DEFAULT '{}', -- Deprecated field for backward compatibility
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Sessions table (updated)
CREATE TABLE IF NOT EXISTS ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(255) NOT NULL,
    ai_type VARCHAR(100) NOT NULL,
    platform_context_id UUID REFERENCES platform_contexts(id),
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP NULL,
    domains_accessed TEXT[] DEFAULT '{}',
    queries_count INTEGER DEFAULT 0,
    last_query TEXT,
    context_hash VARCHAR(64),
    accessed_global_context BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'
);

-- Context Queries table
CREATE TABLE IF NOT EXISTS context_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id VARCHAR(255) NOT NULL,
    ai_session_id UUID REFERENCES ai_sessions(id),
    query_text TEXT NOT NULL,
    domains_filter TEXT[] DEFAULT '{}',
    response_format VARCHAR(50) DEFAULT 'structured',
    include_history BOOLEAN DEFAULT FALSE,
    max_results INTEGER DEFAULT 100,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Context Responses table
CREATE TABLE IF NOT EXISTS context_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID REFERENCES context_queries(id),
    project_id VARCHAR(255) NOT NULL,
    results JSONB DEFAULT '[]',
    domains_found TEXT[] DEFAULT '{}',
    total_results INTEGER DEFAULT 0,
    processing_time_ms FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_global_contexts_project_id ON global_contexts(project_id);
CREATE INDEX IF NOT EXISTS idx_platform_contexts_project_platform ON platform_contexts(project_id, platform_type);
CREATE INDEX IF NOT EXISTS idx_domain_contexts_project_domain ON domain_contexts(project_id, domain_type);
CREATE INDEX IF NOT EXISTS idx_ai_sessions_project_id ON ai_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_context_queries_project_id ON context_queries(project_id);
CREATE INDEX IF NOT EXISTS idx_context_responses_project_id ON context_responses(project_id);

-- Create a test project
INSERT INTO project_contexts (
    id,
    name,
    description,
    technologies,
    repository_url
) VALUES (
    'test-project-123',
    'Test E-commerce Project',
    'A sample e-commerce application for testing UCL',
    ARRAY['React', 'Node.js', 'PostgreSQL', 'Docker'],
    'https://github.com/test/ecommerce-app'
) ON CONFLICT (id) DO NOTHING;