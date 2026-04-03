from app import app, db
from sqlalchemy import text

def patch():
    with app.app_context():
        with db.engine.connect() as conn:
            queries = [
                # Manufacturer Table
                "ALTER TABLE manufacturer RENAME COLUMN id TO ManufacturerID;",
                "ALTER TABLE manufacturer RENAME COLUMN name TO CompanyName;",
                "ALTER TABLE manufacturer RENAME COLUMN contact TO LicenseNo;",
                
                # Manufacturer Contact Table
                "ALTER TABLE manufacturer_contact RENAME COLUMN contact_id TO ContactID;",
                "ALTER TABLE manufacturer_contact RENAME COLUMN phone TO Phone;",
                "ALTER TABLE manufacturer_contact RENAME COLUMN email TO Email;",
                "ALTER TABLE manufacturer_contact RENAME COLUMN manufacturer_id TO ManufacturerID;"
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
