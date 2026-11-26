# Arquitectura y decisiones

## Recursos y stack

El servidor del caso utiliza Ubuntu 24.04 LTS, aproximadamente 1 vCPU, 2 GiB de
RAM, 1 GiB de swap y 38 GB de disco. La revisión del 26 de noviembre encontró
aproximadamente 10 GB de disco libres. Es una fotografía del caso, no un objetivo
de dimensionamiento para otras tiendas.

Se eligió Nginx, PHP-FPM 8.3 y MariaDB instalados desde paquetes de Ubuntu.
Docker se evaluó, pero no fue necesario para operar estos dos sitios. El
desempeño debe reevaluarse con tráfico, plugins y tareas reales: no se hizo una
prueba de carga que demuestre una capacidad máxima.

## Límites entre componentes

| Componente | Función | Exposición prevista |
|---|---|---|
| SSH | Administración con claves y host conocido | Puerto administrativo autorizado |
| Nginx frontal | TLS, redirecciones y rutas públicas | HTTP/HTTPS |
| Nginx de WordPress | Enrutamiento a los sitios restaurados | Solo loopback, puerto 8080 |
| PHP-FPM | Ejecutar PHP como usuario del sitio | Sockets Unix por sitio |
| MariaDB | Bases y usuarios independientes | Acceso local; no publicar 3306 |
| systemd timers | Ejecutar WP-Cron como usuario de cada sitio | Sin listener de red |
| Certbot | Emitir y renovar certificados | Validación HTTP por webroot |

En el servidor actual se conservó la separación frontal/backend usada durante
la migración. Las plantillas de este repositorio describen ese patrón; no
pretenden reemplazar toda la configuración de Nginx de una máquina existente.

## Directorios

```text
/srv/www/
├── embrylab/
│   ├── public/                 # WordPress
│   ├── embrylab_downloads/     # Productos; fuera del webroot
│   └── php-sessions/
└── capadoccia/
    ├── public/                 # WordPress
    └── php-sessions/

/var/lib/wordpress-migration/   # Ejemplo: área privada de copia, no webroot
/var/backups/                  # Respaldos; permisos restringidos
```

Cada sitio tiene usuario Linux propio, shell no interactiva, pool PHP propio y
credenciales de base de datos independientes. Nginx tiene el acceso mínimo de
lectura que necesita. La configuración real utilizó directorios de sitio con
grupo de lectura controlado y `wp-config.php` accesible únicamente al usuario
que ejecuta PHP. No se aplica `chmod -R 777`.

## PHP y memoria

Los pools se prepararon en modo `ondemand`, con un máximo inicial de dos
procesos por sitio y liberación de procesos inactivos. Los ejemplos usan 256 MiB
de `memory_limit`, subida de 64 MiB y POST de 72 MiB. Estos límites son un punto
de partida: `memory_limit` no representa toda la RAM de un proceso PHP y dos
pools pueden competir por la misma memoria del VPS.

Revisar RSS, swap, latencia y tareas de WooCommerce antes de aumentar concurrencia.
La referencia de las directivas es el [manual de PHP-FPM](https://www.php.net/manual/en/install.fpm.configuration.php).

## Red y TLS

El firewall parte de denegar entrada. Se conserva SSH antes de habilitar reglas
de red; no se cambia una política de acceso a ciegas desde la única sesión
disponible. Los puertos públicos adicionales se abren únicamente cuando el
servicio correspondiente está configurado.

Los ejemplos exigen una dirección IPv4 de escucha explícita en el inventario.
En este VPS existía otro listener HTTPS privado; escuchar indiscriminadamente
en todas las interfaces podía causar conflictos. La dirección de documentación
del ejemplo debe sustituirse antes de instalar una plantilla.

El frontal informa a WordPress de la conexión HTTPS. El backend solo acepta
conexiones loopback; no debe publicarse directamente ni confiar en cabeceras de
proxy provenientes de clientes arbitrarios. En este patrón, el backend fija
`HTTPS=on` al pasar solicitudes PHP porque su entrada autorizada es el frontal
TLS. Revisar también las peticiones locales de mantenimiento.

## Extensiones posteriores

El correo de EmbryLab usa Postfix, Dovecot y OpenDKIM. El editor de pruebas es
estático y está protegido por autenticación en Nginx. Son servicios adicionales,
no dependencias necesarias para copiar y restaurar WordPress. El editor procesa
archivos de bordado en el navegador y no requiere un servidor Node permanente.
