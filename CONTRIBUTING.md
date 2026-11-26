# Contribuir

1. Crear una rama `codex/nombre-de-la-tarea` o una rama personal equivalente.
2. Mantener ejemplos sin datos de infraestructura reales.
3. Añadir pruebas cuando cambie un comportamiento de las herramientas.
4. Ejecutar `make check` y `make test` sin acceso a producción.
5. Revisar `git diff --cached` y publicar únicamente archivos del proyecto.

Los cambios de documentación no autorizan cambios en el VPS. Una propuesta de
cutover debe incluir respaldo, validaciones, tratamiento de escrituras y un
procedimiento de rollback. Explicar qué se probó y qué no se probó.
