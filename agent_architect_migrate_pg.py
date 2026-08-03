# Importamos bibliotecas para manipular dados e ligar às bases de dados
import pandas as pd
import sqlite3
# SQLAlchemy é a ferramenta padrão em Python para gerir ligações ao PostgreSQL
from sqlalchemy import create_engine
import os

# 1. Definimos o caminho da base de dados SQLite (a origem dos dados)
caminho_sqlite = r'C:\Users\Lenovo\sovereign-infra\var\qesis.sqlite'

# 2. CONFIGURAÇÃO POSTGRESQL (O destino dos dados)
# Substitui estes valores pelas credenciais reais do teu servidor PostgreSQL
PG_USER = 'teu_utilizador'         # Ex: 'postgres'
PG_PASSWORD = 'tua_password'       # Ex: 'admin123'
PG_HOST = 'localhost'              # Se estiver no teu PC é 'localhost'
PG_PORT = '5432'                   # A porta padrão do PostgreSQL é 5432
PG_DB_NAME = 'qesis_digital_twin'  # O nome da base de dados no PostgreSQL

def migrar_sqlite_para_postgres():
    print("ARCHITECT Agent: A iniciar migração de dados (SQLite -> PostgreSQL)...")
    
    # Verificar se o ficheiro SQLite existe
    if not os.path.exists(caminho_sqlite):
        print(f"Erro: A base de dados SQLite não foi encontrada em {caminho_sqlite}")
        return

    try:
        # 3. Ligar à base de dados SQLite (Origem)
        conn_sqlite = sqlite3.connect(caminho_sqlite)
        
        # 4. Criar a "engine" (o motor de ligação) para o PostgreSQL (Destino)
        # Esta string de ligação usa o formato padrão: postgresql://user:pass@host:port/dbname
        string_ligacao_pg = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
        engine_pg = create_engine(string_ligacao_pg)
        
        # 5. Descobrir todas as tabelas no SQLite
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tabelas_df = pd.read_sql_query(query, conn_sqlite)
        
        contador = 0
        total_tabelas = len(tabelas_df)
        
        print(f"Encontradas {total_tabelas} tabelas. A iniciar transferência...")
        
        # 6. O ciclo que copia cada tabela
        for nome_tabela in tabelas_df['name']:
            print(f"A migrar tabela: {nome_tabela}...")
            
            # Ler a tabela do SQLite para o pandas
            df_temp = pd.read_sql_query(f"SELECT * FROM {nome_tabela}", conn_sqlite)
            
            # Escrever a tabela no PostgreSQL
            # if_exists='replace' garante que se a tabela já existir, é atualizada
            df_temp.to_sql(nome_tabela, engine_pg, if_exists='replace', index=False)
            
            contador += 1
            
        print("-" * 40)
        print(f"SUCESSO! {contador} tabelas foram migradas para o PostgreSQL.")
        print("Os dados estão prontos para o Microsoft Fabric / Power BI.")
        
    except Exception as e:
        print(f"Ocorreu um erro durante a migração: {e}")
        print("Dica: Verifica se o servidor PostgreSQL está ligado e se as credenciais estão corretas.")
        
    finally:
        # Fechamos a ligação ao SQLite no final para libertar a memória
        if 'conn_sqlite' in locals():
            conn_sqlite.close()

if __name__ == "__main__":
    migrar_sqlite_para_postgres()