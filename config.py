"""
Configuración completa del bot PNPtv para manejo de suscripciones
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator

class AdminConfig(BaseSettings):
    """Configuración de administración"""
    host: str = "0.0.0.0"
    port: int = 8000
    ids: List[int] = []
    
    @validator('ids', pre=True)
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            if v.strip():
                return [int(id_str.strip()) for id_str in v.split(',') if id_str.strip()]
            return []
        return v or []
    
    class Config:
        env_prefix = "ADMIN_"
        case_sensitive = False

class BoldConfig(BaseSettings):
    """Configuración de Bold (sistema de pagos)"""
    identity_key: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    class Config:
        env_prefix = "BOLD_"
        case_sensitive = False

class TelegramConfig(BaseSettings):
    """Configuración de Telegram"""
    token: str
    webhook_url: Optional[str] = None
    
    # Canales y grupos
    channel_id_1: Optional[int] = None
    channel_id_2: Optional[int] = None
    vip_group_id: Optional[int] = None
    customer_service_chat_id: Optional[int] = None
    
    @validator('token')
    def validate_token(cls, v):
        if not v:
            raise ValueError('BOT_TOKEN es requerido')
        return v
    
    @validator('channel_id_1', 'channel_id_2', 'vip_group_id', 'customer_service_chat_id', pre=True)
    def parse_chat_ids(cls, v):
        if v is None or v == "":
            return None
        try:
            return int(v)
        except (ValueError, TypeError):
            return None
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class DatabaseConfig(BaseSettings):
    """Configuración de base de datos"""
    url: str = "sqlite:///pnptv_bot.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    class Config:
        env_prefix = "DATABASE_"
        case_sensitive = False

class SubscriptionConfig(BaseSettings):
    """Configuración de suscripciones"""
    reminder_days_before_expiry: int = 3
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class AppConfig(BaseSettings):
    """Configuración general de la aplicación"""
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    pythonpath: str = "."
    pythonunbuffered: str = "1"
    
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    class Config:
        env_prefix = ""
        case_sensitive = False

class Config:
    """Configuración principal del bot PNPtv"""
    
    def __init__(self):
        # Cargar variables de entorno desde .env si existe
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Inicializar configuraciones de administración
        self.admin = AdminConfig(
            host=os.getenv('ADMIN_HOST', '0.0.0.0'),
            port=int(os.getenv('ADMIN_PORT', '8000')),
            ids=os.getenv('ADMIN_IDS', '')
        )
        
        # Configuración de Bold (pagos)
        self.bold = BoldConfig(
            identity_key=os.getenv('BOLD_IDENTITY_KEY'),
            webhook_secret=os.getenv('BOLD_WEBHOOK_SECRET')
        )
        
        # Configuración de Telegram
        self.telegram = TelegramConfig(
            token=os.getenv('BOT_TOKEN', ''),
            webhook_url=os.getenv('WEBHOOK_URL'),
            channel_id_1=os.getenv('CHANNEL_ID_1'),
            channel_id_2=os.getenv('CHANNEL_ID_2'),
            vip_group_id=os.getenv('VIP_GROUP_ID'),
            customer_service_chat_id=os.getenv('CUSTOMER_SERVICE_CHAT_ID')
        )
        
        # Configuración de base de datos
        self.database = DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'sqlite:///pnptv_bot.db'),
            echo=os.getenv('DATABASE_ECHO', 'false').lower() in ('true', '1', 'yes'),
            pool_size=int(os.getenv('DATABASE_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DATABASE_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DATABASE_POOL_RECYCLE', '3600'))
        )
        
        # Configuración de suscripciones
        self.subscription = SubscriptionConfig(
            reminder_days_before_expiry=int(os.getenv('REMINDER_DAYS_BEFORE_EXPIRY', '3'))
        )
        
        # Configuración general de la aplicación
        self.app = AppConfig(
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug=os.getenv('DEBUG', '').lower() in ('true', '1', 'yes'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '8000')),
            pythonpath=os.getenv('PYTHONPATH', '.'),
            pythonunbuffered=os.getenv('PYTHONUNBUFFERED', '1')
        )
    
    def is_production(self) -> bool:
        return self.app.is_production()
    
    def is_development(self) -> bool:
        return self.app.is_development()
    
    def get_admin_ids(self) -> List[int]:
        """Retorna lista de IDs de administradores"""
        return self.admin.ids
    
    def is_admin(self, user_id: int) -> bool:
        """Verifica si un usuario es administrador"""
        return user_id in self.admin.ids
    
    def get_channels(self) -> List[int]:
        """Retorna lista de canales configurados"""
        channels = []
        if self.telegram.channel_id_1:
            channels.append(self.telegram.channel_id_1)
        if self.telegram.channel_id_2:
            channels.append(self.telegram.channel_id_2)
        return channels
    
    def get_vip_group(self) -> Optional[int]:
        """Retorna ID del grupo VIP"""
        return self.telegram.vip_group_id
    
    def get_customer_service_chat(self) -> Optional[int]:
        """Retorna ID del chat de servicio al cliente"""
        return self.telegram.customer_service_chat_id
    
    def has_bold_config(self) -> bool:
        """Verifica si Bold está configurado"""
        return bool(self.bold.identity_key and self.bold.webhook_secret)
    
    def validate_config(self) -> dict:
        """Valida la configuración y retorna un reporte"""
        report = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validaciones críticas
        if not self.telegram.token:
            report['valid'] = False
            report['errors'].append('BOT_TOKEN no configurado')
        
        if not self.admin.ids:
            report['warnings'].append('No hay administradores configurados')
        
        if not self.get_channels():
            report['warnings'].append('No hay canales configurados')
        
        if not self.telegram.vip_group_id:
            report['warnings'].append('Grupo VIP no configurado')
        
        if not self.has_bold_config():
            report['warnings'].append('Bold (pagos) no configurado completamente')
        
        if self.is_production() and not self.telegram.webhook_url:
            report['warnings'].append('Webhook URL no configurada para producción')
        
        return report
    
    def log_config(self, logger):
        """Log de configuración (sin datos sensibles)"""
        logger.info("=== CONFIGURACIÓN PNPTV BOT ===")
        logger.info(f"Ambiente: {self.app.environment}")
        logger.info(f"Log Level: {self.app.log_level}")
        logger.info(f"Host: {self.app.host}:{self.app.port}")
        
        # Admin
        logger.info(f"Admins configurados: {len(self.admin.ids)}")
        if self.admin.ids:
            logger.info(f"Admin IDs: {self.admin.ids}")
        
        # Telegram
        logger.info(f"Token configurado: {'✓' if self.telegram.token else '✗'}")
        logger.info(f"Webhook URL: {'✓' if self.telegram.webhook_url else '✗'}")
        
        # Canales y grupos
        channels = self.get_channels()
        logger.info(f"Canales configurados: {len(channels)}")
        if channels:
            logger.info(f"Channel IDs: {channels}")
        
        if self.telegram.vip_group_id:
            logger.info(f"Grupo VIP: {self.telegram.vip_group_id}")
        
        if self.telegram.customer_service_chat_id:
            logger.info(f"Servicio al cliente: {self.telegram.customer_service_chat_id}")
        
        # Bold
        logger.info(f"Bold configurado: {'✓' if self.has_bold_config() else '✗'}")
        
        # Base de datos
        db_url = self.database.url
        if '@' in db_url:
            db_url = db_url.split('@')[-1]
        logger.info(f"Base de datos: {db_url}")
        
        # Suscripciones
        logger.info(f"Días de recordatorio: {self.subscription.reminder_days_before_expiry}")
        
        logger.info("=" * 40)

# Instancia global de configuración
config = Config()

# Validar configuración al importar
validation_report = config.validate_config()
if not validation_report['valid']:
    import logging
    logger = logging.getLogger(__name__)
    logger.error("❌ Configuración inválida:")
    for error in validation_report['errors']:
        logger.error(f"  - {error}")
    
    if validation_report['warnings']:
        logger.warning("⚠️ Advertencias de configuración:")
        for warning in validation_report['warnings']:
            logger.warning(f"  - {warning}")

# Constantes útiles
CHANNELS = config.get_channels()
VIP_GROUP = config.get_vip_group()
ADMIN_IDS = config.get_admin_ids()
CUSTOMER_SERVICE_CHAT = config.get_customer_service_chat()

# Funciones helper
def is_admin(user_id: int) -> bool:
    """Verifica si un usuario es administrador"""
    return config.is_admin(user_id)

def get_channel_ids() -> List[int]:
    """Retorna IDs de canales"""
    return config.get_channels()

def get_vip_group_id() -> Optional[int]:
    """Retorna ID del grupo VIP"""
    return config.get_vip_group()

def is_subscription_channel(chat_id: int) -> bool:
    """Verifica si un chat ID corresponde a un canal de suscripción"""
    return chat_id in config.get_channels()

def is_vip_group(chat_id: int) -> bool:
    """Verifica si un chat ID corresponde al grupo VIP"""
    return chat_id == config.get_vip_group()

def get_reminder_days() -> int:
    """Retorna días antes de expiración para recordatorios"""
    return config.subscription.reminder_days_before_expiry

def get_bold_config() -> dict:
    """Retorna configuración de Bold para pagos"""
    return {
        'identity_key': config.bold.identity_key,
        'webhook_secret': config.bold.webhook_secret,
        'configured': config.has_bold_config()
    }

def get_webhook_url() -> Optional[str]:
    """Retorna URL del webhook"""
    return config.telegram.webhook_url

def log_startup_config():
    """Log completo de la configuración al inicio"""
    import logging
    logger = logging.getLogger(__name__)
    
    config.log_config(logger)
    
    # Validación y reporte
    validation = config.validate_config()
    if not validation['valid']:
        logger.error("❌ CONFIGURACIÓN INVÁLIDA - EL BOT NO FUNCIONARÁ CORRECTAMENTE")
        for error in validation['errors']:
            logger.error(f"  ❌ {error}")
    
    if validation['warnings']:
        logger.warning("⚠️ ADVERTENCIAS DE CONFIGURACIÓN:")
        for warning in validation['warnings']:
            logger.warning(f"  ⚠️ {warning}")
    
    if validation['valid'] and not validation['warnings']:
        logger.info("✅ Configuración válida y completa")

# Exportar variables principales para compatibilidad
BOT_TOKEN = config.telegram.token
WEBHOOK_URL = config.telegram.webhook_url
ENVIRONMENT = config.app.environment
DATABASE_URL = config.database.url

# Información de canales y grupos
CHANNEL_1_ID = config.telegram.channel_id_1
CHANNEL_2_ID = config.telegram.channel_id_2
VIP_GROUP_ID = config.telegram.vip_group_id
CUSTOMER_SERVICE_ID = config.telegram.customer_service_chat_id

# Configuración de Bold
BOLD_IDENTITY_KEY = config.bold.identity_key
BOLD_WEBHOOK_SECRET = config.bold.webhook_secret

# Configuración de recordatorios
REMINDER_DAYS = config.subscription.reminder_days_before_expiry