#!/bin/bash

# Script para crear la base de datos PostgreSQL y ejecutar migraciones de Django

echo "=========================================="
echo "SETUP DE BASE DE DATOS POSTGRESQL"
echo "=========================================="

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: No se encontró el archivo .env"
    exit 1
fi

# Verificar variables requeridas
if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    echo "Error: Faltan variables de entorno en .env"
    exit 1
fi

POSTGRES_HOST=${POSTGRES_HOST:-localhost}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

echo "Configuración:"
echo "  Host: $POSTGRES_HOST"
echo "  Puerto: $POSTGRES_PORT"
echo "  Base de datos: $POSTGRES_DB"
echo "  Usuario: $POSTGRES_USER"
echo ""

# Crear la base de datos si no existe
echo "Verificando/Creando base de datos..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d postgres -c "CREATE DATABASE $POSTGRES_DB"

if [ $? -eq 0 ]; then
    echo "✓ Base de datos verificada/creada"
else
    echo "✗ Error al crear la base de datos"
    exit 1
fi

# Ejecutar migraciones de Django
echo ""
echo "Creando migraciones de Django..."
python manage.py makemigrations

echo ""
echo "Aplicando migraciones..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Migraciones aplicadas exitosamente"
else
    echo "✗ Error al aplicar migraciones"
    exit 1
fi

# Mostrar tablas creadas
echo ""
echo "=========================================="
echo "TABLAS CREADAS:"
echo "=========================================="
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "\dt"

echo ""
echo "=========================================="
echo "✓ SETUP COMPLETADO"
echo "=========================================="
