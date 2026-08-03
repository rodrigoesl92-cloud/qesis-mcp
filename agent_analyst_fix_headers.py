# We import 'pandas' for data manipulation and 'sqlite3' to talk to the database
import pandas as pd
import sqlite3

# 1. The exact path to the target database
db_path = r'C:\Users\Lenovo\sovereign-infra\var\qesis.sqlite'

def fix_database_headers():
    print(f"ANALYST Agent connecting to database: {db_path}")
    
    try:
        # 2. Establish the connection
        conn = sqlite3.connect(db_path)
        
        # 3. Get all the table names
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables_df = pd.read_sql_query(query, conn)
        
        fixed_count = 0
        
        # 4. Loop through every table
        for table_name in tables_df['name']:
            
            # Read the table
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # 5. Check if it suffers from 'c1' positional drift
            if 'c1' in df.columns and len(df) > 0:
                print(f"Fixing headers for table: {table_name}...")
                
                # Grab the first row as a list
                raw_headers = df.iloc[0].tolist()
                
                # --- NEW CLEANING STEP ---
                clean_headers = []
                for index, header in enumerate(raw_headers):
                    # Convert the header to text and remove extra spaces
                    str_header = str(header).strip()
                    
                    # If the header is empty, 'None', or 'nan', give it a safe fallback name
                    if not str_header or str_header.lower() == 'nan' or str_header.lower() == 'none':
                        clean_headers.append(f"unnamed_column_{index}")
                    else:
                        clean_headers.append(str_header)
                # -------------------------
                
                # 6. Apply our clean headers to the table
                df.columns = clean_headers
                
                # 7. Drop that first row from the data (since it's now our header)
                df = df[1:].reset_index(drop=True)
                
                # 8. Save the corrected table back into the database
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                fixed_count += 1
                
        # Close the connection
        conn.close()
        
        print("-" * 40)
        print(f"Operation complete! {fixed_count} tables were successfully fixed.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    fix_database_headers()