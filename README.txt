# 🚀 PNPtv Bot - Guía de Deployment

Esta guía te ayudará a deploear el bot PNPtv en Railway (recomendado) o cualquier otra plataforma.

## 📋 Requisitos Previos

### 1. Cuentas Necesarias
- ✅ **Telegram**: Bot token de @BotFather
- ✅ **Railway**: Cuenta en [railway.app](https://railway.app)
- ✅ **Bold.co**: API keys para pagos
- ✅ **Webex**: Access token para videollamadas
- ✅ **PostgreSQL**: Base de datos (Railway lo provee automáticamente)

### 2. Información Requerida
- 📱 **Canales/Grupos de Telegram**: IDs de los canales premium
- 👥 **Administradores**: User IDs de los administradores
- 🔐 **Claves de API**: Bold, Webex, etc.

---

## 🎯 Deployment en Railway (Recomendado)

### Paso 1: Preparar el Código

```bash
# Clonar o descargar el código del bot
git clone https://github.com/tu-repo/pnptv-bot.git
cd pnptv-bot

# Verificar que todos los archivos estén presentes
ls -la deploy/
```

### Paso 2: Crear Proyecto en Railway

1. Ve a [railway.app](https://railway.app) y crea una cuenta
2. Haz clic en "New Project"
3. Selecciona "Deploy from GitHub repo" o "Empty Project"
4. Si usas GitHub, conecta tu repositorio

### Paso 3: Configurar Variables de Entorno

En el dashboard de Railway, ve a **Variables** y configura:

#### 🤖 Bot Básico
```env
BOT_TOKEN=tu_bot_token_aqui
BOT_USERNAME=tu_bot_username
BOT_MODE=webhook
WEBHOOK_PORT=8000
```

#### 👥 Administración
```env
ADMIN_USER_IDS=123456789,987654321
ADMIN_EMAIL=admin@pnptv.com
```

#### 🏠 Canales de Telegram
```env
VIP_CHANNEL_ID=-1001234567890
MONTHLY_GROUP_ID=-1001234567891
VIP_GROUP_ID=-1001234567892
ANNUAL_EXCLUSIVE_ID=-1001234567893
LIFETIME_LOUNGE_ID=-1001234567894
```

#### 💳 Pagos Bold.co
```env
BOLD_API_KEY=tu_bold_api_key
BOLD_API_SECRET=tu_bold_api_secret
BOLD_IDENTITY_KEY=tu_bold_identity_key
BOLD_WEBHOOK_SECRET=tu_bold_webhook_secret
```

#### 📹 Webex
```env
WEBEX_ACCESS_TOKEN=tu_webex_token
WEBEX_CLIENT_ID=tu_webex_client_id
WEBEX_CLIENT_SECRET=tu_webex_client_secret
WEBEX_SITE_URL=https://tucompania.webex.com
```

#### 🔐 Seguridad
```env
SECRET_KEY=clave_secreta_32_caracteres_aqui
JWT_SECRET=jwt_secret_key_aqui
ENCRYPTION_KEY=encryption_key_32_chars_here
```

### Paso 4: Configurar Base de Datos

1. En Railway, agrega un servicio de **PostgreSQL**
2. La variable `DATABASE_URL` se configurará automáticamente
3. Opcionalmente, agrega **Redis** para cache

### Paso 5: Deploar

```bash
# Si usas Railway CLI
railway login
railway link tu-proyecto-id
railway up

# O simplemente haz push a tu repo si está conectado a GitHub
git add .
git commit -m "Deploy PNPtv bot"
git push origin main
```

### Paso 6: Configurar Webhook de Telegram

Una vez que el bot esté desplegado:

1. Obtén tu URL de Railway (ej: `https://tu-app.railway.app`)
2. Configura la variable `WEBHOOK_URL` con esa URL
3. El bot configurará automáticamente el webhook de Telegram

### Paso 7: Configurar Webhooks de Bold

1. En el panel de Bold.co, configura el webhook URL:
   ```
   https://tu-app.railway.app/webhooks/payment
   ```
2. Configura el secret que pusiste en `BOLD_WEBHOOK_SECRET`

---

## 🐳 Deployment con Docker

### Dockerfile Incluido

El proyecto incluye un `Dockerfile` optimizado:

```bash
# Build de la imagen
docker build -t pnptv-bot .

# Ejecutar en desarrollo
docker run -p 8000:8000 --env-file .env pnptv-bot

# Ejecutar en producción
docker run -d \
  -p 8000:8000 \
  --env-file .env.production \
  --restart unless-stopped \
  --name pnptv-bot \
  pnptv-bot
```

### Docker Compose

```yaml
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: pnptv
      POSTGRES_USER: pnptv
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## ⚙️ Configuración Avanzada

### Variables de Entorno Completas

Copia el archivo `deploy/.env.template` como `.env` y configura todas las variables:

```bash
cp deploy/.env.template .env
nano .env  # o tu editor preferido
```

### Configuración de Logging

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=tu_sentry_dsn  # Opcional para monitoreo
```

### Performance Tuning

```env
MAX_WORKERS=4
WORKER_TIMEOUT=300
BATCH_SIZE=50
DB_POOL_SIZE=20
```

### Rate Limiting

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=30
RATE_LIMIT_WINDOW=60
```

---

## 🔧 Configuración Post-Deployment

### 1. Verificar que el Bot Funciona

```bash
# Health check
curl https://tu-app.railway.app/health

# Estadísticas básicas
curl https://tu-app.railway.app/stats
```

### 2. Configurar Canales de Telegram

1. Agrega el bot a todos los canales premium como administrador
2. Obtén los IDs de los canales:
   ```
   /start en el bot
   Reenvía un mensaje del canal al bot
   El bot te mostrará el ID
   ```

### 3. Probar Pagos

1. Usa el comando `/plans` en el bot
2. Intenta comprar un plan de prueba
3. Verifica que el webhook de Bold funcione

### 4. Configurar Webex

1. Crea una aplicación en [developer.webex.com](https://developer.webex.com)
2. Obtén los tokens necesarios
3. Prueba crear un evento con `/webex`

---

## 📊 Monitoreo y Mantenimiento

### Logs en Railway

```bash
# Ver logs en tiempo real
railway logs --follow

# Filtrar por servicio
railway logs --service tu-servicio
```

### Health Checks

El bot incluye varios endpoints de monitoreo:

- `GET /health` - Estado general
- `GET /stats` - Estadísticas básicas
- `GET /webhooks/health` - Estado de webhooks

### Backup Automático

El bot incluye backup automático configurado:

```env
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 4 * * *  # Diario a las 4 AM
BACKUP_RETENTION_DAYS=30
```

### Scheduler de Trabajos

El bot ejecuta trabajos automáticos:

- ✅ **Verificación de membresías**: Diario a las 9 AM
- 📨 **Envío de broadcasts**: Cada minuto
- 🔄 **Sincronización de canales**: Cada 6 horas
- 🧹 **Limpieza de datos**: Semanal

---

## 🛠️ Troubleshooting

### Error: Bot no responde

1. Verifica que `BOT_TOKEN` esté correcto
2. Revisa los logs: `railway logs`
3. Verifica el webhook: `/health`

### Error: Pagos no funcionan

1. Verifica las credenciales de Bold.co
2. Revisa el webhook URL en Bold.co
3. Verifica los logs de webhook

### Error: Base de datos

1. Verifica que `DATABASE_URL` esté configurado
2. Revisa las conexiones de DB en Railway
3. Ejecuta migraciones si es necesario

### Error: Webex no funciona

1. Verifica el token de Webex
2. Revisa los permisos de la aplicación
3. Verifica la URL del sitio

---

## 🔄 Actualizaciones

### Deployment Automático con GitHub

1. Conecta tu repositorio a Railway
2. Habilita auto-deploy en Railway
3. Cada push a `main` desplegará automáticamente

### Deployment Manual

```bash
# Actualizar el código
git pull origin main

# Redesplegar
railway up

# O si usas Docker
docker build -t pnptv-bot .
docker stop pnptv-bot
docker rm pnptv-bot
docker run -d --name pnptv-bot pnptv-bot
```

---

## 📈 Escalabilidad

### Horizontal Scaling

Para manejar más usuarios:

1. Aumenta `MAX_WORKERS` en Railway
2. Considera usar múltiples instancias
3. Implementa load balancing si es necesario

### Database Scaling

1. Usa conexión pooling (ya configurado)
2. Considera read replicas para Railway Postgres
3. Implementa caching con Redis

### Monitoring Avanzado

Servicios recomendados:

- 📊 **Sentry**: Para error tracking
- 📈 **Datadog/New Relic**: Para APM
- 📊 **Grafana**: Para métricas custom

---

## 🔐 Seguridad

### Checklist de Seguridad

- ✅ Todas las variables de entorno están configuradas
- ✅ `SECRET_KEY` es único y seguro
- ✅ Webhooks usan HTTPS
- ✅ Rate limiting está habilitado
- ✅ Logs de seguridad están habilitados
- ✅ Database está protegida
- ✅ Solo administradores tienen acceso admin

### Backup Strategy

1. Database backup diario automático
2. Código en GitHub como backup
3. Variables de entorno documentadas
4. Configuración de canales respaldada

---

## 📞 Soporte

### Logs Importantes

```bash
# Ver errores recientes
railway logs --filter error

# Ver logs de webhook
railway logs --filter webhook

# Ver logs de scheduler
railway logs --filter scheduler
```

### Comandos de Debug

En el bot de Telegram (solo admins):

- `/admin` - Panel de administración
- `/stats` - Estadísticas del sistema
- Health checks disponibles en el panel admin

### Contacto

Para soporte técnico:
- 📧 Email: admin@pnptv.com
- 💬 Telegram: @AdminPNPtv
- 🐛 Issues: GitHub repository

---

## ✅ Checklist Final

Antes de considerar el deployment completo:

### Funcionalidad Básica
- [ ] Bot responde a `/start`
- [ ] Registro de usuarios funciona
- [ ] Menú principal funciona
- [ ] Cambio de idiomas funciona

### Pagos
- [ ] `/plans` muestra todos los planes
- [ ] Links de Bold.co funcionan
- [ ] Webhook de pagos funciona
- [ ] Activación automática funciona

### Membresías
- [ ] Usuarios son agregados a canales
- [ ] Usuarios son removidos al expirar
- [ ] Verificación diaria funciona

### Webex
- [ ] `/webex` muestra eventos
- [ ] Reserva de llamadas funciona
- [ ] Integración con API funciona

### Admin
- [ ] Panel admin funciona
- [ ] Broadcast funciona
- [ ] Estadísticas se muestran
- [ ] Exports funcionan

### Monitoreo
- [ ] Health checks responden
- [ ] Logs se generan correctamente
- [ ] Scheduler está funcionando
- [ ] Alertas están configuradas

¡Tu bot PNPtv está listo para producción! 🚀