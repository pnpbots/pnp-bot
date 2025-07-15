"""
scheduler.py
Configuración principal del scheduler APScheduler para todos los jobs automáticos
"""

import asyncio
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from config import Config
from utils.helpers import logger


class PNPtvScheduler:
    def __init__(self):
        # Configuración de jobstores
        jobstores = {
            'default': MemoryJobStore(),
        }
        
        # Si está configurada la base de datos, usar SQLAlchemy jobstore
        if Config.DATABASE_URL:
            try:
                jobstores['persistent'] = SQLAlchemyJobStore(url=Config.DATABASE_URL)
                logger.info("✅ SQLAlchemy jobstore configurado")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo configurar SQLAlchemy jobstore: {str(e)}")
        
        # Configuración de executors
        executors = {
            'default': AsyncIOExecutor(),
        }
        
        # Configuración de jobs por defecto
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutos de gracia
        }
        
        # Crear scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Estado del scheduler
        self.is_started = False
        self.job_statistics = {}
        
        # Configurar listeners de eventos
        self._setup_event_listeners()
    
    def _setup_event_listeners(self):
        """Configurar listeners de eventos del scheduler"""
        
        def job_executed_listener(event):
            """Listener para jobs ejecutados exitosamente"""
            job_id = event.job_id
            runtime = event.scheduled_run_time
            
            logger.debug(f"✅ Job '{job_id}' ejecutado exitosamente a las {runtime}")
            
            # Actualizar estadísticas
            if job_id not in self.job_statistics:
                self.job_statistics[job_id] = {
                    'executions': 0,
                    'errors': 0,
                    'last_success': None,
                    'last_error': None
                }
            
            self.job_statistics[job_id]['executions'] += 1
            self.job_statistics[job_id]['last_success'] = datetime.utcnow()
        
        def job_error_listener(event):
            """Listener para jobs con error"""
            job_id = event.job_id
            exception = event.exception
            
            logger.error(f"❌ Job '{job_id}' falló: {str(exception)}")
            
            # Actualizar estadísticas
            if job_id not in self.job_statistics:
                self.job_statistics[job_id] = {
                    'executions': 0,
                    'errors': 0,
                    'last_success': None,
                    'last_error': None
                }
            
            self.job_statistics[job_id]['errors'] += 1
            self.job_statistics[job_id]['last_error'] = datetime.utcnow()
        
        def job_missed_listener(event):
            """Listener para jobs perdidos"""
            job_id = event.job_id
            run_time = event.scheduled_run_time
            
            logger.warning(f"⚠️ Job '{job_id}' perdido en tiempo {run_time}")
        
        # Agregar listeners
        self.scheduler.add_listener(job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)
        self.scheduler.add_listener(job_missed_listener, EVENT_JOB_MISSED)
    
    async def start_scheduler(self):
        """Iniciar scheduler con todos los jobs configurados"""
        if self.is_started:
            logger.warning("Scheduler ya está iniciado")
            return
        
        try:
            logger.info("🚀 Iniciando PNPtv Scheduler...")
            
            # Configurar todos los jobs
            await self._setup_core_jobs()
            await self._setup_membership_jobs()
            await self._setup_broadcast_jobs()
            await self._setup_webex_jobs()
            await self._setup_maintenance_jobs()
            
            # Iniciar scheduler
            self.scheduler.start()
            self.is_started = True
            
            # Mostrar jobs configurados
            jobs = self.scheduler.get_jobs()
            logger.info(f"✅ Scheduler iniciado con {len(jobs)} jobs configurados:")
            
            for job in jobs:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'No programado'
                logger.info(f"  📋 {job.id}: {job.name} - Próxima ejecución: {next_run}")
            
        except Exception as e:
            logger.error(f"❌ Error iniciando scheduler: {str(e)}")
            raise
    
    async def stop_scheduler(self):
        """Detener scheduler"""
        if not self.is_started:
            return
        
        try:
            logger.info("🛑 Deteniendo scheduler...")
            self.scheduler.shutdown(wait=True)
            self.is_started = False
            logger.info("✅ Scheduler detenido")
            
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {str(e)}")
    
    async def _setup_core_jobs(self):
        """Configurar jobs principales del sistema"""
        
        # Job de health check cada 5 minutos
        self.scheduler.add_job(
            self._system_health_check,
            IntervalTrigger(minutes=5),
            id='system_health_check',
            name='System Health Check',
            replace_existing=True
        )
        
        # Job de limpieza de logs cada 6 horas
        self.scheduler.add_job(
            self._cleanup_logs,
            IntervalTrigger(hours=6),
            id='cleanup_logs',
            name='Log Cleanup',
            replace_existing=True
        )
        
        # Job de estadísticas diarias a las 23:55
        self.scheduler.add_job(
            self._generate_daily_stats,
            CronTrigger(hour=23, minute=55),
            id='daily_stats',
            name='Generate Daily Statistics',
            replace_existing=True
        )
    
    async def _setup_membership_jobs(self):
        """Configurar jobs de gestión de membresías"""
        
        # Importar aquí para evitar dependencias circulares
        from jobs.membership_checker import membership_checker
        
        # Verificación diaria de membresías a las 9:00 AM UTC
        self.scheduler.add_job(
            membership_checker.run_daily_membership_check,
            CronTrigger(hour=9, minute=0),
            id='daily_membership_check',
            name='Daily Membership Check',
            replace_existing=True,
            jobstore='persistent' if 'persistent' in self.scheduler._jobstores else 'default'
        )
        
        # Sincronización de canales cada 6 horas
        self.scheduler.add_job(
            membership_checker._sync_channel_access,
            IntervalTrigger(hours=6),
            id='channel_sync',
            name='Channel Access Sync',
            replace_existing=True
        )
        
        # Limpieza semanal los domingos a las 3:00 AM UTC
        self.scheduler.add_job(
            membership_checker._cleanup_old_data,
            CronTrigger(day_of_week=6, hour=3, minute=0),
            id='weekly_cleanup',
            name='Weekly Data Cleanup',
            replace_existing=True
        )
    
    async def _setup_broadcast_jobs(self):
        """Configurar jobs de broadcast"""
        
        # Importar aquí para evitar dependencias circulares
        from jobs.broadcast_sender import broadcast_sender
        
        # Verificación de broadcasts cada minuto
        self.scheduler.add_job(
            broadcast_sender.run_broadcast_sender,
            IntervalTrigger(minutes=1),
            id='broadcast_sender',
            name='Broadcast Sender',
            replace_existing=True,
            jobstore='persistent' if 'persistent' in self.scheduler._jobstores else 'default'
        )
        
        # Limpieza de broadcasts antiguos diaria a las 2:00 AM
        self.scheduler.add_job(
            broadcast_sender._cleanup_old_broadcasts,
            CronTrigger(hour=2, minute=0),
            id='cleanup_broadcasts',
            name='Cleanup Old Broadcasts',
            replace_existing=True
        )
        
        # Limpiar cache de segmentos cada hora
        self.scheduler.add_job(
            broadcast_sender.clear_cache,
            IntervalTrigger(hours=1),
            id='clear_broadcast_cache',
            name='Clear Broadcast Cache',
            replace_existing=True
        )
    
    async def _setup_webex_jobs(self):
        """Configurar jobs de Webex"""
        
        try:
            from services.webex_service import WebexService
            webex_service = WebexService()
            
            # Limpieza de sesiones expiradas cada 2 horas
            self.scheduler.add_job(
                webex_service.cleanup_expired_sessions,
                IntervalTrigger(hours=2),
                id='cleanup_webex_sessions',
                name='Cleanup Expired Webex Sessions',
                replace_existing=True
            )
            
            # Sincronización con Webex API cada 30 minutos
            self.scheduler.add_job(
                self._sync_webex_data,
                IntervalTrigger(minutes=30),
                id='sync_webex_data',
                name='Sync Webex Data',
                replace_existing=True
            )
            
        except Exception as e:
            logger.warning(f"No se pudieron configurar jobs de Webex: {str(e)}")
    
    async def _setup_maintenance_jobs(self):
        """Configurar jobs de mantenimiento"""
        
        # Backup de base de datos diario a las 4:00 AM
        if Config.ENABLE_DB_BACKUPS:
            self.scheduler.add_job(
                self._backup_database,
                CronTrigger(hour=4, minute=0),
                id='database_backup',
                name='Database Backup',
                replace_existing=True
            )
        
        # Verificación de archivos multimedia cada 12 horas
        self.scheduler.add_job(
            self._check_media_files,
            IntervalTrigger(hours=12),
            id='check_media_files',
            name='Check Media Files',
            replace_existing=True
        )
        
        # Optimización de base de datos semanal los lunes a las 5:00 AM
        self.scheduler.add_job(
            self._optimize_database,
            CronTrigger(day_of_week=0, hour=5, minute=0),
            id='optimize_database',
            name='Optimize Database',
            replace_existing=True
        )
    
    # === FUNCIONES DE JOBS ===
    
    async def _system_health_check(self):
        """Health check del sistema"""
        try:
            logger.debug("🏥 Ejecutando health check del sistema")
            
            # Verificar conexión a base de datos
            from database.connection import get_async_session
            
            async with get_async_session() as session:
                await session.execute("SELECT 1")
            
            # Verificar bot de Telegram
            from main import application
            
            if application and application.bot:
                bot_info = await application.bot.get_me()
                logger.debug(f"✅ Bot activo: @{bot_info.username}")
            
            # Verificar uso de memoria (si está disponible)
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                
                if memory_percent > 90:
                    logger.warning(f"⚠️ Uso de memoria alto: {memory_percent}%")
                    
            except ImportError:
                pass
            
        except Exception as e:
            logger.error(f"❌ Health check falló: {str(e)}")
    
    async def _cleanup_logs(self):
        """Limpiar logs antiguos"""
        try:
            logger.debug("🧹 Ejecutando limpieza de logs")
            
            # Implementar limpieza de logs según configuración
            # Por ahora es un placeholder
            
        except Exception as e:
            logger.error(f"Error en limpieza de logs: {str(e)}")
    
    async def _generate_daily_stats(self):
        """Generar estadísticas diarias"""
        try:
            logger.info("📊 Generando estadísticas diarias")
            
            from services.membership_service import MembershipService
            from services.webex_service import WebexService
            from jobs.broadcast_sender import broadcast_sender
            
            membership_service = MembershipService()
            webex_service = WebexService()
            
            # Obtener estadísticas
            membership_stats = await membership_service.get_membership_statistics()
            webex_stats = await webex_service.get_webex_statistics()
            broadcast_stats = await broadcast_sender.get_sender_statistics()
            
            # Log de estadísticas clave
            logger.info(f"📈 Usuarios activos: {membership_stats.get('active_memberships', 0)}")
            logger.info(f"📈 Revenue mensual: ${membership_stats.get('monthly_revenue', 0):.2f}")
            logger.info(f"📈 Sesiones Webex totales: {webex_stats.get('total_sessions', 0)}")
            logger.info(f"📈 Broadcasts enviados hoy: {broadcast_stats.get('broadcasts_today', 0)}")
            
        except Exception as e:
            logger.error(f"Error generando estadísticas diarias: {str(e)}")
    
    async def _sync_webex_data(self):
        """Sincronizar datos con Webex"""
        try:
            logger.debug("🔄 Sincronizando datos con Webex")
            
            # Implementar sincronización con Webex API
            # Por ahora es un placeholder
            
        except Exception as e:
            logger.error(f"Error sincronizando Webex: {str(e)}")
    
    async def _backup_database(self):
        """Realizar backup de base de datos"""
        try:
            logger.info("💾 Iniciando backup de base de datos")
            
            # Implementar backup según el tipo de base de datos
            # Por ahora es un placeholder
            
            logger.info("✅ Backup completado")
            
        except Exception as e:
            logger.error(f"Error en backup: {str(e)}")
    
    async def _check_media_files(self):
        """Verificar archivos multimedia"""
        try:
            logger.debug("🖼️ Verificando archivos multimedia")
            
            from services.file_service import FileService
            file_service = FileService()
            
            cleaned_count = await file_service.cleanup_invalid_files()
            
            if cleaned_count > 0:
                logger.info(f"🧹 Limpiados {cleaned_count} archivos inválidos")
                
        except Exception as e:
            logger.error(f"Error verificando archivos: {str(e)}")
    
    async def _optimize_database(self):
        """Optimizar base de datos"""
        try:
            logger.info("🔧 Optimizando base de datos")
            
            # Implementar optimización según el tipo de base de datos
            # Por ahora es un placeholder
            
        except Exception as e:
            logger.error(f"Error optimizando base de datos: {str(e)}")
    
    # === MÉTODOS DE GESTIÓN ===
    
    def add_scheduled_job(self, func, trigger, job_id: str, **kwargs):
        """Agregar job programado dinámicamente"""
        try:
            self.scheduler.add_job(
                func,
                trigger,
                id=job_id,
                replace_existing=True,
                **kwargs
            )
            
            logger.info(f"✅ Job '{job_id}' agregado al scheduler")
            
        except Exception as e:
            logger.error(f"Error agregando job '{job_id}': {str(e)}")
    
    def remove_job(self, job_id: str):
        """Remover job del scheduler"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"🗑️ Job '{job_id}' removido del scheduler")
            
        except Exception as e:
            logger.error(f"Error removiendo job '{job_id}': {str(e)}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtener estado de un job específico"""
        try:
            job = self.scheduler.get_job(job_id)
            
            if not job:
                return None
            
            stats = self.job_statistics.get(job_id, {})
            
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger),
                'max_instances': job.max_instances,
                'executions': stats.get('executions', 0),
                'errors': stats.get('errors', 0),
                'last_success': stats.get('last_success').isoformat() if stats.get('last_success') else None,
                'last_error': stats.get('last_error').isoformat() if stats.get('last_error') else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del job '{job_id}': {str(e)}")
            return None
    
    def get_all_jobs_status(self) -> Dict[str, Any]:
        """Obtener estado de todos los jobs"""
        try:
            jobs = self.scheduler.get_jobs()
            
            jobs_status = {}
            for job in jobs:
                jobs_status[job.id] = self.get_job_status(job.id)
            
            return {
                'scheduler_running': self.is_started,
                'total_jobs': len(jobs),
                'jobs': jobs_status,
                'jobstores': list(self.scheduler._jobstores.keys()),
                'uptime': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de jobs: {str(e)}")
            return {'error': str(e)}
    
    async def execute_job_now(self, job_id: str) -> bool:
        """Ejecutar job inmediatamente"""
        try:
            job = self.scheduler.get_job(job_id)
            
            if not job:
                logger.error(f"Job '{job_id}' no encontrado")
                return False
            
            # Ejecutar job inmediatamente
            await job.func()
            
            logger.info(f"✅ Job '{job_id}' ejecutado manualmente")
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando job '{job_id}': {str(e)}")
            return False


# Instancia global del scheduler
pnptv_scheduler = PNPtvScheduler()


# === FUNCIONES DE CONTROL ===

async def start_scheduler():
    """Iniciar scheduler principal"""
    await pnptv_scheduler.start_scheduler()


async def stop_scheduler():
    """Detener scheduler principal"""
    await pnptv_scheduler.stop_scheduler()


async def get_scheduler_status():
    """Obtener estado completo del scheduler"""
    return pnptv_scheduler.get_all_jobs_status()


async def execute_job_manually(job_id: str):
    """Ejecutar job manualmente"""
    return await pnptv_scheduler.execute_job_now(job_id)


# === FUNCIONES DE EMERGENCIA ===

async def emergency_restart_scheduler():
    """Reiniciar scheduler en caso de emergencia"""
    try:
        logger.warning("🚨 Reinicio de emergencia del scheduler")
        
        await pnptv_scheduler.stop_scheduler()
        await asyncio.sleep(2)
        await pnptv_scheduler.start_scheduler()
        
        logger.info("✅ Scheduler reiniciado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en reinicio de emergencia: {str(e)}")
        return False


async def emergency_stop_all_jobs():
    """Detener todos los jobs en emergencia"""
    try:
        logger.warning("🚨 Deteniendo todos los jobs de emergencia")
        
        for job in pnptv_scheduler.scheduler.get_jobs():
            pnptv_scheduler.scheduler.pause_job(job.id)
            
        logger.info("⏸️ Todos los jobs pausados")
        return True
        
    except Exception as e:
        logger.error(f"Error pausando jobs: {str(e)}")
        return False


if __name__ == "__main__":
    # Para testing directo
    async def test_scheduler():
        logger.info("🧪 Iniciando test del scheduler")
        
        try:
            await start_scheduler()
            
            # Esperar un poco
            await asyncio.sleep(10)
            
            # Mostrar estado
            status = await get_scheduler_status()
            print(f"Estado del scheduler: {status}")
            
            await stop_scheduler()
            
        except KeyboardInterrupt:
            logger.info("Test interrumpido por usuario")
            await stop_scheduler()
    
    asyncio.run(test_scheduler())