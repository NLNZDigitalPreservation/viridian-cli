#!/usr/bin/env bash

export PGPASSWORD=password

cat create-postgres.sql | psql -U postgres
cat schema-drop.sql | psql -U postgres --dbname=fixity
cat schema-postgres.sql | psql -U postgres --dbname=fixity
cat schema-grants-postgres.sql | psql -U postgres --dbname=fixity


