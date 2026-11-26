# Datos privados y operaciones

Este proyecto público no debe recibir contraseñas, claves SSH privadas, tokens,
dumps SQL, cookies, pedidos, correos personales ni archivos de clientes. Los
inventarios reales, respaldos y evidencias sin anonimizar deben quedar fuera de
Git. `.gitignore` no elimina un secreto que ya fue registrado en el historial.

Si encuentras un secreto, no lo pegues en un issue público. Avisa al responsable
por un canal privado, revoca o rota la credencial y revisa el historial antes de
publicar otra versión. Los controles incluidos detectan patrones frecuentes;
no sustituyen la revisión humana.

Las herramientas de este repositorio no necesitan credenciales de producción
en GitHub Actions. No deben ejecutarse automáticamente contra el VPS desde CI.
Ninguna prueba debe cobrar, enviar mensajes a clientes o cancelar servicios.
