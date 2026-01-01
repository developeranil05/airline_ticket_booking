@echo off
echo Resetting PostgreSQL database...

REM Connect to PostgreSQL and drop/recreate database
psql -U airline_user -h localhost -c "DROP DATABASE IF EXISTS airline_db;"
psql -U airline_user -h localhost -c "CREATE DATABASE airline_db;"

echo Database reset complete!
pause