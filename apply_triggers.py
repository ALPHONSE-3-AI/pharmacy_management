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
    with open('d:/Pharmacy/viva_triggers.sql', 'r') as f:
        # Split by DELIMITER // manually since pymysql doesn't support the DELIMITER keyword
        sql_script = f.read()
    
    # Simple parsing to execute segments separately (ignoring DELIMITER statements)
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # First, handle the non-delimiter parts
            cursor.execute("USE pharmacy;")
            cursor.execute("DELETE FROM stock_alert;")
            cursor.execute("DROP TRIGGER IF EXISTS low_stock_trigger;")
            cursor.execute("DROP TRIGGER IF EXISTS low_stock_trigger_update;")
            
            # Now the CREATE TRIGGER statements (manually extracted)
            # Trigger 1
            trigger1 = """
            CREATE TRIGGER low_stock_trigger
            AFTER INSERT ON medicine
            FOR EACH ROW
            BEGIN
                IF NEW.Quantity < NEW.ReorderPoint THEN
                    INSERT INTO stock_alert (medicine_id, message, created_at)
                    SELECT NEW.MedicineID, 
                           CONCAT('Stock alert: ', NEW.Name, ' is low (', NEW.Quantity, ' units remaining).'),
                           NOW()
                    WHERE NOT EXISTS (SELECT 1 FROM stock_alert WHERE medicine_id = NEW.MedicineID);
                END IF;
            END
            """
            cursor.execute(trigger1)
            
            # Trigger 2
            trigger2 = """
            CREATE TRIGGER low_stock_trigger_update
            AFTER UPDATE ON medicine
            FOR EACH ROW
            BEGIN
                IF NEW.Quantity < NEW.ReorderPoint THEN
                    IF NOT EXISTS (SELECT 1 FROM stock_alert WHERE medicine_id = NEW.MedicineID) THEN
                        INSERT INTO stock_alert (medicine_id, message, created_at)
                        VALUES (NEW.MedicineID, 
                                CONCAT('Stock alert: ', NEW.Name, ' is low (', NEW.Quantity, ' units remaining).'),
                                NOW());
                    ELSE
                        UPDATE stock_alert 
                        SET message = CONCAT('Stock alert: ', NEW.Name, ' is low (', NEW.Quantity, ' units remaining).')
                        WHERE medicine_id = NEW.MedicineID;
                    END IF;
                ELSE
                    DELETE FROM stock_alert WHERE medicine_id = NEW.MedicineID;
                END IF;
            END
            """
            cursor.execute(trigger2)
            
        conn.commit()
    print("Triggers updated and stock alerts cleaned successfully.")
    
except Exception as e:
    print(f"Error: {e}")
