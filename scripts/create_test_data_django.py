#!/usr/bin/env python
"""Create test data using Django models"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from driven.db.context.models import (
    ProjectContextDBO,
    DomainContextDBO,
    AISessionDBO
)
from datetime import datetime

def create_test_data():
    """Create test data using Django ORM"""

    print("📁 Creating test project...")

    # Create or update project
    project, created = ProjectContextDBO.objects.update_or_create(
        name="Test E-commerce Project",
        defaults={
            'description': 'A sample e-commerce application for testing UCL',
            'version': '1.0.0',
            'repository_url': 'https://github.com/test/ecommerce-app',
            'technologies': ['React', 'Node.js', 'PostgreSQL', 'Docker'],
            'team_members': ['developer1', 'developer2'],
            'documentation_urls': ['https://docs.example.com'],
            'global_context': {
                'project_info': {
                    'name': 'Test E-commerce Project',
                    'description': 'A sample e-commerce application',
                    'technologies': ['React', 'Node.js', 'PostgreSQL']
                },
                'architecture': {
                    'pattern': 'microservices',
                    'frontend': 'React with TypeScript',
                    'backend': 'Node.js with Express'
                },
                'conventions': {
                    'code_style': 'ESLint + Prettier',
                    'naming': 'camelCase for variables',
                    'testing': 'Jest + Testing Library'
                }
            }
        }
    )

    action = "Created" if created else "Updated"
    print(f"✓ {action} project: {project.name} ({project.id})")

    # Create domains
    print("\n📦 Creating domain contexts...")

    domains_data = [
        {
            'domain_type': 'frontend',
            'technologies': ['React', 'TypeScript', 'Tailwind CSS'],
            'file_patterns': ['src/**/*.tsx', 'src/**/*.ts', 'src/**/*.css'],
            'key_files': ['src/App.tsx', 'src/index.tsx', 'package.json'],
            'apis': [],
            'dependencies': ['react', 'typescript', 'tailwindcss'],
            'conventions': {
                'component_style': 'functional_components',
                'state_management': 'React_Context_API',
                'styling': 'Tailwind_utility_classes'
            },
            'metadata': {'framework_version': '18.2.0'}
        },
        {
            'domain_type': 'backend',
            'technologies': ['Node.js', 'Express', 'Prisma'],
            'file_patterns': ['server/**/*.js', 'server/**/*.ts'],
            'key_files': ['server/index.ts', 'server/routes/*.ts'],
            'apis': ['/api/v1/users', '/api/v1/products', '/api/v1/orders'],
            'dependencies': ['express', 'prisma', 'jsonwebtoken'],
            'conventions': {
                'routing': 'RESTful_API',
                'authentication': 'JWT_tokens',
                'error_handling': 'centralized_middleware'
            },
            'metadata': {'node_version': '18.16.0'}
        },
        {
            'domain_type': 'database',
            'technologies': ['PostgreSQL', 'Prisma ORM'],
            'file_patterns': ['prisma/**/*.prisma', 'migrations/**/*.sql'],
            'key_files': ['prisma/schema.prisma'],
            'apis': [],
            'dependencies': ['@prisma/client'],
            'conventions': {
                'naming': 'snake_case',
                'migrations': 'automatic_via_prisma'
            },
            'metadata': {'postgres_version': '15'}
        }
    ]

    for domain_data in domains_data:
        domain, created = DomainContextDBO.objects.update_or_create(
            project=project,
            domain_type=domain_data['domain_type'],
            defaults={k: v for k, v in domain_data.items() if k != 'domain_type'}
        )
        action = "Created" if created else "Updated"
        print(f"  ✓ {action} domain: {domain.domain_type}")

    # Create AI sessions
    print("\n🤖 Creating AI sessions...")

    ai_types = ['claude', 'chatgpt']
    for ai_type in ai_types:
        session, created = AISessionDBO.objects.get_or_create(
            project=project,
            ai_type=ai_type,
            ai_instance_id=f'test-{ai_type}-session',
            defaults={
                'domains_accessed': ['frontend', 'backend'],
                'queries_count': 0,
                'metadata': {
                    'preferred_style': 'detailed' if ai_type == 'claude' else 'conversational'
                }
            }
        )
        action = "Created" if created else "Found existing"
        print(f"  ✓ {action} AI session: {ai_type} ({session.id})")

    print("\n" + "="*60)
    print("✅ TEST DATA CREATED SUCCESSFULLY")
    print("="*60)
    print(f"\nProject ID: {project.id}")
    print(f"Project Name: {project.name}")
    print(f"Domains: {DomainContextDBO.objects.filter(project=project).count()}")
    print(f"AI Sessions: {AISessionDBO.objects.filter(project=project).count()}")
    print("\nYou can now run: python test_client.py")

if __name__ == '__main__':
    try:
        create_test_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)