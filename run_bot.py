#!/usr/bin/env python3
"""
run_bot.py
Punto de entrada para el bot PNPtv en Railway
"""

import sys
import os
import logging
import traceback

# Configurar logging básico inmediatamente
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Agregar el directorio actual al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def verify_environment():
    """Verifica el entorno y dependencias"""
    try:
        # Verificar Python version
        logger.info(f"Python version: {sys.version}")
        if sys.version_info < (3, 11):
            logger.error("Error: Se requiere Python 3.11 o superior")
            return False
        
        # Verificar directorio de trabajo
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Script directory: {current_dir}")
        
        # Verificar que existe main.py
        main_py_path = os.path.join(current_dir, 'main.py')
        if not os.path.exists(main_py_path):
            logger.error(f"main.py no encontrado en {main_py_path}")
            return False
        
        # Verificar variables de entorno críticas
        required_vars = ['BOT_TOKEN']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                logger.info(f"{var}: {'*' * min(8, len(value))}...")
        
        # DATABASE_URL es opcional para development
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            # Censurar URL para logging
            if '@' in database_url:
                censored_url = database_url.split('@')[-1]
            else:
                censored_url = database_url[:20] + "..."
            logger.info(f"DATABASE_URL: {censored_url}")
        else:
            logger.warning("DATABASE_URL no configurada")
        
        if missing_vars:
            logger.error(f"Variables de entorno faltantes: {missing_vars}")
            return False
        
        # Verificar entorno de ejecución
        environment = os.getenv('ENVIRONMENT', 'development')
        logger.info(f"Environment: {environment}")
        
        # Verificar puerto
        port = os.getenv('PORT', '8000')
        logger.info(f"Port: {port}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando entorno: {e}")
        logger.error(traceback.format_exc())
        return False

def test_imports():
    """Prueba imports críticos"""
    try:
        logger.info("Verificando imports críticos...")
        
        # Test import asyncio
        import asyncio
        logger.info("✓ asyncio importado")
        
        # Test import telegram
        try:
            from telegram import Bot
            logger.info("✓ python-telegram-bot importado")
        except ImportError as e:
            logger.error(f"✗ Error importando telegram: {e}")
            return False
        
        # Test import config (nuestro módulo)
        try:
            import config
            logger.info("✓ config module importado")
        except ImportError as e:
            logger.warning(f"⚠ config module no disponible: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en test de imports: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Función principal de entrada"""
    try:
        logger.info("🚀 Iniciando PNPtv Bot...")
        logger.info("=" * 50)
        
        # Verificar entorno
        if not verify_environment():
            logger.error("❌ Verificación de entorno falló")
            sys.exit(1)
        
        # Verificar imports
        if not test_imports():
            logger.error("❌ Verificación de imports falló")
            sys.exit(1)
        
        logger.info("✓ Verificaciones completadas")
        logger.info("=" * 50)
        
        # Importar y ejecutar main
        logger.info("Importando módulo principal...")
        try:
            from main import main as bot_main
            import asyncio
            logger.info("✓ Módulo principal importado exitosamente")
        except ImportError as e:
            logger.error(f"❌ Error importando main.py: {e}")
            logger.error(traceback.format_exc())
            
            # Listar archivos en directorio actual para debug
            logger.info("Contenido del directorio actual:")
            try:
                for item in os.listdir(current_dir):
                    logger.info(f"  - {item}")
            except Exception as list_error:
                logger.error(f"Error listando directorio: {list_error}")
            
            sys.exit(1)
        
        logger.info("🤖 Ejecutando bot...")
        logger.info("=" * 50)
        
        # Ejecutar bot
        asyncio.run(bot_main())
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("Verificar que todos los módulos estén instalados")
        logger.error(traceback.format_exc())
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("⏹️ Bot detenido por usuario")
        sys.exit(0)
    except SystemExit:
        # Re-raise SystemExit para mantener el código de salida
        raise
    except Exception as e:
        logger.error(f"❌ Error crítico ejecutando bot: {e}")
        logger.error(traceback.format_exc())
        
        # Información adicional de debug
        logger.error("Información de debug:")
        logger.error(f"  - Directorio actual: {os.getcwd()}")
        logger.error(f"  - Script path: {__file__}")
        logger.error(f"  - Python path: {sys.path[:3]}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()