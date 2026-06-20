# Candidatos RH

Este repositorio contiene el proyecto Candidatos RH.

## Descripción

Aplicación para gestionar candidatos y procesos de recursos humanos.

### Variables de entorno requeridas

```env
SUPABASE_URL=<su_api_key>
SUPABASE_URL=<su_api_key>
DATABASE_URL=<su_api_key>
JWT_SECRET_KEY=<su_secret>
CSRF_SECRET_KEY=<su_secret>
```

## Uso

Por defecto si no configuras las siguientes variables, se creara localmente una instancia de sqllite
son necesarias para la base de datos y el bucket (archivos, avatares), puedes clonar el repositorio y adaptarlo al bucket y db que gustes

## Despliegue con Docker Compose

1. Copie el archivo `docker-compose.yml` al entorno de ejecución.
2. Configure sus credenciales en el archivo `.env`.
3. Se contempla Caddy para el reverse proxy (se incluye ejemplo minimo de Caddyfile, ajustar al dominio), en caso de no necesitarlo omitirlo del docker-compose.yml
