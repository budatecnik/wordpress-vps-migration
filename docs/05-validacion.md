# Validación y evidencia

## Dos niveles de evidencia

**Pruebas del caso real:** resultados observados durante la migración y la
operación posterior. Las evidencias originales permanecen privadas. Esta página
resume hechos sin publicar credenciales, pedidos ni registros completos.

**Pruebas de este repositorio:** pruebas offline con datos sintéticos sobre las
herramientas públicas y sus límites. No se conectan al hosting ni cobran pedidos.
Un CI verde valida este nivel, no el servidor de producción.

## Resultados históricos registrados

| Área | Resultado observado | Alcance |
|---|---|---|
| Stack | Nginx, PHP-FPM y MariaDB activos | Confirmado nuevamente el 26-11-2026 por consulta de solo lectura |
| Copia | Dumps, hashes y comparación de archivos | No se publican los datos originales |
| Descargas EmbryLab | 807 referencias de descarga resueltas durante la migración | Conteo histórico; no inventario permanente |
| Descarga autenticada | HTTP 200, tamaño y SHA-256 coincidentes; permiso inválido rechazado | Prueba sintética en copia privada, sin pasarela de pago |
| Capadoccia Tour | HTTPS y respuestas públicas correctas; pruebas de idiomas | No equivale a revisar todo el contenido editorial |
| HTTPS | Certificados y simulaciones de renovación correctos | Se requiere seguimiento operativo |
| WP-Cron | Ambos servicios con resultado success | Confirmado nuevamente el 26-11-2026 |
| Correo EmbryLab | Recepción local, autenticación cifrada y firma DKIM probadas | La entrega externa sigue bloqueada por el proveedor |
| Editor de staging | 33 archivos publicados comparados por SHA-256, acceso protegido y motor probado | Aplicación externa al repositorio; selección nativa de archivos pendiente en Chrome normal |

La migración no validó una compra con cargo real. Los pagos de EmbryLab se
mantuvieron controlados durante las pruebas. Revisar el estado comercial antes
de habilitar ventas y no confundir catálogo accesible con compra verificada.

## Checklist antes de un cutover

- [ ] Existe una copia del origen y una exportación coherente de la base.
- [ ] Se conocen motores de tablas y restricciones de consistencia.
- [ ] Se incluyeron archivos privados fuera del webroot y destinos de symlinks.
- [ ] La restauración se realizó en una base y ubicación separadas.
- [ ] Se ajustaron rutas en datos serializados y en plugins personalizados.
- [ ] Portada, recursos, login y páginas esenciales responden correctamente.
- [ ] WooCommerce resuelve descargas y rechaza permisos inválidos.
- [ ] Se acordó una pausa de escrituras y una sincronización final.
- [ ] Se revisaron tareas y correos que podrían activarse al salir de preview.
- [ ] El rollback contempla datos nuevos, no solo el registro DNS.

## Verificaciones públicas disponibles

```bash
python3 scripts/check_site.py embrylab.com cappadociatour.help
python3 scripts/check_smtp.py --host gmail-smtp-in.l.google.com --family 4
```

El segundo comando debe ejecutarse desde el VPS para comprobar su salida SMTP.
No envía mensajes: solo abre TCP 25 y revisa el saludo. Una conexión correcta
no demuestra autenticación SPF/DKIM/DMARC, aceptación del mensaje ni recepción
en la bandeja principal.

Para la auditoría de descargas, ejecutar como el usuario de WordPress y señalar
explícitamente la raíz privada permitida:

```bash
sudo -u embrylab env PRIVATE_DOWNLOAD_ROOT=/srv/www/embrylab/embrylab_downloads \
  php /opt/wordpress-migration/wp-cli.phar --path=/srv/www/embrylab/public \
  eval-file scripts/audit_downloads.php
```

La ruta del script debe ser legible por ese usuario y encontrarse fuera del
webroot. La auditoría no modifica metadatos y solo muestra contadores. Para
descargas servidas desde otros dominios se necesita una revisión específica.

## Pruebas offline del repositorio

```bash
make check
make test
```

Se comprueban la ausencia de ejecución en modo plan, la obligación de `--apply`,
la prohibición de borrado durante la copia, validaciones de rutas y plantillas,
parsing literal de PHP, separación de opciones MySQL/MariaDB, hashes de archivos,
rechazo de symlinks, redirecciones HTTPS y familia de red en SMTP. También se
revisa el límite de archivos publicables y patrones de secretos frecuentes.

La sintaxis de las plantillas PHP y Nginx requiere sus intérpretes. Las
comprobaciones adicionales ejecutadas durante la preparación se anotan en
`docs/06-estado-y-limitaciones.md`; no se inventa un resultado si una herramienta
no está disponible en CI.
