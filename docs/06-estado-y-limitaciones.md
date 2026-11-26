# Estado del proyecto

**Fecha de referencia: 26 de noviembre de 2026.** Este documento es un registro
del caso, no un monitor en tiempo real.

## Completado en el caso real

- Preparación del VPS existente y conservación de una carga anterior y respaldos.
- Stack nativo Nginx, PHP-FPM y MariaDB con separación de sitios.
- Copia y restauración de EmbryLab y Capadoccia Tour desde Zomro.
- Publicación de ambos dominios en el VPS.
- HTTPS y configuración de renovación automática.
- Temporizadores de WordPress independientes; última consulta con resultado correcto.
- Adaptación y comprobación de referencias de descarga de WooCommerce.
- Creación de `support@embrylab.com` y configuración del remitente en WooCommerce.
- Publicación y verificación de MX, SPF, DKIM, DMARC y PTR de EmbryLab.
- Publicación posterior de un editor estático de staging protegido por contraseña.

## Pendiente o no demostrado

| Elemento | Situación al cierre de esta versión |
|---|---|
| Correo externo | InterServer bloquea la salida IPv4 por TCP 25. Soporte programó habilitarla el **4 de diciembre de 2026**. Aún no se verificó el desbloqueo ni la entrega a Gmail. |
| Mensajes en cola | Pueden caducar antes del desbloqueo. Revisar el estado y enviar una prueba nueva; no asumir que se entregarán automáticamente. |
| Pagos | No existe una prueba documentada de compra con cargo real y confirmación externa de principio a fin. |
| Hosting de Zomro | La migración no acredita su cancelación. La baja y las renovaciones requieren comprobación administrativa separada. |
| Respaldos operativos | No se afirma una política externa completa para ambos sitios con ejercicios de recuperación y retención aprobados. |
| Capacidad | Sin benchmark de carga ni compromiso de disponibilidad. |
| Editor | Despliegue inicial manual. No hay actualización automática desde GitHub; el selector nativo de archivos requiere prueba en Chrome normal. |
| Navegación Capadoccia | Durante las pruebas se observó un ancla ausente en una página española. No se acredita su corrección en este repositorio. |

## Incidentes y aprendizajes

### TLS correcto, aviso persistente en una sesión de Chrome

El certificado, la redirección HTTPS y los recursos revisados eran válidos. Una
sesión de incógnito aparecía segura. Esto acotó el problema a la sesión habitual
del navegador, pero no se documentó una causa definitiva ni una reparación
universal. No se desactivó la verificación de certificados para ocultar el aviso.

### SMTP: comprobar la familia de red utilizada

Una prueba inicial de conectividad eligió IPv6, mientras Postfix estaba
configurado para IPv4. La prueba real dejó el mensaje diferido. Las conexiones
IPv4 a los MX de Gmail agotaron el tiempo y el proveedor confirmó su política
de bloqueo. Por eso la herramienta pública permite elegir explícitamente IPv4
o IPv6. No se propone IPv6 como mecanismo para eludir la política del proveedor.

### Clave de despliegue y clave de host son distintas

GitHub aceptó una deploy key de solo lectura para el editor. La primera conexión
del usuario de despliegue falló porque faltaba registrar la identidad del host
de GitHub. Se incorporó la clave oficial y la lectura del repositorio funcionó.
No se deshabilitó `StrictHostKeyChecking` y no se publicó ninguna clave privada.

### Copia, publicación y baja son procesos diferentes

Una copia correcta no prueba que el DNS público cambió; un DNS correcto no
cancela el servicio anterior; un sitio visible no prueba pagos o correo. Cada
paso necesita su propia verificación y un responsable.

## Qué representa este repositorio público

Documentación del trabajo realizado y herramientas nuevas derivadas de ese
proceso, con parámetros de ejemplo. No es una exportación literal del servidor
ni garantiza reproducir una migración completa sin intervención administrativa.
Las herramientas deben probarse en un entorno propio antes de usarse con datos
reales. Los originales operativos y los datos migrados permanecen privados.

## Verificación de esta entrega pública

Preparación del 26-11-2026:

- 32 pruebas offline pasadas con datos sintéticos.
- Sintaxis de Python, JSON, shell y estructura YAML del workflow comprobadas.
- Plantillas generadas para los dos sitios y enlaces locales de Markdown revisados.
- Auditor PHP y protección de preview comprobados con `php -l`, sin ejecutarlos.
- Seis bloques Nginx comprobados con un certificado de prueba y listeners de
  loopback temporales; no se instalaron ni recargaron configuraciones públicas.
- Cuatro unidades systemd y dos pools PHP-FPM pasaron comprobaciones de sintaxis
  en archivos temporales, sin iniciar servicios.
- Revisión automatizada de los límites de publicación y patrones de secretos.

La comprobación de sintaxis no demuestra los permisos ni el comportamiento de
una instalación futura. La ejecución remota de GitHub Actions queda pendiente
de la publicación del repositorio; no se muestra como CI ya ejecutado.
