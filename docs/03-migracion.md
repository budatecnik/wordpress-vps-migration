# Procedimiento de migración

Este procedimiento describe las fases del caso y cómo adaptar los ejemplos.
No ejecutar los comandos contra una instalación publicada sin revisar antes
backups, rutas, permisos y el estado de escrituras de cada sitio.

## 1. Inventario y preparación

Registrar versiones, usuarios, puertos, servicios, uso de disco y política de
respaldos. Confirmar acceso administrativo y mantener una sesión de recuperación.

```bash
bash scripts/audit_vps.sh
```

El script no instala nada ni cambia servicios. Su salida se conserva como
evidencia privada; no se publica sin revisión. Antes de instalar paquetes,
revisar el plan de APT y confirmar que no eliminará cargas ajenas al proyecto.

Para un VPS nuevo equivalente, los componentes base del caso fueron:

```bash
sudo apt-get update
sudo apt-get install nginx mariadb-server php8.3-fpm php8.3-mysql \
  php8.3-curl php8.3-gd php8.3-mbstring php8.3-xml php8.3-zip \
  php8.3-intl php8.3-opcache rsync certbot
```

Esta es una receta de referencia, no una operación realizada por los scripts.
Instalar paquetes puede iniciar servicios. Revisar previamente la red y el
servidor existente. Verificar también la autenticidad de WP-CLI y guardarlo
fuera del webroot. Los ejemplos systemd esperan un PHAR verificado en
`/opt/wordpress-migration/wp-cli.phar`; adaptar esa ruta si se utiliza otra.

## 2. Inventario de origen y exportación de base de datos

Confirmar que la clave SSH y la identidad del hosting estén verificadas.
Inventariar rutas, tablas, motores de almacenamiento, rutinas y eventos.
`scripts/export_wordpress_db.py` lee definiciones literales de `wp-config.php`
sin ejecutar PHP y guarda las credenciales temporalmente en un archivo 0600.
No acepta configuraciones dinámicas basadas en variables de entorno.

Ejecutar en el host que puede leer ese `wp-config.php` y acceder a la base:

```bash
umask 077
python3 scripts/export_wordpress_db.py inspect /ruta/privada/wp-config.php
python3 scripts/export_wordpress_db.py dump /ruta/privada/wp-config.php \
  --flavor mysql > /ruta/privada/site.sql
```

Si se ejecuta a través de SSH, el script debe estar disponible en el origen y
el dump debe viajar directamente hacia una carpeta privada del destino. No
imprimirlo en la terminal ni copiarlo al repositorio.

`--single-transaction` proporciona una instantánea coherente para tablas
transaccionales bajo sus condiciones de uso. No resuelve por sí solo tablas
no transaccionales ni coordina escrituras de archivos y pedidos. Revisar los
motores y definir una pausa de escrituras para el corte final.

## 3. Copia de archivos, incluida la zona privada

Crear un inventario local ignorado por Git:

```bash
cp config/inventory.example.json config/config.local.json
```

Completar hostname, usuario, clave SSH y rutas reales. El área de migración debe
estar fuera de los webroots y tener permisos privados. Los valores de ejemplo
no se aceptan para ejecutar una copia.

```bash
# Solo plan; no crea directorios ni abre conexiones.
python3 scripts/migrate_files.py --config config/config.local.json --site embrylab

# Copia explícita hacia el área privada de migración.
python3 scripts/migrate_files.py --config config/config.local.json \
  --site embrylab --mode copy --apply

# Comparación de contenido; nunca elimina archivos.
python3 scripts/migrate_files.py --config config/config.local.json \
  --site embrylab --mode verify
```

Repetir para `capadoccia`. El modo de copia no usa `--delete`. La comparación
sí puede mostrar qué sobra en el destino mediante `--delete --dry-run`, sin
borrar nada. Las salidas operativas no se adjuntan a un issue público.

Se usa `--safe-links`: los enlaces que apuntan fuera del árbol de origen no se
copian. Hay que inventariarlos y migrar sus destinos explícitamente cuando
formen parte del sitio. En EmbryLab se necesitó una colección separada de
descargas fuera de `public_html`.

## 4. Integridad y respaldo verificable

Validar el formato y la finalización del dump, no solo que exista un archivo
comprimido. Conservar hashes y tamaños de archivos en un manifiesto privado.

```bash
python3 scripts/file_manifest.py create /ruta/privada/copia \
  --output /ruta/privada/manifest.json
python3 scripts/file_manifest.py verify /ruta/privada/copia \
  --manifest /ruta/privada/manifest.json
```

Un hash coincidente demuestra integridad del archivo comparado; no demuestra
que la base pueda restaurarse ni que la aplicación funcione. Ensayar la
restauración antes de dar por verificado un respaldo.

## 5. Restauración privada

Crear bases y usuarios independientes, limitar permisos a la base del sitio e
importar el dump en una base **nueva**, nunca sobre la base productiva existente.
Definir credenciales nuevas fuera de Git. Copiar archivos hacia los directorios
del sitio sin modificar la copia original conservada.

Generar las plantillas sin instalarlas:

```bash
python3 scripts/render_templates.py --config config/config.local.json \
  --site embrylab --output private/rendered/embrylab
```

Revisar el pool PHP, el backend Nginx y las protecciones de preview. La plantilla
MU requiere que WordPress esté marcado como staging. Configurar también:

```php
define('WP_ENVIRONMENT_TYPE', 'staging');
define('DISABLE_WP_CRON', true);
define('WP_HTTP_BLOCK_EXTERNAL', true);
```

Durante esta fase se bloquean el correo de WordPress y las pasarelas disponibles
de WooCommerce. El filtro de correo devuelve fallo deliberadamente: no simula
una entrega real. Plugins que usan conexiones ajenas a las APIs de WordPress
requieren revisión adicional. No ejecutar pedidos de pago reales.

## 6. Adaptación de rutas y pruebas

Actualizar rutas absolutas antiguas en la copia restaurada y revisar los plugins
personalizados que las utilicen. Para la base, usar una herramienta que respete
datos serializados, primero en modo de ensayo:

```bash
wp --path=/srv/www/embrylab/public search-replace \
  /home/SOURCE_USER/embrylab_downloads /srv/www/embrylab/embrylab_downloads \
  --all-tables-with-prefix --precise --dry-run
```

Revisar el informe y el alcance antes de repetir sin `--dry-run`. No hacer
reemplazos globales con `sed` dentro de un dump SQL. Ver la
[referencia de WP-CLI](https://developer.wordpress.org/cli/commands/search-replace/).

Validar portada, login, recursos, idiomas, catálogo, carrito y checkout sin
confirmar pagos. Auditar referencias de descarga con
`scripts/audit_downloads.php`, ejecutado como el usuario del sitio. La prueba
funcional de una descarga debe verificar autorización, tamaño y SHA-256; una
URL visible no basta. Crear y retirar datos sintéticos solo en la copia privada.

## 7. Corte final y DNS

Antes del corte: respaldar, detener las escrituras del sitio origen o ponerlo
en mantenimiento, repetir el dump y la sincronización final, validar el destino
y definir qué sistema será la única fuente de nuevas escrituras.

Cambiar los registros del dominio hacia el VPS, conservar el origen para
recuperación y verificar la propagación con más de un resolutor y con los
servidores autoritativos. Una entrada en `/etc/hosts` sirve para pruebas locales;
no prueba la propagación pública y debe retirarse cuando deje de ser necesaria.

Habilitar el frontal HTTP para el desafío ACME, emitir el certificado y después
activar el frontal HTTPS. La plantilla HTTPS requiere certificados existentes.
Probar la renovación automática y su hook de recarga de Nginx.

## 8. Salida de preview y cierre

Revisar la cola de tareas importada antes de activar correo y cron. Retirar las
protecciones de preview solo cuando corresponda, activar los timers por sitio y
verificar sus resultados. Los pagos requieren una validación y autorización
específicas antes de habilitarse.

No eliminar Zomro ni cancelar su servicio como consecuencia automática del
cambio de DNS. Confirmar respaldo externo, observación del destino y tratamiento
de escrituras antes de decidir una baja administrativa.
