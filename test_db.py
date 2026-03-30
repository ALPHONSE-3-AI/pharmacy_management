from app import app, db
from sqlalchemy import text

def test_connection():
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES;"))
                tables = [row[0] for row in result]
                print(f"Connection successful! Found tables: {tables}")
        except Exception as e:
            print(f"Connection failed: {e}")

if __name__ == '__main__':
    test_connection()
