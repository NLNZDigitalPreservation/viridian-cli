#!/usr/bin/env bash

# This script initializes the Oracle database by running the necessary SQL scripts.
podman exec -i oracle \
sqlplus system/Pass123Word@localhost:1521/FREEPDB1 < schema-oracle.sql