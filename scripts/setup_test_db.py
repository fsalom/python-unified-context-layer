#!/usr/bin/env python3
"""Setup test database with sample data"""
import asyncio
import asyncpg
import json
from datetime import datetime
from uuid import uuid4

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "ucl",
    "password": "ucl",
    "database": "ucl"
}

async def setup_test_data():
    """Set up test data in the database"""
    print("🗄️ Connecting to database...")

    conn = await asyncpg.connect(**DB_CONFIG)

    try:
        # Create test project with global context
        project_id = "test-project-123"
        global_context_id = str(uuid4())

        print("📁 Creating test project...")

        # Insert global context first
        await conn.execute("""
            INSERT INTO global_contexts (
                id, project_id, shared_knowledge, shared_conventions,
                common_patterns, version
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET
                shared_knowledge = EXCLUDED.shared_knowledge,
                shared_conventions = EXCLUDED.shared_conventions,
                common_patterns = EXCLUDED.common_patterns,
                last_updated = CURRENT_TIMESTAMP
        """,
        global_context_id,
        project_id,
        json.dumps({
            "project_info": {
                "name": "Test E-commerce Project",
                "description": "A sample e-commerce application for testing UCL",
                "technologies": ["React", "Node.js", "PostgreSQL", "Docker"],
                "repository_url": "https://github.com/test/ecommerce-app"
            },
            "architecture": {
                "pattern": "microservices",
                "frontend": "React with TypeScript",
                "backend": "Node.js with Express",
                "database": "PostgreSQL with Prisma ORM"
            },
            "business_rules": {
                "payment_providers": ["Stripe", "PayPal"],
                "shipping_zones": ["US", "EU", "Canada"],
                "tax_calculation": "automated_by_region"
            }
        }),
        json.dumps({
            "code_style": {
                "linting": "ESLint + Prettier",
                "naming": "camelCase for variables, PascalCase for components",
                "file_structure": "feature-based organization"
            },
            "api_design": {
                "versioning": "/api/v1/",
                "error_format": "RFC 7807",
                "authentication": "JWT tokens"
            },
            "testing": {
                "framework": "Jest + Testing Library",
                "coverage_threshold": 80,
                "e2e": "Playwright"
            }
        }),
        ["Repository pattern for data access", "Event-driven architecture", "CQRS pattern"],
        1
        )

        # Update project context with global context reference
        await conn.execute("""
            UPDATE project_contexts
            SET global_context_id = $1, last_updated = CURRENT_TIMESTAMP
            WHERE id = $2
        """, global_context_id, project_id)

        print("🌍 Created global context")

        # Create sample platform contexts
        platforms = [
            {
                "type": "claude",
                "data": {
                    "preferred_response_style": "detailed_with_examples",
                    "code_explanation_level": "intermediate",
                    "error_handling_approach": "defensive_programming"
                },
                "preferences": {
                    "likes_typescript_strict_mode": True,
                    "prefers_functional_components": True,
                    "documentation_style": "JSDoc_with_examples"
                },
                "prompts": [
                    "Always include error handling in code examples",
                    "Provide TypeScript interfaces when relevant",
                    "Suggest testing approaches for new features"
                ]
            },
            {
                "type": "chatgpt",
                "data": {
                    "preferred_response_style": "conversational_with_examples",
                    "code_explanation_level": "beginner_friendly",
                    "error_handling_approach": "try_catch_with_explanations"
                },
                "preferences": {
                    "likes_step_by_step_guides": True,
                    "prefers_visual_explanations": True,
                    "documentation_style": "markdown_with_diagrams"
                },
                "prompts": [
                    "Break down complex tasks into simple steps",
                    "Provide visual diagrams when possible",
                    "Include beginner-friendly explanations"
                ]
            }
        ]

        platform_context_ids = []
        for platform in platforms:
            platform_id = str(uuid4())
            platform_context_ids.append(platform_id)

            await conn.execute("""
                INSERT INTO platform_contexts (
                    id, platform_type, project_id, global_context_id,
                    platform_specific_data, learned_preferences, custom_prompts,
                    version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            platform_id,
            platform["type"],
            project_id,
            global_context_id,
            json.dumps(platform["data"]),
            json.dumps(platform["preferences"]),
            platform["prompts"],
            1
            )

            print(f"🤖 Created {platform['type']} platform context")

        # Create sample domain contexts
        domains = [
            {
                "type": "frontend",
                "technologies": ["React", "TypeScript", "Tailwind CSS", "Redux Toolkit"],
                "file_patterns": ["src/components/**/*.tsx", "src/pages/**/*.tsx", "src/hooks/**/*.ts"],
                "key_files": ["src/App.tsx", "src/index.tsx", "package.json"],
                "conventions": {
                    "component_naming": "PascalCase",
                    "file_naming": "kebab-case",
                    "state_management": "Redux Toolkit Query",
                    "styling": "Tailwind CSS with component variants"
                }
            },
            {
                "type": "backend",
                "technologies": ["Node.js", "Express", "TypeScript", "Prisma", "PostgreSQL"],
                "file_patterns": ["src/routes/**/*.ts", "src/controllers/**/*.ts", "src/services/**/*.ts"],
                "key_files": ["src/server.ts", "src/app.ts", "prisma/schema.prisma"],
                "conventions": {
                    "api_versioning": "/api/v1/",
                    "error_handling": "centralized middleware",
                    "validation": "Joi schemas",
                    "authentication": "JWT with refresh tokens"
                }
            },
            {
                "type": "database",
                "technologies": ["PostgreSQL", "Prisma", "Redis"],
                "file_patterns": ["prisma/**/*.prisma", "migrations/**/*.sql"],
                "key_files": ["prisma/schema.prisma", "docker-compose.yml"],
                "conventions": {
                    "naming": "snake_case for tables and columns",
                    "indexing": "automatic for foreign keys and search fields",
                    "migrations": "descriptive names with timestamps"
                }
            }
        ]

        for domain in domains:
            domain_id = str(uuid4())

            await conn.execute("""
                INSERT INTO domain_contexts (
                    id, project_id, domain_type, technologies, file_patterns,
                    key_files, conventions, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            domain_id,
            project_id,
            domain["type"],
            domain["technologies"],
            domain["file_patterns"],
            domain["key_files"],
            json.dumps(domain["conventions"]),
            json.dumps({"created_by": "setup_script", "sample_data": True})
            )

            print(f"📦 Created {domain['type']} domain context")

        print("✅ Test data setup complete!")
        print(f"📋 Project ID: {project_id}")
        print(f"🌍 Global Context ID: {global_context_id}")
        print(f"🤖 Platform Contexts: {len(platforms)} created")
        print(f"📦 Domain Contexts: {len(domains)} created")

    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_test_data())