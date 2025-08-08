#!/bin/bash
set -e

# Create the database and user if they don't exist
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create user if not exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'codeconv_user') THEN
            CREATE USER codeconv_user WITH PASSWORD 'akhil123';
        END IF;
    END
    \$\$;
    
    -- Grant all privileges
    GRANT ALL PRIVILEGES ON DATABASE codeconv TO codeconv_user;
    
    -- Make sure the user can create tables
    GRANT CREATE ON SCHEMA public TO codeconv_user;
    GRANT USAGE ON SCHEMA public TO codeconv_user;
EOSQL

echo "PostgreSQL initialization completed"
