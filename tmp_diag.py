import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'pharmacy'),
        port=int(os.getenv('DB_PORT', '3306')),
        cursorclass=pymysql.cursors.DictCursor
    )

try:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            print("--- MEDICINES ---")
            cursor.execute("SELECT MedicineID, Name, Quantity, ReorderPoint FROM medicine WHERE Name LIKE '%Paracetamol%'")
            for row in cursor.fetchall():
                print(row)
                
            print("\n--- STOCK ALERTS ---")
            cursor.execute("SELECT * FROM stock_alert")
            for row in cursor.fetchall():
                print(row)
                
            print("\n--- TRIGGERS ---")
            cursor.execute("SHOW TRIGGERS")
            for row in cursor.fetchall():
                print(f"Trigger: {row['Trigger']}, Event: {row['Event']}, Table: {row['Table']}, Timing: {row['Timing']}")
                # print(f"Statement: {row['Statement']}")
                
except Exception as e:
    print(f"Error: {e}")
