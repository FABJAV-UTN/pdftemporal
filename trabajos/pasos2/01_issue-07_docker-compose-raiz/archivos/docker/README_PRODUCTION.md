Despliegue en producción (flujo)
================================

1. Construir la imagen en CI/CD y etiquetarla con la versión.
2. Entregar `docker/app/docker-compose.yml` y `docker/app/.env` al cliente.
3. El cliente crea una red externa Docker (ej: `pdf_network`).
4. Levantar `docker/mongodb/docker-compose.yml` para la base de datos.
5. Levantar `docker/app/docker-compose.yml` (usa imagen ya publicada).

Para desarrollo usar `docker-compose.yml` en la raíz (`docker compose up --build`).
