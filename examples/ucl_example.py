"""
Ejemplo completo de uso del Unified Context Layer (UCL)
"""
import asyncio
import httpx
from typing import Dict, Any, List


class UCLClient:
    """Cliente Python para interactuar con UCL"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def close(self):
        """Cerrar cliente"""
        await self.client.aclose()

    # Project Context Methods

    async def create_project(
        self,
        name: str,
        description: str = None,
        technologies: List[str] = None,
        repository_url: str = None
    ) -> Dict[str, Any]:
        """Crear nuevo proyecto"""
        payload = {
            "project_metadata": {
                "name": name,
                "description": description,
                "technologies": technologies or [],
                "repository_url": repository_url
            }
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/ucl/projects",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Obtener proyecto por ID"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/ucl/projects/{project_id}"
        )
        response.raise_for_status()
        return response.json()

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Listar todos los proyectos"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/ucl/projects"
        )
        response.raise_for_status()
        return response.json()

    # Domain Context Methods

    async def add_domain(
        self,
        project_id: str,
        domain_type: str,
        technologies: List[str] = None,
        file_patterns: List[str] = None,
        conventions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Agregar contexto de dominio"""
        payload = {
            "domain_type": domain_type,
            "technologies": technologies or [],
            "file_patterns": file_patterns or [],
            "conventions": conventions or {}
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/ucl/projects/{project_id}/domains",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def get_domains(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtener dominios del proyecto"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/ucl/projects/{project_id}/domains"
        )
        response.raise_for_status()
        return response.json()

    # AI Session Methods

    async def start_ai_session(
        self,
        project_id: str,
        ai_type: str,
        ai_instance_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Iniciar sesión de IA"""
        payload = {
            "ai_type": ai_type,
            "ai_instance_id": ai_instance_id,
            "metadata": metadata or {}
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/ucl/projects/{project_id}/ai-sessions",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def end_ai_session(self, session_id: str) -> Dict[str, Any]:
        """Finalizar sesión de IA"""
        response = await self.client.patch(
            f"{self.base_url}/api/v1/ucl/ai-sessions/{session_id}/end"
        )
        response.raise_for_status()
        return response.json()

    # Context Query Methods

    async def query_context(
        self,
        project_id: str,
        query_text: str,
        domains_filter: List[str] = None,
        ai_session_id: str = None,
        response_format: str = "structured",
        max_results: int = 100
    ) -> Dict[str, Any]:
        """Consultar contexto del proyecto"""
        payload = {
            "query_text": query_text,
            "domains_filter": domains_filter or [],
            "ai_session_id": ai_session_id,
            "response_format": response_format,
            "max_results": max_results
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/ucl/projects/{project_id}/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    # Analytics Methods

    async def get_project_analytics(
        self,
        project_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtener analytics del proyecto"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/ucl/projects/{project_id}/analytics?days={days}"
        )
        response.raise_for_status()
        return response.json()


class AIAgent:
    """Clase base para agentes de IA que usan UCL"""

    def __init__(self, ai_type: str, ucl_client: UCLClient):
        self.ai_type = ai_type
        self.ucl = ucl_client
        self.session_id = None
        self.project_id = None

    async def connect_to_project(self, project_id: str, instance_id: str = None):
        """Conectar agente a un proyecto"""
        self.project_id = project_id
        session = await self.ucl.start_ai_session(
            project_id=project_id,
            ai_type=self.ai_type,
            ai_instance_id=instance_id or f"{self.ai_type}_agent",
            metadata={"agent_version": "1.0"}
        )
        self.session_id = session["id"]
        print(f"✅ {self.ai_type} conectado al proyecto {project_id}")

    async def query_context(self, query: str, domains: List[str] = None):
        """Consultar contexto con la sesión activa"""
        if not self.session_id:
            raise ValueError("Agent not connected to project")

        response = await self.ucl.query_context(
            project_id=self.project_id,
            query_text=query,
            domains_filter=domains,
            ai_session_id=self.session_id
        )
        return response

    async def disconnect(self):
        """Desconectar agente"""
        if self.session_id:
            await self.ucl.end_ai_session(self.session_id)
            print(f"👋 {self.ai_type} desconectado")


async def main_example():
    """Ejemplo principal de uso de UCL"""
    print("🚀 Iniciando ejemplo de UCL")

    # Crear cliente UCL
    ucl = UCLClient()

    try:
        # 1. Crear proyecto
        print("\n📁 Creando proyecto...")
        project = await ucl.create_project(
            name="E-commerce Platform",
            description="Plataforma de comercio electrónico moderna",
            technologies=["Python", "FastAPI", "React", "TypeScript", "PostgreSQL"],
            repository_url="https://github.com/company/ecommerce-platform"
        )
        project_id = project["id"]
        print(f"✅ Proyecto creado: {project['project_metadata']['name']}")

        # 2. Agregar contextos de dominio
        print("\n🏗️ Agregando contextos de dominio...")

        # Frontend
        await ucl.add_domain(
            project_id=project_id,
            domain_type="frontend",
            technologies=["React", "TypeScript", "Tailwind CSS", "Zustand"],
            file_patterns=["src/components/**/*.tsx", "src/pages/**/*.tsx"],
            conventions={
                "naming": "PascalCase for components",
                "file_structure": "feature-based",
                "state_management": "zustand",
                "styling": "tailwind-css"
            }
        )

        # Backend
        await ucl.add_domain(
            project_id=project_id,
            domain_type="backend",
            technologies=["Python", "FastAPI", "SQLAlchemy", "Pydantic"],
            file_patterns=["api/**/*.py", "services/**/*.py", "models/**/*.py"],
            conventions={
                "naming": "snake_case",
                "architecture": "hexagonal",
                "api_versioning": "path-based",
                "validation": "pydantic"
            }
        )

        # Database
        await ucl.add_domain(
            project_id=project_id,
            domain_type="database",
            technologies=["PostgreSQL", "Alembic", "Redis"],
            file_patterns=["migrations/**/*.py", "schemas/**/*.sql"],
            conventions={
                "naming": "snake_case",
                "migrations": "alembic",
                "caching": "redis"
            }
        )

        print("✅ Dominios agregados")

        # 3. Crear agentes de IA
        print("\n🤖 Conectando agentes de IA...")

        claude_agent = AIAgent("claude", ucl)
        chatgpt_agent = AIAgent("chatgpt", ucl)

        await claude_agent.connect_to_project(project_id, "claude_frontend_specialist")
        await chatgpt_agent.connect_to_project(project_id, "chatgpt_backend_specialist")

        # 4. Consultas de contexto
        print("\n🔍 Realizando consultas de contexto...")

        # Claude consulta sobre frontend
        frontend_context = await claude_agent.query_context(
            "componentes de autenticación y login",
            domains=["frontend"]
        )
        print(f"🎨 Claude encontró {frontend_context['total_results']} resultados sobre frontend")

        # ChatGPT consulta sobre backend
        backend_context = await chatgpt_agent.query_context(
            "API endpoints para autenticación",
            domains=["backend", "database"]
        )
        print(f"⚙️ ChatGPT encontró {backend_context['total_results']} resultados sobre backend")

        # Consulta multi-dominio
        full_context = await claude_agent.query_context(
            "flujo completo de autenticación",
            domains=["frontend", "backend", "database"]
        )
        print(f"🔄 Consulta multi-dominio: {full_context['total_results']} resultados")

        # 5. Simular actividad adicional
        print("\n📊 Simulando actividad adicional...")

        queries = [
            "carrito de compras",
            "procesamiento de pagos",
            "gestión de inventario",
            "notificaciones push",
            "sistema de reviews"
        ]

        for query in queries:
            if len(query) % 2 == 0:
                await claude_agent.query_context(query)
            else:
                await chatgpt_agent.query_context(query)

        # 6. Obtener analytics
        print("\n📈 Obteniendo analytics...")

        analytics = await ucl.get_project_analytics(project_id, days=1)
        print(f"📊 Analytics del proyecto:")
        print(f"   - Sesiones activas: {analytics['sessions']['active']}")
        print(f"   - Consultas por IA: {analytics['sessions']['by_ai_type']}")
        print(f"   - Dominios configurados: {len(analytics['domains']['types'])}")

        # 7. Desconectar agentes
        print("\n👋 Desconectando agentes...")
        await claude_agent.disconnect()
        await chatgpt_agent.disconnect()

        print("\n🎉 Ejemplo completado exitosamente!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await ucl.close()


async def multi_ai_collaboration_example():
    """Ejemplo de colaboración entre múltiples IAs"""
    print("\n🤝 Ejemplo de colaboración multi-IA")

    ucl = UCLClient()

    try:
        # Obtener proyecto existente o crear uno nuevo
        projects = await ucl.list_projects()
        if projects:
            project_id = projects[0]["id"]
            print(f"📁 Usando proyecto existente: {projects[0]['project_metadata']['name']}")
        else:
            project = await ucl.create_project("Collaboration Demo", "Demo de colaboración")
            project_id = project["id"]

        # Crear múltiples agentes
        agents = [
            AIAgent("claude", ucl),
            AIAgent("chatgpt", ucl),
            AIAgent("copilot", ucl),
        ]

        # Conectar todos los agentes
        for i, agent in enumerate(agents):
            await agent.connect_to_project(
                project_id,
                f"{agent.ai_type}_collaborator_{i+1}"
            )

        # Simular colaboración secuencial
        tasks = [
            ("claude", "diseñar componente de login", ["frontend"]),
            ("chatgpt", "crear API para autenticación", ["backend"]),
            ("copilot", "implementar validaciones", ["frontend", "backend"]),
            ("claude", "agregar tests unitarios", ["frontend"]),
            ("chatgpt", "documentar API endpoints", ["backend"]),
        ]

        print("\n🔄 Simulando colaboración secuencial...")
        for ai_type, task, domains in tasks:
            agent = next(a for a in agents if a.ai_type == ai_type)
            result = await agent.query_context(task, domains)
            print(f"   {ai_type}: {task} -> {result['total_results']} resultados")

        # Obtener analytics de colaboración
        analytics = await ucl.get_project_analytics(project_id)
        print(f"\n📊 Resultados de colaboración:")
        print(f"   - IAs participantes: {list(analytics['sessions']['by_ai_type'].keys())}")
        print(f"   - Total de consultas: {analytics['queries']['total_recent']}")

        # Desconectar todos
        for agent in agents:
            await agent.disconnect()

    finally:
        await ucl.close()


if __name__ == "__main__":
    print("🌟 UCL - Unified Context Layer Examples")
    print("=" * 50)

    # Ejecutar ejemplo principal
    asyncio.run(main_example())

    # Ejecutar ejemplo de colaboración
    asyncio.run(multi_ai_collaboration_example())

    print("\n✨ Todos los ejemplos completados!")