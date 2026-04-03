from app import app, db
from sqlalchemy import text

def patch():
    with app.app_context():
        with db.engine.connect() as conn:
            queries = [
                # USERS
                "ALTER TABLE users RENAME COLUMN id TO UserID;",
                "ALTER TABLE users RENAME COLUMN username TO Username;",
                "ALTER TABLE users RENAME COLUMN password TO Password;",
                "ALTER TABLE users RENAME COLUMN role TO Role;",

                # MEDICINE
                "ALTER TABLE medicine RENAME COLUMN id TO MedicineID;",
                "ALTER TABLE medicine RENAME COLUMN name TO Name;",
                "ALTER TABLE medicine RENAME COLUMN price TO Price;",
                "ALTER TABLE medicine RENAME COLUMN quantity TO Quantity;",
                "ALTER TABLE medicine RENAME COLUMN manufacturer_id TO ManufacturerID;",
                "ALTER TABLE medicine RENAME COLUMN reorder_point TO ReorderPoint;",
                "ALTER TABLE medicine RENAME COLUMN expiry TO ExpiryDate;",

                # BATCH
                "ALTER TABLE batch RENAME COLUMN batch_no TO BatchNo;",
                "ALTER TABLE batch RENAME COLUMN medicine_id TO MedicineID;",
                "ALTER TABLE batch RENAME COLUMN expiry_date TO ExpiryDate;",

                # CUSTOMER
                "ALTER TABLE customer RENAME COLUMN customer_id TO CustomerID;",
                "ALTER TABLE customer RENAME COLUMN name TO Name;",
                "ALTER TABLE customer RENAME COLUMN phone TO Phone;",

                # SALES_TRANSACTION
                "ALTER TABLE sales_transaction RENAME COLUMN transaction_id TO TransactionID;",
                "ALTER TABLE sales_transaction RENAME COLUMN date TO Date;",
                "ALTER TABLE sales_transaction RENAME COLUMN payment_method TO PaymentMethod;",
                "ALTER TABLE sales_transaction RENAME COLUMN customer_id TO CustomerID;",

                # SALES_DETAILS
                "ALTER TABLE sales_details RENAME COLUMN sales_details_id TO SalesDetailsID;",
                "ALTER TABLE sales_details RENAME COLUMN transaction_id TO TransactionID;",
                "ALTER TABLE sales_details RENAME COLUMN medicine_id TO MedicineID;",
                "ALTER TABLE sales_details RENAME COLUMN quantity TO Quantity;",
                "ALTER TABLE sales_details RENAME COLUMN unit_price TO UnitPrice;"
            ]
            for q in queries:
                try:
                    conn.execute(text(q))
                    print('Success:', q)
                except Exception as e:
                    print('Failed:', q, '->', e)
            
            conn.commit()

if __name__ == '__main__':
    patch()
