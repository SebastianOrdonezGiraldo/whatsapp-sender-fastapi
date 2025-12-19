# WhatsApp Sender FastAPI Backend

Backend API para sistema de envío masivo de mensajes de WhatsApp usando WhatsApp Cloud API de Meta.

## 🚀 Stack Tecnológico

- **FastAPI** - Framework web async
- **PostgreSQL** - Base de datos
- **Redis + RQ** - Cola de tareas y procesamiento en background
- **SQLAlchemy (async)** - ORM
- **Alembic** - Migraciones de base de datos
- **Pydantic** - Validación de datos
- **Server-Sent Events (SSE)** - Updates en tiempo real

## 📋 Prerrequisitos

- Python 3.11+
- Poetry (gestor de dependencias)
- PostgreSQL 15+
- Redis 7+
- Docker y Docker Compose (opcional, para desarrollo)

## 🛠️ Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd whatsapp-sender-fastapi
```

### 2. Instalar dependencias

```bash
poetry install
```

O si prefieres usar pip:

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Application
APP_NAME=WhatsApp Sender API
DEBUG=True
SECRET_KEY=tu-secret-key-super-segura-aqui

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=whatsapp_sender
DB_USER=postgres
DB_PASSWORD=postgres123

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# WhatsApp API (Meta)
WHATSAPP_ACCESS_TOKEN=tu-access-token-de-meta
WHATSAPP_PHONE_NUMBER_ID=tu-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=tu-waba-id

# Campaign Settings
CAMPAIGN_MAX_RECIPIENTS=1000
CAMPAIGN_BATCH_SIZE=50
CAMPAIGN_DELAY_BETWEEN_BATCHES=60

# Retry Settings
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=5
RETRY_BACKOFF_MULTIPLIER=2

# Cost Settings
COST_PER_MESSAGE=0.005
CURRENCY=USD

# CORS (ajusta según tu frontend)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

### 4. Iniciar servicios con Docker Compose

```bash
docker-compose up -d
```

Esto iniciará PostgreSQL y Redis.

### 5. Ejecutar migraciones

```bash
alembic upgrade head
```

### 6. Iniciar el servidor de desarrollo

```bash
# Con Poetry
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# O directamente
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

### 7. Iniciar workers (en una terminal separada)

Los workers procesan las tareas en background (envío de mensajes):

```bash
# Con Poetry
poetry run rq worker --with-scheduler

# O directamente
rq worker --with-scheduler
```

**Importante:** Necesitas tener al menos un worker corriendo para que las campañas procesen los mensajes.

## 📚 Documentación de la API

Una vez que el servidor esté corriendo, puedes acceder a:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## 🔌 Endpoints Principales

### Campañas

- `GET /api/v1/campaigns` - Listar campañas
- `POST /api/v1/campaigns` - Crear campaña
- `GET /api/v1/campaigns/{id}` - Obtener campaña
- `PUT /api/v1/campaigns/{id}` - Actualizar campaña
- `DELETE /api/v1/campaigns/{id}` - Eliminar campaña
- `POST /api/v1/campaigns/{id}/start` - Iniciar campaña
- `POST /api/v1/campaigns/{id}/pause` - Pausar campaña
- `POST /api/v1/campaigns/{id}/resume` - Reanudar campaña
- `POST /api/v1/campaigns/{id}/cancel` - Cancelar campaña
- `GET /api/v1/campaigns/{id}/stats` - Estadísticas de campaña
- `POST /api/v1/campaigns/{id}/upload-recipients` - Subir CSV con destinatarios

### Plantillas

- `GET /api/v1/templates` - Listar plantillas de Meta
- `GET /api/v1/templates/{name}` - Obtener plantilla específica
- `POST /api/v1/templates/send` - Enviar mensaje de prueba

### Eventos en Tiempo Real (SSE)

- `GET /api/v1/events/campaigns/{id}/stream` - Stream de actualizaciones de una campaña
- `GET /api/v1/events/campaigns/stream` - Stream de todas las campañas

### Webhooks

- `GET /api/v1/webhooks/whatsapp` - Verificación de webhook (Meta)
- `POST /api/v1/webhooks/whatsapp` - Recibir actualizaciones de WhatsApp

## 🔄 Flujo de Trabajo

1. **Obtener plantillas disponibles:**
   ```bash
   GET /api/v1/templates
   ```

2. **Crear una campaña:**
   ```bash
   POST /api/v1/campaigns
   {
     "name": "Mi Campaña",
     "template_name": "bienvenida",
     "template_language": "es",
     "description": "Campaña de bienvenida"
   }
   ```

3. **Subir CSV con destinatarios:**
   ```bash
   POST /api/v1/campaigns/{id}/upload-recipients
   Content-Type: multipart/form-data
   file: [archivo.csv]
   ```

   Formato CSV:
   ```csv
   Recipient-Phone-Number,variable_1,variable_2
   +573001234567,Juan,Pérez
   +573001234568,María,García
   ```

4. **Iniciar la campaña:**
   ```bash
   POST /api/v1/campaigns/{id}/start
   ```

5. **Monitorear en tiempo real (SSE):**
   ```javascript
   const eventSource = new EventSource('http://localhost:8000/api/v1/events/campaigns/1/stream');
   
   eventSource.onmessage = (event) => {
     const data = JSON.parse(event.data);
     console.log('Update:', data);
   };
   ```

## 🧪 Testing

```bash
# Ejecutar tests
poetry run pytest

# Con cobertura
poetry run pytest --cov=app --cov-report=html
```

## 📝 Notas Importantes

### Configuración de Meta WhatsApp

1. Obtén tus credenciales de [Meta for Developers](https://developers.facebook.com/)
2. Configura el webhook en Meta Developer Console:
   - URL: `https://tu-dominio.com/api/v1/webhooks/whatsapp`
   - Verify Token: (configúralo en el código o variables de entorno)
   - Suscríbete a los eventos: `messages`, `message_status`

### Workers

- Los workers procesan las tareas en background
- Puedes ejecutar múltiples workers para mayor throughput
- Los workers se conectan automáticamente a Redis

### CORS

Asegúrate de configurar `CORS_ORIGINS` en el `.env` con las URLs de tu frontend.

## 🐛 Troubleshooting

### Error: "Template not found"
- Verifica que la plantilla existe en Meta
- Verifica que la plantilla está en estado "APPROVED"
- Verifica el nombre y lenguaje de la plantilla

### Error: "Campaign cannot be started"
- Asegúrate de haber subido un CSV con destinatarios
- Verifica que la campaña está en estado DRAFT o SCHEDULED

### Los mensajes no se envían
- Verifica que hay un worker corriendo (`rq worker`)
- Verifica la conexión a Redis
- Verifica las credenciales de WhatsApp en el `.env`

## 📖 Arquitectura

Ver `docs/architecture.md` para más detalles sobre la arquitectura del sistema.

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.
