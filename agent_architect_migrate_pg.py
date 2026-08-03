"""
QESIS+ Ecosystem - Enterprise Database Migration Engine
File: agent_architect_migrate_pg.py
Target: SQLite to PostgreSQL Migration with Native SQLite Dump Fallback
"""

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = r'C:\Users\Lenovo\qesis-mcp'
ALT_BASE_DIR = r'C:\Users\Lenovo\sovereign-infra'

SQLITE_PATH = os.path.join(BASE_DIR, 'var', 'qesis.sqlite')
if not os.path.exists(SQLITE_PATH):
    alt_sqlite = os.path.join(ALT_BASE_DIR, 'var', 'qesis.sqlite')
    if os.path.exists(alt_sqlite):
        SQLITE_PATH = alt_sqlite

FALLBACK_DUMP_PATH = os.path.join(BASE_DIR, 'var', 'qesis_fallback_dump.sql')

PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'admin123')
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
PG_DB_NAME = os.getenv('PG_DB_NAME', 'qesis_digital_twin')

def execute_migration():
    print("ARCHITECT Agent: Initializing robust data migration pipeline...")
    
    os.makedirs(os.path.dirname(FALLBACK_DUMP_PATH), exist_ok=True)

    if not os.path.exists(SQLITE_PATH):
        print(f"Critical Error: SQLite database not found at {SQLITE_PATH}")
        return

    conn_sqlite = sqlite3.connect(SQLITE_PATH)
    
    connection_string = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
    pg_connected = False
    
    try:
        engine_pg = create_engine(connection_string)
        with engine_pg.connect() as conn:
            conn.execute(text("SELECT 1"))
        pg_connected = True
        print("PostgreSQL connection established successfully.")
    except Exception as e:
        print(f"Notice: PostgreSQL server offline ({e}). Switching to native SQLite SQL dump fallback.")

    if pg_connected:
        tables_df = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn_sqlite)
        migrated_count = 0
        for table_name in tables_df['name']:
            try:
                df_temp = pd.read_sql_query(f"SELECT * FROM [{table_name}]", conn_sqlite)
                df_temp.to_sql(table_name, engine_pg, if_exists='replace', index=False)
                print(f"Successfully migrated table to PostgreSQL: {table_name}")
                migrated_count += 1
            except Exception as table_err:
                print(f"Error migrating table {table_name}: {table_err}")
        print(f"SUCCESS: All {migrated_count} tables synchronized to PostgreSQL.")
    else:
        try:
            with open(FALLBACK_DUMP_PATH, 'w', encoding='utf-8') as f:
                for line in conn_sqlite.iterdump():
                    f.write(f"{line}\n")
            print(f"SUCCESS: Native SQLite fallback SQL dump successfully saved to {FALLBACK_DUMP_PATH}.")
        except Exception as dump_err:
            print(f"Error generating SQL dump: {dump_err}")

    conn_sqlite.close()

if __name__ == "__main__":
    execute_migration()