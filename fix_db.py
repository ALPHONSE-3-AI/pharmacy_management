from app import app, db
from sqlalchemy import text

def fix():
    with app.app_context():
        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE sales_transaction ADD COLUMN customer_id INT NULL;"))
                print("Added customer_id to sales_transaction.")
            except Exception as e:
                print("customer_id alter failed:", e)
                
            try:
                conn.execute(text("ALTER TABLE sales_transaction ADD CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customer(customer_id);"))
                print("Added foreign key constraint.")
            except Exception as e:
                print("fk alter failed:", e)
                
            try:
                conn.execute(text("ALTER TABLE medicine MODIFY COLUMN expiry DATE NULL;"))
                print("Made expiry nullable.")
            except Exception as e:
                print("expiry alter failed:", e)
            conn.commit()

if __name__ == '__main__':
    fix()
