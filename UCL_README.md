# Unified Context Layer (UCL) 🚀

**UCL** es una capa de contexto unificado que permite a múltiples IAs (Claude, ChatGPT, Copilot, etc.) compartir y mantener un contexto coherente del proyecto en tiempo real.

## 🎯 Características Principales

- **Contexto Compartido**: Todas las IAs acceden al mismo contexto del proyecto
- **Multi-Dominio**: Soporte para frontend, backend, diseño, infraestructura, etc.
- **Tiempo Real**: Sincronización automática entre IAs
- **Búsqueda Semántica**: Consultas inteligentes usando embeddings
- **Arquitectura Hexagonal**: Diseño limpio y extensible
- **Analytics**: Métricas de uso y colaboración entre IAs

## 🏗️ Arquitectura

```
ucl/
├── domain/entities/          # Entidades de negocio
├── application/
│   ├── ports/               # Interfaces (Ports)
│   └── services/            # Lógica de negocio
├── driven/db/context/       # Implementación BD (Adapters)
├── driving/api/v1/context/  # API REST (Adapters)
└── config/                  # Configuración e inyección
```

## 🚀 Instalación

1. **Agregar al INSTALLED_APPS**:
```python
# config/settings/base.py
INSTALLED_APPS = [
    # ... apps existentes
    'driven.db.context',
]
```

2. **Ejecutar migraciones**:
```bash
python manage.py makemigrations context
python manage.py migrate
```

3. **La API estará disponible en**:
- Docs: `http://localhost:8000/docs`
- UCL API: `http://localhost:8000/api/v1/ucl/`

## 📖 Guía de Uso

### 1. Crear Proyecto

```bash
curl -X POST "http://localhost:8000/api/v1/ucl/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_metadata": {
      "name": "Mi Proyecto",
      "description": "Proyecto de ejemplo",
      "technologies": ["Python", "FastAPI", "React"],
      "repository_url": "https://github.com/user/repo"
    }
  }'
```

### 2. Agregar Contexto de Dominio

```bash
curl -X POST "http://localhost:8000/api/v1/ucl/projects/{project_id}/domains" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_type": "frontend",
    "technologies": ["React", "TypeScript", "Tailwind"],
    "file_patterns": ["src/**/*.tsx", "src/**/*.ts"],
    "key_files": ["src/App.tsx", "src/main.tsx"],
    "conventions": {
      "naming": "camelCase",
      "component_structure": "functional",
      "state_management": "zustand"
    }
  }'
```

### 3. Iniciar Sesión de IA

```bash
curl -X POST "http://localhost:8000/api/v1/ucl/projects/{project_id}/ai-sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_type": "claude",
    "ai_instance_id": "claude_session_1",
    "metadata": {
      "user": "developer_1",
      "task": "frontend_development"
    }
  }'
```

### 4. Consultar Contexto

```bash
curl -X POST "http://localhost:8000/api/v1/ucl/projects/{project_id}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "componentes de autenticación",
    "domains_filter": ["frontend", "backend"],
    "ai_session_id": "{session_id}",
    "response_format": "structured",
    "max_results": 50
  }'
```

## 🤖 Integración con IAs

### Claude Code

```python
# Integración con Claude Code
import httpx

class ClaudeUCLAdapter:
    def __init__(self, base_url: str, project_id: str):
        self.base_url = base_url
        self.project_id = project_id
        self.session = None

    async def start_session(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ucl/projects/{self.project_id}/ai-sessions",
                json={
                    "ai_type": "claude",
                    "ai_instance_id": "claude_code_session",
                    "metadata": {"integration": "claude_code"}
                }
            )
            self.session = response.json()

    async def query_context(self, query: str, domains: list = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/ucl/projects/{self.project_id}/query",
                json={
                    "query_text": query,
                    "domains_filter": domains or [],
                    "ai_session_id": self.session["id"],
                    "response_format": "markdown"
                }
            )
            return response.json()

# Uso
adapter = ClaudeUCLAdapter("http://localhost:8000", "project_id")
await adapter.start_session()
context = await adapter.query_context("autenticación", ["frontend", "backend"])
```

### ChatGPT Custom GPT

```yaml
# gpt-config.yaml
openapi: 3.0.0
info:
  title: UCL API
  version: 1.0.0
servers:
  - url: http://localhost:8000/api/v1/ucl
paths:
  /projects/{project_id}/query:
    post:
      operationId: query_context
      summary: Query project context
      parameters:
        - name: project_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query_text:
                  type: string
                domains_filter:
                  type: array
                  items:
                    type: string
```

### GitHub Copilot Extension

```javascript
// copilot-extension.js
const vscode = require('vscode');
const axios = require('axios');

class UCLProvider {
    constructor() {
        this.baseUrl = 'http://localhost:8000/api/v1/ucl';
        this.projectId = vscode.workspace.getConfiguration('ucl').get('projectId');
    }

    async getContext(query) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/projects/${this.projectId}/query`,
                {
                    query_text: query,
                    domains_filter: ['frontend', 'backend'],
                    response_format: 'structured'
                }
            );
            return response.data;
        } catch (error) {
            console.error('UCL Error:', error);
            return null;
        }
    }
}

// Registro del provider
function activate(context) {
    const uclProvider = new UCLProvider();

    vscode.languages.registerCompletionItemProvider('*', {
        async provideCompletionItems(document, position) {
            const line = document.lineAt(position).text;
            const context = await uclProvider.getContext(line);

            if (context && context.results.length > 0) {
                return context.results.map(result => {
                    const item = new vscode.CompletionItem(
                        result.title || 'Context Suggestion',
                        vscode.CompletionItemKind.Text
                    );
                    item.detail = 'UCL Context';
                    item.documentation = result.content;
                    return item;
                });
            }
            return [];
        }
    });
}
```

## 📊 Analytics y Métricas

### Analytics del Proyecto

```bash
curl "http://localhost:8000/api/v1/ucl/projects/{project_id}/analytics?days=30"
```

```json
{
  "queries": {
    "popular": [
      {"query_text": "autenticación", "count": 15},
      {"query_text": "componentes", "count": 12}
    ],
    "total_recent": 45
  },
  "sessions": {
    "total_recent": 8,
    "by_ai_type": {"claude": 3, "chatgpt": 3, "copilot": 2},
    "active": 2
  },
  "domains": {
    "total": 4,
    "types": ["frontend", "backend", "design", "infrastructure"]
  }
}
```

### Analytics de IA

```bash
curl "http://localhost:8000/api/v1/ucl/projects/{project_id}/ai-analytics?ai_type=claude&days=7"
```

### Insights de Colaboración

```bash
curl "http://localhost:8000/api/v1/ucl/projects/{project_id}/collaboration-insights?days=7"
```

## 🔧 Configuración Avanzada

### Personalización de Dominios

```python
# Agregar dominio personalizado
DOMAIN_TYPES = [
    ('mobile_ios', 'Mobile iOS'),
    ('mobile_android', 'Mobile Android'),
    ('blockchain', 'Blockchain'),
    ('ai_ml', 'AI/ML'),
]
```

### Rate Limiting

```python
# config/settings/base.py
UCL_SETTINGS = {
    'RATE_LIMITS': {
        'claude': {'requests_per_minute': 100},
        'chatgpt': {'requests_per_minute': 60},
        'copilot': {'requests_per_minute': 120},
    },
    'VECTOR_STORE': {
        'enabled': True,
        'similarity_threshold': 0.7
    }
}
```

### Webhooks para Notificaciones

```python
# Configurar webhook para recibir actualizaciones
webhook_config = {
    "url": "https://your-app.com/ucl-webhook",
    "events": ["context_updated", "new_session", "query_completed"],
    "domains": ["frontend", "backend"]
}
```

## 🚀 Roadmap

### Fase 1 ✅ (Completada)
- [x] Arquitectura hexagonal base
- [x] Modelos de dominio
- [x] API REST completa
- [x] Persistencia con Django
- [x] Dependency injection

### Fase 2 🔄 (En Desarrollo)
- [ ] Vector store con ChromaDB
- [ ] Indexación automática de archivos
- [ ] WebSocket para tiempo real
- [ ] CLI tool para gestión

### Fase 3 🔮 (Planificada)
- [ ] Extensions para IDEs
- [ ] Integración con Git hooks
- [ ] Dashboard web para analytics
- [ ] Exportación de contexto

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

- **Issues**: [GitHub Issues](https://github.com/your-org/ucl/issues)
- **Documentación**: [Wiki](https://github.com/your-org/ucl/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/ucl/discussions)

---

**UCL** - Unificando el contexto para una colaboración IA más inteligente 🤖✨