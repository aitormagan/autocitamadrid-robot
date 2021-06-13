# Telegram Bot - Autocita Madrid

Robot de Telegram que te notifica en cuanto la Comunidad de Madrid permite vacunarse a gente de la edad seleccionada 
por el usuario.

Hay dos programas principales:

* `main.py`: Este es el que se conecta a la API de Telegram y obtiene los mensajes escritos por los usuarios: 
  * Inicio de conversación
  * Inclusión en el sistema de notificación
  * Cancelación de la notificación
* `main_checker.py`: Este es el que consulta la web de citación y comprueba cuál es la edad mínima que se permite en el
sistema de autocitación.

De esta forma, el primero debe instalarse como servicio o demonio del sistema operativo para que ejecute de forma 
continuada, mientras que el segundo puede ejecutarse dentro de un cronjob que lo levante cada cierto tiempo.