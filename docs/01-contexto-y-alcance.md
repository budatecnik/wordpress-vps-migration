# Contexto y alcance

## Responsable y objetivo

Daniel, [budatecnik](https://github.com/budatecnik), administra el VPS y documenta
la migración. El objetivo fue trasladar dos instalaciones WordPress desde Zomro
a InterServer, conservando contenido, URLs y funcionalidades, con un proceso
revisable y una alternativa de recuperación.

El VPS ya existía. La fase de preparación comprendió inventario, acceso SSH,
revisión de firewall, conservación de una carga anterior e instalación del stack
web. No se reemplazó el servidor ni se automatizó su contratación.

## Sitios del caso

| Nombre comercial | Dominio | Identificador Linux utilizado |
|---|---|---|
| EmbryLab | `embrylab.com` | `embrylab` |
| Capadoccia Tour | `cappadociatour.help` | `capadoccia` |

La escritura del identificador Linux y la del dominio son distintas por motivos
históricos. Los ejemplos preservan esa distinción para no mezclar directorios,
sockets o temporizadores de los dos sitios.

EmbryLab incluye WooCommerce y archivos de descarga almacenados fuera del
directorio público. Capadoccia Tour incluye contenido multilingüe. Copiar solo
`public_html` no cubría todo el alcance de EmbryLab.

## Incluido

- Arquitectura nativa Nginx, PHP-FPM y MariaDB para un VPS pequeño.
- Copias privadas de archivos y exportaciones de bases de datos.
- Adaptación de rutas, protecciones de preview y validación de descargas.
- Publicación por DNS, certificados y tareas programadas.
- Procedimientos de respaldo, rollback y diagnóstico de correo.
- Herramientas de planificación, copia opt-in, integridad y verificación.

## Excluido

- Copias de contenido comercial, bases de datos, pedidos o datos personales.
- Código fuente de WordPress, plugins, temas o del editor de bordados.
- Aprovisionamiento de una cuenta InterServer, cancelación del hosting Zomro o
  administración automática de cuentas de registradores.
- Un sistema genérico de alta disponibilidad, failover o escalado automático.
- Afirmaciones de migración sin interrupción, de pagos validados o de entrega
  garantizada a la bandeja principal del correo.

## Forma de trabajo

Primero se inspeccionó; después se prepararon cambios y se validó su sintaxis.
Las operaciones administrativas que requerían contraseña se ejecutaron desde
la terminal del administrador. Se usaron permisos temporales y acotados cuando
fueron necesarios; se retiraron al finalizar cada preparación.

Este repositorio no propone habilitar `NOPASSWD: ALL`. Para tareas repetidas,
conviene definir comandos concretos y permisos mínimos, una vez conocido el
procedimiento que se necesita ejecutar.

Los scripts originales del trabajo permanecen en `ops/` en la estación de
trabajo de Daniel. Esa carpeta no forma parte de la publicación. Los ejemplos
del repositorio fueron separados de los parámetros privados del caso real.
