import sqlite3
import pandas as pd
import glob
import os

def run_sql_analysis():
    print("Setting up SQLite database...")
    conn = sqlite3.connect(':memory:')
    
    # Load data
    consumption_df = pd.read_csv('data/energy_consumption.csv')
    household_df = pd.read_csv('data/household_info.csv')
    
    consumption_df.to_sql('energy_consumption', conn, index=False)
    household_df.to_sql('household_info', conn, index=False)
    
    # Execute SQL files
    sql_files = sorted(glob.glob('sql/*.sql'))
    
    for file in sql_files:
        print(f"\n{'='*50}\nExecuting {file}\n{'='*50}")
        with open(file, 'r') as f:
            sql_script = f.read()
            
            # Split queries by semicolon (basic splitting)
            queries = [q.strip() for q in sql_script.split(';') if q.strip()]
            
            for query in queries:
                if query.startswith('--'):
                    # Print the comment as query description
                    lines = query.split('\n')
                    desc = [line for line in lines if line.startswith('--')]
                    if desc: print(f"\n{desc[0]}")
                try:
                    df_result = pd.read_sql_query(query, conn)
                    if not df_result.empty:
                        print(df_result.head(10))
                        if len(df_result) > 10:
                            print(f"... ({len(df_result)} rows total)")
                    else:
                        print("(Empty result)")
                except Exception as e:
                    print(f"Error executing query: {e}")
                    
    conn.close()

if __name__ == "__main__":
    run_sql_analysis()
