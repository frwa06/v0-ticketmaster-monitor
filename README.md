# 🎫 Ticketmaster Monitor

Sistema automatizado de monitoreo para eventos de Bad Bunny en Ticketmaster Colombia. Detecta cuando se habilitan nuevos sectores y envía alertas SMS instantáneas.

## 🚀 Características

- **Monitoreo Continuo**: Verifica automáticamente cada 90-150 segundos
- **Detección Inteligente**: Identifica nuevos sectores disponibles usando múltiples estrategias
- **Alertas SMS**: Notificaciones instantáneas vía Twilio cuando hay cambios
- **Interfaz Web**: Registro fácil de números telefónicos y panel de estado
- **Deduplicación**: Evita spam enviando solo una alerta por cambio
- **Persistencia**: Base de datos SQLite para historial y configuración
- **Docker**: Despliegue fácil con contenedores
- **Logs Detallados**: Monitoreo completo de actividad y errores

## 📋 Eventos Monitoreados

- **Bad Bunny PQ23**: https://www.ticketmaster.co/event/bad-bunny-pq23
- **Bad Bunny PQ24**: https://www.ticketmaster.co/event/bad-bunny-pq24  
- **Bad Bunny PQ25**: https://www.ticketmaster.co/event/bad-bunny-pq25

## 🛠️ Instalación y Configuración

### Prerrequisitos

- Docker y Docker Compose
- Cuenta de Twilio (para SMS)
- Puerto 8000 disponible

### 1. Configuración Inicial

\`\`\`bash
# Clonar el repositorio
git clone <repository-url>
cd ticketmaster-monitor

# Ejecutar configuración inicial
./scripts/setup.sh
\`\`\`

### 2. Configurar Credenciales de Twilio

Editar el archivo `.env` con tus credenciales de Twilio:

\`\`\`env
TWILIO_ACCOUNT_SID=tu_account_sid_aqui
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_FROM_NUMBER=+1234567890
\`\`\`

**Obtener credenciales de Twilio:**
1. Crear cuenta en [Twilio Console](https://console.twilio.com/)
2. Obtener Account SID y Auth Token del dashboard
3. Comprar un número de teléfono para envío de SMS

### 3. Iniciar el Sistema

\`\`\`bash
# Iniciar todos los servicios
./scripts/start.sh
\`\`\`

El sistema estará disponible en:
- **Interfaz Web**: http://localhost:8000
- **Panel de Estado**: http://localhost:8000/status
- **Health Check**: http://localhost:8000/healthz

## 📱 Uso

### Registrar Número para Alertas

1. Abrir http://localhost:8000
2. Ingresar número telefónico (formato: +573001234567 o 3001234567)
3. Hacer clic en "Registrar para Alertas SMS"

### Cancelar Alertas

1. En la misma página, usar el formulario "Cancelar Alertas"
2. Ingresar el número a cancelar
3. Confirmar cancelación

### Monitorear Estado

- Visitar http://localhost:8000/status para ver:
  - Números registrados
  - Cambios recientes detectados
  - Historial de SMS enviados
  - Estado de eventos monitoreados

## 🔧 Comandos Útiles

\`\`\`bash
# Ver logs en tiempo real
./scripts/logs.sh

# Ejecutar pruebas
./scripts/test.sh

# Parar el sistema
./scripts/stop.sh

# Reiniciar servicios
docker-compose restart

# Ejecutar monitoreo una sola vez (prueba)
docker-compose exec ticketmaster-monitor python -m app.main --once --dry-run

# Simular cambios para probar SMS
docker-compose exec ticketmaster-monitor python -m app.main --simulate-delta --dry-run

# Ver métricas del sistema
curl http://localhost:8000/metrics
\`\`\`

## 🏗️ Arquitectura

\`\`\`
app/
├── main.py                 # Servicio principal de monitoreo
├── run_web.py             # Servidor web + monitoreo combinado
├── config.py              # Configuración del sistema
├── monitor/
│   ├── fetch.py           # Web scraping con Playwright
│   ├── parse.py           # Normalización de sectores
│   └── diff.py            # Comparación de snapshots
├── alerts/
│   └── sms.py             # Sistema de alertas SMS
├── storage/
│   └── db.py              # Modelos de base de datos
└── web/
    ├── server.py          # API web con FastAPI
    └── templates/         # Plantillas HTML
\`\`\`

## 🧪 Testing

\`\`\`bash
# Ejecutar todas las pruebas
docker-compose exec ticketmaster-monitor python -m pytest tests/ -v

# Ejecutar pruebas específicas
docker-compose exec ticketmaster-monitor python -m pytest tests/test_diff.py -v

# Prueba de monitoreo en vivo (sin SMS)
docker-compose exec ticketmaster-monitor python -m app.main --once --dry-run

# Prueba de SMS (sin envío real)
docker-compose exec ticketmaster-monitor python -m app.main --simulate-delta --dry-run
\`\`\`

## 📊 Monitoreo y Logs

### Logs del Sistema

\`\`\`bash
# Logs en tiempo real
docker-compose logs -f

# Logs específicos del contenedor
docker-compose logs ticketmaster-monitor

# Logs guardados en archivo
tail -f logs/ticketmaster_monitor.log
\`\`\`

### Métricas Disponibles

- **Números activos registrados**
- **Total de SMS enviados**
- **Cambios detectados**
- **Snapshots guardados**
- **Estado del servicio SMS**

## ⚙️ Configuración Avanzada

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `POLL_INTERVAL_MIN` | Intervalo mínimo entre verificaciones (segundos) | 90 |
| `POLL_INTERVAL_MAX` | Intervalo máximo entre verificaciones (segundos) | 150 |
| `HEADLESS` | Ejecutar navegador sin interfaz gráfica | true |
| `PAGE_TIMEOUT` | Timeout para carga de páginas (ms) | 30000 |
| `LOG_LEVEL` | Nivel de logging (DEBUG, INFO, WARNING, ERROR) | INFO |
| `WEB_PORT` | Puerto del servidor web | 8000 |

### Personalizar User-Agent

\`\`\`env
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
CONTACT_EMAIL=tu-email@ejemplo.com
\`\`\`

## 🚨 Solución de Problemas

### El servicio no inicia

1. Verificar que Docker esté ejecutándose
2. Revisar que el puerto 8000 esté disponible
3. Verificar credenciales de Twilio en `.env`

\`\`\`bash
# Verificar estado de Docker
docker info

# Verificar logs de error
docker-compose logs ticketmaster-monitor
\`\`\`

### No se envían SMS

1. Verificar credenciales de Twilio
2. Confirmar que el número FROM esté verificado en Twilio
3. Revisar logs para errores específicos

\`\`\`bash
# Probar configuración SMS
docker-compose exec ticketmaster-monitor python -m app.main --simulate-delta
\`\`\`

### Errores de scraping

1. Verificar conectividad a internet
2. Revisar si Ticketmaster cambió la estructura de la página
3. Aumentar timeout si es necesario

\`\`\`bash
# Probar scraping manual
docker-compose exec ticketmaster-monitor python -m app.main --once --event pq23
\`\`\`

### Base de datos corrupta

\`\`\`bash
# Respaldar y recrear base de datos
cp data/ticketmaster_monitor.db data/backup.db
rm data/ticketmaster_monitor.db
docker-compose restart
\`\`\`

## 📄 Licencia

Este proyecto es para uso educativo y personal. Respeta los términos de servicio de Ticketmaster y usa el sistema de manera responsable.

## 🤝 Contribuciones

1. Fork el repositorio
2. Crear rama para nueva funcionalidad
3. Hacer commit de cambios
4. Crear Pull Request

## 📞 Soporte

Para problemas técnicos:
1. Revisar logs del sistema
2. Consultar sección de solución de problemas
3. Crear issue en el repositorio con logs relevantes

---

**⚠️ Aviso Legal**: Este sistema es para uso personal y educativo. El usuario es responsable de cumplir con los términos de servicio de Ticketmaster y usar el sistema de manera ética y responsable.
