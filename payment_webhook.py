"""
webhooks/payment_webhook.py
Webhook para recibir confirmaciones de pago desde Bold.co
"""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Header
from fastapi.responses import JSONResponse
from telegram import Bot
from telegram.error import TelegramError

from config import Config
from services.payment_service import PaymentService
from services.user_service import UserService
from services.notification_service import NotificationService
from utils.helpers import logger


class PaymentWebhookHandler:
    def __init__(self):
        self.payment_service = PaymentService()
        self.user_service = UserService()
        self.notification_service = NotificationService()
        self.bot = None
        
    async def initialize_bot(self):
        """Inicializar bot de Telegram"""
        if not self.bot:
            self.bot = Bot(token=Config.BOT_TOKEN)
    
    async def handle_bold_webhook(self, 
                                 request_data: Dict[str, Any],
                                 signature: Optional[str] = None,
                                 background_tasks: BackgroundTasks = None) -> Dict[str, Any]:
        """Manejar webhook de Bold.co"""
        try:
            logger.info(f"Webhook Bold recibido: {json.dumps(request_data, indent=2)}")
            
            # Verificar estructura básica del webhook
            if not self._validate_webhook_structure(request_data):
                logger.error("Estructura de webhook inválida")
                raise HTTPException(status_code=400, detail="Invalid webhook structure")
            
            # Procesar webhook en background
            if background_tasks:
                background_tasks.add_task(
                    self._process_webhook_background,
                    request_data,
                    signature
                )
            else:
                # Procesar síncronamente si no hay background tasks
                await self._process_webhook_background(request_data, signature)
            
            return {"status": "success", "message": "Webhook received"}
            
        except Exception as e:
            logger.error(f"Error manejando webhook Bold: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _process_webhook_background(self, 
                                        webhook_data: Dict[str, Any],
                                        signature: Optional[str]):
        """Procesar webhook en background"""
        try:
            # Procesar pago con PaymentService
            success = await self.payment_service.process_bold_webhook(webhook_data, signature)
            
            if success:
                # Enviar notificaciones
                await self._send_payment_notifications(webhook_data)
                logger.info("Webhook procesado exitosamente")
            else:
                logger.error("Error procesando webhook")
                
        except Exception as e:
            logger.error(f"Error en procesamiento background: {str(e)}")
    
    def _validate_webhook_structure(self, data: Dict[str, Any]) -> bool:
        """Validar estructura básica del webhook"""
        required_fields = ['id', 'status', 'amount']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Campo requerido faltante en webhook: {field}")
                return False
        
        # Validar tipos
        if not isinstance(data['amount'], (int, float)):
            logger.error("Campo 'amount' debe ser numérico")
            return False
        
        if not isinstance(data['status'], str):
            logger.error("Campo 'status' debe ser string")
            return False
        
        return True
    
    async def _send_payment_notifications(self, webhook_data: Dict[str, Any]):
        """Enviar notificaciones de pago"""
        try:
            await self.initialize_bot()
            
            transaction_id = webhook_data.get('id')
            status = webhook_data.get('status', '').lower()
            amount = webhook_data.get('amount', 0)
            
            # Extraer user_id de metadata
            user_id = self._extract_user_id_from_webhook(webhook_data)
            
            if user_id:
                if status in ['completed', 'approved', 'success']:
                    await self._notify_payment_success(user_id, amount, transaction_id)
                elif status in ['failed', 'declined', 'error']:
                    await self._notify_payment_failure(user_id, amount, transaction_id)
            
            # Notificar a admins
            await self._notify_admins_payment_event(webhook_data, user_id)
            
        except Exception as e:
            logger.error(f"Error enviando notificaciones de pago: {str(e)}")
    
    def _extract_user_id_from_webhook(self, webhook_data: Dict[str, Any]) -> Optional[int]:
        """Extraer user_id del webhook"""
        try:
            metadata = webhook_data.get('metadata', {})
            
            if isinstance(metadata, dict):
                user_id = metadata.get('user_id')
                if user_id:
                    return int(user_id)
            
            elif isinstance(metadata, str):
                if 'user_id:' in metadata:
                    user_id_str = metadata.split('user_id:')[1].split(',')[0]
                    return int(user_id_str)
            
            # Buscar en otros campos
            description = webhook_data.get('description', '')
            if 'user_id:' in description:
                user_id_str = description.split('user_id:')[1].split(',')[0]
                return int(user_id_str)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extrayendo user_id: {str(e)}")
            return None
    
    async def _notify_payment_success(self, user_id: int, amount: float, transaction_id: str):
        """Notificar al usuario sobre pago exitoso"""
        try:
            # Obtener idioma del usuario
            user_lang = await self.user_service.get_user_language(user_id)
            
            # Crear mensaje de confirmación
            if user_lang == 'es':
                message = f"""
🎉 ¡Pago Confirmado!

✅ Tu pago de ${amount:.2f} USD ha sido procesado exitosamente.
🆔 ID de transacción: {transaction_id}

Tu suscripción ya está activa. ¡Disfruta del contenido premium!

Para acceder a tus beneficios, usa /menu
                """.strip()
            else:
                message = f"""
🎉 Payment Confirmed!

✅ Your payment of ${amount:.2f} USD has been processed successfully.
🆔 Transaction ID: {transaction_id}

Your subscription is now active. Enjoy the premium content!

To access your benefits, use /menu
                """.strip()
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message
            )
            
            logger.info(f"Notificación de pago exitoso enviada a usuario {user_id}")
            
        except TelegramError as e:
            logger.error(f"Error enviando notificación Telegram a {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error notificando pago exitoso: {str(e)}")
    
    async def _notify_payment_failure(self, user_id: int, amount: float, transaction_id: str):
        """Notificar al usuario sobre pago fallido"""
        try:
            # Obtener idioma del usuario
            user_lang = await self.user_service.get_user_language(user_id)
            
            # Crear mensaje de fallo
            if user_lang == 'es':
                message = f"""
😔 Pago No Procesado

❌ Tu pago de ${amount:.2f} USD no pudo ser procesado.
🆔 ID de transacción: {transaction_id}

Posibles causas:
• Fondos insuficientes
• Problema con el método de pago
• Error temporal del procesador

💡 Puedes intentar nuevamente usando /plans

Si el problema persiste, contacta soporte.
                """.strip()
            else:
                message = f"""
😔 Payment Not Processed

❌ Your payment of ${amount:.2f} USD could not be processed.
🆔 Transaction ID: {transaction_id}

Possible causes:
• Insufficient funds
• Payment method issue
• Temporary processor error

💡 You can try again using /plans

If the problem persists, contact support.
                """.strip()
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message
            )
            
            logger.info(f"Notificación de pago fallido enviada a usuario {user_id}")
            
        except TelegramError as e:
            logger.error(f"Error enviando notificación Telegram a {user_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error notificando pago fallido: {str(e)}")
    
    async def _notify_admins_payment_event(self, webhook_data: Dict[str, Any], user_id: Optional[int]):
        """Notificar a administradores sobre evento de pago"""
        try:
            admin_ids = await self.user_service.get_admin_user_ids()
            
            if not admin_ids:
                return
            
            # Crear mensaje para admins
            transaction_id = webhook_data.get('id', 'N/A')
            status = webhook_data.get('status', 'unknown')
            amount = webhook_data.get('amount', 0)
            payment_method = webhook_data.get('payment_method', 'N/A')
            
            status_emoji = {
                'completed': '✅',
                'approved': '✅', 
                'success': '✅',
                'failed': '❌',
                'declined': '❌',
                'error': '❌',
                'pending': '⏳'
            }.get(status.lower(), '❓')
            
            admin_message = f"""
🔔 Evento de Pago

{status_emoji} Estado: {status.upper()}
💰 Monto: ${amount:.2f} USD
👤 Usuario: {user_id or 'Desconocido'}
🆔 Transacción: {transaction_id}
💳 Método: {payment_method}
🕐 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Raw data:
{json.dumps(webhook_data, indent=2)}
            """.strip()
            
            # Enviar a todos los admins
            for admin_id in admin_ids:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=admin_message,
                        parse_mode='HTML'
                    )
                except TelegramError as e:
                    logger.error(f"Error enviando notificación a admin {admin_id}: {str(e)}")
            
            logger.info(f"Notificación de evento de pago enviada a {len(admin_ids)} admins")
            
        except Exception as e:
            logger.error(f"Error notificando a admins: {str(e)}")
    
    async def handle_test_webhook(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manejar webhook de prueba"""
        try:
            logger.info("Webhook de prueba recibido")
            
            # Validar que sea un webhook de prueba
            if not test_data.get('test', False):
                raise HTTPException(status_code=400, detail="Not a test webhook")
            
            # Procesar webhook de prueba
            response = {
                "status": "success",
                "message": "Test webhook processed",
                "received_data": test_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Notificar a admins sobre webhook de prueba
            admin_ids = await self.user_service.get_admin_user_ids()
            
            if admin_ids and self.bot:
                test_message = f"""
🧪 Webhook de Prueba Recibido

✅ El webhook endpoint está funcionando correctamente.
🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Datos recibidos:
{json.dumps(test_data, indent=2)}
                """.strip()
                
                for admin_id in admin_ids:
                    try:
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=test_message
                        )
                    except TelegramError:
                        pass
            
            return response
            
        except Exception as e:
            logger.error(f"Error manejando webhook de prueba: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_webhook_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de webhooks"""
        try:
            # Obtener estadísticas desde el servicio de pagos
            end_date = datetime.utcnow()
            start_date = end_date.replace(day=1)  # Desde inicio del mes
            
            payment_stats = await self.payment_service.get_payment_statistics(start_date, end_date)
            
            webhook_stats = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "payment_stats": payment_stats,
                "webhook_endpoint": f"{Config.WEBHOOK_URL}/webhooks/payment",
                "test_endpoint": f"{Config.WEBHOOK_URL}/webhooks/payment/test",
                "status": "active"
            }
            
            return webhook_stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de webhook: {str(e)}")
            return {"error": str(e)}


# Instancia global del handler
webhook_handler = PaymentWebhookHandler()


# === ENDPOINTS FASTAPI ===

app = FastAPI(title="PNPtv Payment Webhooks", version="1.0.0")


@app.post("/webhooks/payment")
async def receive_bold_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature: Optional[str] = Header(None, alias="X-Bold-Signature")
):
    """Endpoint principal para webhooks de Bold.co"""
    try:
        request_data = await request.json()
        
        return await webhook_handler.handle_bold_webhook(
            request_data=request_data,
            signature=x_signature,
            background_tasks=background_tasks
        )
        
    except json.JSONDecodeError:
        logger.error("JSON inválido en webhook")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    except Exception as e:
        logger.error(f"Error en endpoint webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/webhooks/payment/test")
async def test_webhook_endpoint(request: Request):
    """Endpoint para probar webhooks"""
    try:
        test_data = await request.json()
        test_data['test'] = True  # Marcar como webhook de prueba
        
        return await webhook_handler.handle_test_webhook(test_data)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    except Exception as e:
        logger.error(f"Error en endpoint de prueba: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/webhooks/payment/stats")
async def get_webhook_statistics():
    """Obtener estadísticas de webhooks"""
    try:
        return await webhook_handler.get_webhook_stats()
    
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/webhooks/health")
async def health_check():
    """Health check del servicio de webhooks"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "pnptv-payment-webhooks"
    }


# === COMANDO PARA INICIALIZAR WEBHOOK HANDLER ===

async def initialize_webhook_handler():
    """Inicializar el webhook handler con el bot"""
    await webhook_handler.initialize_bot()
    logger.info("Webhook handler inicializado")


# === FUNCIONES AUXILIARES PARA TESTING ===

async def simulate_payment_webhook(user_id: int, plan_code: str, 
                                 amount: float, status: str = 'completed'):
    """Simular webhook de pago para testing"""
    test_webhook_data = {
        "id": f"test_transaction_{datetime.utcnow().timestamp()}",
        "status": status,
        "amount": amount,
        "payment_method": "credit_card",
        "metadata": {
            "user_id": user_id,
            "plan": plan_code
        },
        "timestamp": datetime.utcnow().isoformat(),
        "test": True
    }
    
    await webhook_handler._process_webhook_background(test_webhook_data, None)
    logger.info(f"Webhook simulado procesado para usuario {user_id}")


if __name__ == "__main__":
    import uvicorn
    
    # Inicializar webhook handler
    asyncio.run(initialize_webhook_handler())
    
    # Ejecutar servidor
    uvicorn.run(
        "webhooks.payment_webhook:app",
        host="0.0.0.0",
        port=Config.WEBHOOK_PORT,
        reload=Config.DEBUG
    )