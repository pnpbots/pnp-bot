"""
Aplicación principal del bot PNPtv
Configuración del bot Telegram con handlers y middleware
"""

import asyncio
import logging
import signal
import sys
import os
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
    ContextTypes
)
from telegram.error import NetworkError, TelegramError
from config import config
from utils.helpers import setup_logging, graceful_shutdown

# --- Importar los SERVICIOS ---
from services.user_service import UserService
from services.menu_service import MenuService
from services.file_service import FileService
from services.payment_service import PaymentService
from services.webex_service import WebexService
from services.notification_service import NotificationService
from services.channel_manager import ChannelManager

# --- Importar los HANDLERS (clases y funciones) ---
from handlers.admin import AdminHandler
from handlers.start import start_command, language_callback, terms_callback
from handlers.menu import menu_command, menu_callback
from handlers.plans import PlansHandler
from handlers.webex import WebexHandler

# Configurar logging
logger = setup_logging()

class PNPtvBot:
    """Clase principal del bot PNPtv"""

    def __init__(self):
        self.application: Optional[Application] = None
        self.is_running = False

    async def initialize(self):
        """Inicializa el bot y sus componentes"""
        try:
            logger.info("Iniciando bot PNPtv...")
            await init_database()
            logger.info("Base de datos inicializada")
            self.application = Application.builder().token(config.telegram.token).build()
            self._register_handlers()
            self.application.add_error_handler(self._error_handler)
            logger.info("Bot inicializado exitosamente")
        except Exception as e:
            logger.error(f"Error inicializando bot: {e}", exc_info=True)
            raise

    def _register_handlers(self):
        """Registra todos los handlers del bot usando Inyección de Dependencias."""
        
        # 1. Crear instancias de todos los servicios
        user_service = UserService()
        menu_service = MenuService()
        file_service = FileService()
        payment_service = PaymentService()
        webex_service = WebexService()
        notification_service = NotificationService()
        channel_manager = ChannelManager()

        # 2. Crear instancias de los handlers que son clases, inyectando los servicios
        admin_handler = AdminHandler(user_service, menu_service, file_service)
        plans_handler = PlansHandler(user_service, payment_service)
        webex_handler = WebexHandler(webex_service, user_service, notification_service)

        # 3. Registrar los handlers en la aplicación
        
        # Comandos
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("menu", menu_command))
        self.application.add_handler(CommandHandler("plans", plans_handler.show_plans_menu))
        self.application.add_handler(CommandHandler("admin", admin_handler.admin_panel))
        self.application.add_handler(CommandHandler("webex", webex_handler.show_webex_menu))

        # Callbacks
        self.application.add_handler(CallbackQueryHandler(language_callback, pattern="^lang_"))
        self.application.add_handler(CallbackQueryHandler(terms_callback, pattern="^terms_"))
        self.application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
        self.application.add_handler(CallbackQueryHandler(plans_handler.handle_plans_callback, pattern="^plans_"))
        self.application.add_handler(CallbackQueryHandler(admin_handler.handle_admin_callback, pattern="^admin_"))
        self.application.add_handler(CallbackQueryHandler(webex_handler.handle_webex_callback, pattern="^webex_"))
        
        logger.info("Handlers registrados exitosamente")

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Maneja los errores capturados por el bot."""
        logger.error("Exception while handling an update:", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text("⚠️ Ocurrió un error. El equipo ha sido notificado.")
            except Exception as e:
                logger.error(f"No se pudo enviar mensaje de error al usuario: {e}")

    async def run(self):
        """Inicia el bot en el modo apropiado (polling o webhook)."""
        if not self.application:
            await self.initialize()
        
        if config.is_production() and config.telegram.webhook_url:
            port = int(os.getenv("PORT", 8000))
            logger.info(f"Iniciando bot en modo webhook en puerto {port}...")
            await self.application.run_webhook(
                listen="0.0.0.0",
                port=port,
                webhook_url=config.telegram.webhook_url
            )
        else:
            logger.info("Iniciando bot en modo polling...")
            await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def shutdown(self):
        """Detiene el bot de forma segura."""
        if self.application and self.application.running:
            await self.application.stop()
        await close_database()
        logger.info("Bot detenido.")

async def main():
    """Función principal para correr el bot."""
    bot = PNPtvBot()
    
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(bot.shutdown()))

    try:
        await bot.run()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown solicitado.")
    except Exception as e:
        logger.critical(f"Error crítico en la ejecución del bot: {e}", exc_info=True)
    finally:
        await bot.shutdown()

if __name__ == "__main__":
    if sys.version_info < (3, 8):
        sys.exit("Se requiere Python 3.8 o superior.")
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Proceso terminado.")
