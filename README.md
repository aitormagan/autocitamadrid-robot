# Telegram Bot - Autocita Madrid

[![Deploy](https://github.com/aitormagan/autocitamadrid-robot/actions/workflows/deploy.yml/badge.svg)](https://github.com/aitormagan/autocitamadrid-robot/actions/workflows/deploy.yml)

*[Producto decomisionado]*

Robot de Telegram que te notificaba cuando la Comunidad de Madrid permitía vacunarse a gente de la edad seleccionada 
por el usuario.

Para el funcionamiento se disponía de la siguiente infraestructura sobre AWS:

* Un API Gateway conectado a una lambda que procesa los mensajes enviados por los usuarios:
  * Inicio de conversación
  * Inclusión en el sistema de notificación (en base a su edad)
  * Cancelación de la notificación
  * Ayuda, etc.
* Otra lambda, que se ejecuta cada 20 minutos, y que comprueba si ha cambiado la edad para pedir cita y notificar a 
quien corresponda.

Para que Telegram llame a la API desplegada, hay que acceder a la siguiente URL: `
https://api.telegram.org/bot<BOT_TOKEN>/setWebHook?url=<APIGW_URL>`