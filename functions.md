# Funciones del Bot PNPtv

Este documento detalla las principales funciones y características del bot PNPtv, basado en el análisis de su código fuente.

## 1. Gestión de Usuarios y Onboarding (`handlers/start.py`, `services/user_service.py`)

*   **Comando /start:**
    *   Maneja el inicio de la interacción del usuario con el bot.
    *   Detecta si el usuario es nuevo o existente.
    *   Para usuarios nuevos, solicita la selección de idioma (español/inglés).
    *   Para usuarios existentes, actualiza la última actividad y redirige al menú principal o al proceso de aceptación de términos si es necesario.
*   **Selección de Idioma:**
    *   Permite al usuario elegir su idioma preferido (español o inglés).
    *   Guarda la preferencia de idioma en la base de datos.
*   **Aceptación de Términos y Condiciones:**
    *   Presenta los términos y condiciones al usuario.
    *   Registra la aceptación o rechazo de los términos.
    *   Completa el proceso de onboarding del usuario al aceptar los términos.
*   **Servicio de Usuario (`UserService`):**
    *   Creación y actualización de usuarios en la base de datos.
    *   Actualización de la última actividad del usuario.
    *   Gestión del estado de onboarding del usuario.
    *   Obtención de preferencias de idioma del usuario.

## 2. Gestión de Membresías y Suscripciones (`services/membership_service.py`, `jobs/membership_checker.py`)

*   **Servicio de Membresía (`MembershipService`):**
    *   Gestión de la lógica de suscripciones de usuarios.
    *   Verificación del estado de la membresía (activa, expirada, etc.).
    *   Funciones para activar, desactivar o extender membresías.
*   **Verificador de Membresías (`membership_checker.py`):**
    *   Tarea programada (job) que verifica periódicamente el estado de las membresías.
    *   Envía recordatorios a los usuarios antes de que expire su suscripción.
    *   Maneja la desactivación automática de membresías expiradas.

## 3. Pagos (`services/payment_service.py`, `webhooks/payment_webhook.py`)

*   **Servicio de Pagos (`PaymentService`):**
    *   Integración con un sistema de pagos externo (Bold, según `config.py`).
    *   Generación de enlaces de pago.
    *   Procesamiento de confirmaciones de pago.
*   **Webhook de Pagos (`payment_webhook.py`):**
    *   Endpoint para recibir notificaciones de pago del sistema externo.
    *   Actualiza el estado de la membresía del usuario tras un pago exitoso.

## 4. Gestión de Canales y Grupos (`services/channel_manager.py`)

*   **Gestor de Canales (`ChannelManager`):**
    *   Manejo de la adición y eliminación de usuarios a canales y grupos de Telegram (canales de suscripción, grupo VIP).
    *   Verificación de la membresía del usuario antes de permitir el acceso a contenido exclusivo.

## 5. Funciones de Administración (`handlers/admin.py`, `handlers/broadcast.py`, `jobs/broadcast_sender.py`)

*   **Comandos de Administración:**
    *   Permite a los administradores gestionar usuarios, membresías y configuraciones del bot.
    *   Funciones para ver el estado de usuarios, extender suscripciones manualmente, etc.
*   **Difusión de Mensajes (`handlers/broadcast.py`, `jobs/broadcast_sender.py`):**
    *   Permite a los administradores enviar mensajes masivos a todos los usuarios o a grupos específicos.
    *   Manejo de la cola de mensajes para difusión (`broadcast_sender.py`).

## 6. Menú Principal y Navegación (`handlers/menu.py`, `keyboards/inline.py`)

*   **Menú Principal:**
    *   Presenta las opciones principales del bot al usuario (ej. Ver mi membresía, Comprar suscripción, Contacto).
*   **Teclados Inline:**
    *   Generación de teclados inline dinámicos para la interacción del usuario (selección de idioma, aceptación de términos, opciones de menú).

## 7. Integración con Webex (`handlers/webex.py`, `services/webex_service.py`)

*   **Servicio Webex (`WebexService`):**
    *   Funcionalidad para interactuar con la API de Webex.
    *   Posiblemente para gestionar reuniones, enviar notificaciones o integrar con espacios de Webex.

## 8. Notificaciones y Mensajería (`services/notification_service.py`)

*   **Servicio de Notificaciones (`NotificationService`):**
    *   Envío de mensajes y notificaciones a los usuarios a través de Telegram.
    *   Manejo de mensajes seguros y edición de mensajes existentes.

## 9. Utilidades y Helpers (`utils/`)

*   **Validadores:**
    *   Funciones para validar entradas de usuario.
*   **Helpers:**
    *   Funciones de utilidad general, como extracción de información de usuario de Telegram, determinación de idioma, etc.
*   **Decoradores:**
    *   Decoradores para aplicar lógica común a los handlers (ej. autenticación, verificación de administrador).

## 10. Modelos de Datos (`database/models.py`)

*   Define la estructura de las tablas de la base de datos (usuarios, membresías, etc.).

Esta es una descripción general de las funciones principales. Para un análisis más detallado, se requeriría una inmersión más profunda en cada archivo y sus interacciones.



## Actualización: Funcionalidad de Administración Mejorada

### 5.1. Gestión de Suscriptores Manual (Nuevo)

Se ha añadido una nueva opción al panel de administración para permitir el ingreso manual de suscriptores. Esta funcionalidad se accede a través del botón "➕ Agregar Suscriptor" en el panel de administración y sigue un flujo conversacional:

*   **Inicio (`admin_add_subscriber` callback)**: El administrador inicia el proceso desde el panel.
*   **Solicitud de Nombre de Usuario**: El bot pide el nombre de usuario de Telegram (sin @) del suscriptor a añadir.
*   **Solicitud de Duración**: Una vez proporcionado el nombre de usuario, el bot solicita la duración de la suscripción en días.
*   **Creación de Suscripción**: El bot verifica si el usuario existe en la base de datos (es decir, si ha iniciado el bot al menos una vez) y, si es así, le otorga una membresía por la duración especificada.
*   **Cancelación**: El proceso puede ser cancelado en cualquier momento con el comando `/cancel`.

### 5.2. Funciones del Administrador (Resumen)

Las funciones que un administrador puede ejecutar a través del panel de administración son:

*   **Panel de Administración (`/admin` comando)**: Acceso al menú principal de administración.
*   **Editor de Menú (`admin_menu_editor`)**:
    *   Crear nuevas secciones de menú.
    *   Editar texto de secciones existentes.
    *   Cambiar multimedia (imágenes/videos) de secciones.
    *   Editar botones asociados a secciones.
    *   Configurar opciones de secciones.
    *   Eliminar secciones de menú.
    *   Previsualizar el menú.
*   **Estadísticas (`admin_stats`)**: Acceso a métricas y datos del bot (implementación detallada no visible en los handlers proporcionados, pero la opción existe).
*   **Programar Broadcast (`admin_broadcast`)**:
    *   Enviar mensajes masivos a diferentes segmentos de usuarios (nuevos, activos, cancelados, todos).
    *   Seleccionar el idioma del broadcast (español, inglés, ambos).
*   **Gestión Webex (`admin_webex`)**:
    *   Programar eventos de Webex.
    *   Ver eventos activos.
    *   Gestionar llamadas privadas.
    *   Acceder a estadísticas de Webex.
*   **Gestión de Usuarios (`admin_users`)**: Funcionalidad para gestionar usuarios (implementación detallada no visible en los handlers proporcionados, pero la opción existe).
*   **Gestión de Pagos (`admin_payments`)**: Funcionalidad para gestionar pagos (implementación detallada no visible en los handlers proporcionados, pero la opción existe).
*   **Agregar Suscriptor (`admin_add_subscriber`)**: Nueva funcionalidad para añadir suscriptores manualmente, como se detalla arriba.

Estas funciones permiten a los administradores un control completo sobre el contenido del bot, la comunicación con los usuarios y la gestión de suscripciones y eventos.

