# Operación, respaldos y recuperación

## Comprobaciones después de publicar

Revisar estado de servicios, logs privados, disco, memoria, swap, latencia y
colas de tareas. No publicar `wp-config.php`, cookies, dumps ni logs de pedidos.

```bash
systemctl is-active nginx php8.3-fpm mariadb certbot.timer
systemctl show embrylab-wp-cron.service capadoccia-wp-cron.service \
  -p Id -p Result -p ExecMainStatus
systemctl list-timers --all
```

Una unidad `oneshot` puede quedar `inactive` después de terminar correctamente.
Hay que revisar el resultado y su temporizador, no interpretar ese estado
aislado como un fallo.

## WP-Cron

El caso usa un servicio y timer por sitio, ejecutados como el usuario Linux del
sitio. `DISABLE_WP_CRON` permanece activado para evitar depender del tráfico
web. Revisar la cola importada antes de la primera ejecución: puede contener
notificaciones y tareas antiguas.

Las plantillas se instalan con nombres como `embrylab-wp-cron.service` y
`embrylab-wp-cron.timer`. El nombre del timer debe coincidir con su directiva
`Unit`. Verificar previamente la ruta del binario PHP y de WP-CLI.

## HTTPS y renovación

El webroot ACME se prepara fuera de WordPress y se mantiene accesible desde
HTTP. Los registros A/AAAA y el firewall deben dirigir los desafíos al servidor
correcto. No instalar un vhost que referencia certificados todavía inexistentes.

Ejemplo, con dominios de documentación que hay que sustituir:

```bash
sudo certbot certonly --webroot -w /var/www/letsencrypt \
  -d embrylab.example.invalid -d www.embrylab.example.invalid
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable --now certbot.timer
sudo certbot renew --dry-run --no-random-sleep-on-renew
```

El hook generado valida Nginx antes de recargarlo. El caso comprobó la
renovación en simulación; esto no constituye una garantía permanente. Revisar
los resultados posteriores y probar también la recarga de los servicios de
correo si utilizan el mismo certificado. No copiar claves privadas al repositorio.
Referencia: [guía de Certbot](https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates).

## Respaldos

Separar tres elementos:

1. **Copia de migración:** permite reconstruir el estado usado durante el traslado.
2. **Respaldos operativos:** capturan el estado posterior de archivos, base y configuración.
3. **Copia externa:** permite recuperar información si se pierde el VPS o su disco.

Un respaldo en el mismo disco no protege frente a la pérdida de ese disco.
Definir frecuencia, retención, cifrado, ubicación externa y responsable según
la tolerancia real a pérdida de pedidos y contenido. No se afirma aquí que
exista una política externa completa y probada para ambos sitios.

Respaldar de forma coordinada bases, `wp-content`, descargas privadas y
configuraciones necesarias. Conservar hashes y metadatos fuera de Git. Probar
una restauración en un entorno aislado y registrar su resultado.

## Rollback de configuración

Antes de cada cambio guardar una copia privada, registrar qué se modificó y
probar `nginx -t` y `php-fpm8.3 -t`. Si una configuración nueva falla, restaurar
la anterior y volver a validar antes de recargar. Evitar reiniciar servicios
como primera respuesta a un error que aún no se ha diagnosticado.

Este repositorio no incluye un botón genérico de rollback: la configuración
anterior y el contenido posterior al corte pertenecen a cada operación.

## Rollback después del cambio de DNS

Cambiar DNS hacia Zomro **no deshace** los pedidos o cambios creados en el VPS.
Antes de volver atrás:

1. Poner en mantenimiento o detener escrituras en el sistema activo.
2. Respaldar su estado actual, aunque el sitio presente un fallo.
3. Identificar pedidos, usuarios, archivos o contenido posteriores al corte.
4. Decidir qué sistema será la fuente de verdad y reconciliar la diferencia.
5. Restaurar en un destino separado y verificar antes de dirigirle visitantes.
6. Cambiar DNS, observar propagación y evitar dos instalaciones aceptando
   escrituras de forma simultánea.

No importar un dump antiguo sobre producción para «volver atrás» sin tratar los
datos nuevos. Tampoco eliminar una copia del origen antes de cerrar este análisis.

## Cierre del hosting anterior

Confirmar con el administrador: backup externo restaurable, DNS estabilizado,
validaciones funcionales y ausencia de escrituras en Zomro. Después revisar
servicios contratados, renovación automática y facturas en el panel del proveedor.
La cancelación del hosting es una decisión administrativa separada de la migración.
