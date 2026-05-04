#!/usr/bin/env bash


export PGPASSWORD=password

PGHOST=127.0.0.1
PGPORT=5432
PGUSER=postgres
PGDATABASE=fixity

# psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f create-postgres.sql
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f schema-drop.sql
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f schema-postgres.sql
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f schema-grants-postgres.sql
