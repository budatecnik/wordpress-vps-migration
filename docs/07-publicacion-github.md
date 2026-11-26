# Publicación en GitHub

- **Cuenta:** [budatecnik](https://github.com/budatecnik)
- **Nombre propuesto y aceptado:** `wordpress-vps-migration`
- **Visibilidad elegida:** pública.

La preparación local no crea por sí sola un repositorio remoto. Antes de
publicar, autenticar la cuenta correcta y revisar los archivos que se enviarán.
El código del editor de bordados pertenece a un repositorio independiente y no
se incorpora aquí.

## Comprobación previa

```bash
make check
make test
git status --short
git diff --cached --stat
git diff --cached
```

La carpeta `ops/`, `config/config.local.json`, respaldos y evidencias privadas
deben quedar fuera del índice. Comprobarlo también con `git ls-files`. No usar
`git add .` para incorporar material de este directorio de trabajo.

El historial preparado contiene solo archivos de este proyecto. No reutilizar
historiales de otros repositorios ni subir un dump para «guardar el backup».

## Opción A: publicar mediante la conexión de GitHub

Conectar GitHub con la cuenta `budatecnik` y crear un repositorio público vacío
con el nombre acordado. Verificar que la integración permita crear repositorios
y publicar código; una conexión de solo lectura no alcanza para hacerlo.

## Opción B: GitHub CLI

Con `gh` instalado y autenticado como `budatecnik`, desde esta carpeta:

```bash
gh auth status
gh repo create budatecnik/wordpress-vps-migration --public --source=. --remote=origin
git push -u origin HEAD:main
```

Estos comandos son un paso manual de publicación. Ejecutarlos solo tras revisar
la cuenta, el índice y que `origin` no apunte a otro proyecto. Si el repositorio
ya existe, no sobrescribirlo: revisar primero su contenido e historial.

Si se utiliza un token, conservarlo en el gestor de credenciales o la integración,
nunca en la URL del remoto, en un archivo del repositorio o en una conversación.

## Opción C: paquete limpio

```bash
make package
```

Genera `dist/wordpress-vps-migration.zip` con una lista explícita de archivos,
sin `ops/`, `.git` ni datos privados. Extraer el ZIP en una carpeta nueva antes
de iniciar otro repositorio o usar la carga de archivos de GitHub. La interfaz
web puede tratar carpetas ocultas de forma distinta; comprobar que se haya
incluido `.github/workflows/validate.yml` para que exista la validación de CI.

## Después de publicar

- Revisar README, enlaces, diagrama y visibilidad desde GitHub.
- Comprobar que no haya datos privados en el árbol ni en el primer commit.
- Abrir Actions y esperar el resultado de `Validate portfolio repository`.
- No añadir una insignia que indique éxito antes de esa ejecución.
- Revisar el apartado de estado cuando se verifique el desbloqueo SMTP.

La publicación de este repositorio no debe activar despliegues sobre el VPS.
Su workflow solo revisa archivos y ejecuta pruebas offline.
