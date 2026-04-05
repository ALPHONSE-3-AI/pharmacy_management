import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import pymysql
import pymysql.cursors
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

# Database configuration
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'pharmacy')

def get_db_connection():
    return pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=int(db_port),
        cursorclass=pymysql.cursors.DictCursor
    )

# MongoDB configuration
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client['pharmacy']
medicine_details_collection = mongo_db['medicine_details']

# --- Role enforcement helpers ---
def require_role(roles):
    if 'user_id' not in session:
        return False
    return session.get('role') in roles

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect_to_dashboard(session['role'])
    return render_template('role_selection.html')

def redirect_to_dashboard(role):
    if role == 'admin': return redirect(url_for('admin_dashboard'))
    elif role == 'pharmacist': return redirect(url_for('pharmacist_dashboard'))
    elif role == 'salesclerk': return redirect(url_for('clerk_dashboard'))
    return redirect(url_for('index'))

@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    role = role.lower()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE Username=%s AND Password=%s AND Role=%s",
                    (username, password, role)
                )
                user = cursor.fetchone()
                
        if user:
            session['user_id'] = user['UserID']
            session['role'] = user['Role']
            session['username'] = user['Username']
            flash(f'Logged in successfully as {role.capitalize()}!', 'success')
            return redirect_to_dashboard(role)
        else:
            flash('Invalid credentials or you selected the incorrect role portal.', 'danger')
            
    return render_template('login.html', role=role)

@app.route('/signup/<role>', methods=['GET', 'POST'])
def signup(role):
    role = role.lower()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Fields cannot be empty!', 'danger')
            return redirect(url_for('signup', role=role))
            
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE Username=%s", (username,))
                if cursor.fetchone():
                    flash('Username already exists!', 'danger')
                    return redirect(url_for('signup', role=role))
                
                cursor.execute(
                    "INSERT INTO users (Username, Password, Role) VALUES (%s, %s, %s)",
                    (username, password, role)
                )
            conn.commit()
        
        flash(f'Account created successfully! You can now log in as {role.capitalize()}.', 'success')
        return redirect(url_for('login', role=role))
        
    return render_template('signup.html', role=role)
    
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# --- Helper for CSV parsing ---
def parse_csv_to_list(val):
    if not val:
        return []
    return [x.strip() for x in val.split(',') if x.strip()]

# --- Helper to fetch medicines nested ---
def fetch_nested_medicines(medicine_id=None, only_in_stock=False):
    query = """
        SELECT m.*, mf.CompanyName, mf.LicenseNo, b.BatchNo, b.ExpiryDate as BatchExpiry
        FROM medicine m
        LEFT JOIN manufacturer mf ON m.ManufacturerID = mf.ManufacturerID
        LEFT JOIN batch b ON m.MedicineID = b.MedicineID
    """
    params = []
    conditions = []
    
    if medicine_id is not None:
        conditions.append("m.MedicineID = %s")
        params.append(medicine_id)
        
    if only_in_stock:
        conditions.append("m.Quantity > 0")
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

    medicines_dict = {}
    for row in rows:
        med_id = row['MedicineID']
        if med_id not in medicines_dict:
            medicines_dict[med_id] = {
                'MedicineID': med_id,
                'Name': row['Name'],
                'Price': row['Price'],
                'Quantity': row['Quantity'],
                'ReorderPoint': row['ReorderPoint'],
                'ManufacturerID': row['ManufacturerID'],
                'manufacturer': {
                    'CompanyName': row['CompanyName'],
                    'LicenseNo': row['LicenseNo']
                } if row['CompanyName'] else None,
                'batches': []
            }
        
        if row['BatchNo']:
            # Avoid duplicate batches if somehow joined multiple times
            batch_exists = any(b['BatchNo'] == row['BatchNo'] for b in medicines_dict[med_id]['batches'])
            if not batch_exists:
                medicines_dict[med_id]['batches'].append({
                    'BatchNo': row['BatchNo'],
                    'ExpiryDate': row['BatchExpiry']
                })
                
    result = list(medicines_dict.values())
    # Always return a list to maintain compatibility with dashboard and detail routes
    return result

def fetch_nested_sales():
    query = "SELECT * FROM view_sales_summary ORDER BY Date DESC, TransactionID DESC"
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
    sales_dict = {}
    for row in rows:
        tid = row['TransactionID']
        if tid not in sales_dict:
            sales_dict[tid] = {
                'TransactionID': tid,
                'Date': row['Date'],
                'PaymentMethod': row['PaymentMethod'],
                'customer': {'CustomerID': row['CustomerID'], 'Name': row['CustomerName'], 'Phone': row['CustomerPhone']} if row['CustomerID'] else None,
                'details': []
            }
        
        if row['MedicineName']:
            sales_dict[tid]['details'].append({
                'Quantity': row['Quantity'],
                'UnitPrice': row['UnitPrice'],
                'medicine': {'Name': row['MedicineName']}
            })
            
    return list(sales_dict.values())


# --- Dashboards ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not require_role(['admin']): return unauthorized()
    medicines = fetch_nested_medicines()
    sales = fetch_nested_sales()
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT SUM(Quantity * UnitPrice) AS total_sales FROM sales_details")
            result = cursor.fetchone()
            total_sales = result['total_sales'] if result and result['total_sales'] else 0
            
            # Fetch alerts for Admin too
            try:
                cursor.execute("SELECT sa.*, m.Name as MedicineName FROM stock_alert sa JOIN medicine m ON sa.medicine_id = m.MedicineID")
                alerts = cursor.fetchall()
            except:
                alerts = []
            
    return render_template('admin_dashboard.html', medicines=medicines, sales=sales, total_sales=total_sales, alerts=alerts)

@app.route('/pharmacist/dashboard')
def pharmacist_dashboard():
    if not require_role(['pharmacist']): return unauthorized()
    medicines = fetch_nested_medicines()
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT sa.*, m.Name as MedicineName FROM stock_alert sa JOIN medicine m ON sa.medicine_id = m.MedicineID")
                alerts = cursor.fetchall()
            except:
                alerts = []
                
    return render_template('pharmacist_dashboard.html', medicines=medicines, alerts=alerts)

@app.route('/clerk/dashboard')
def clerk_dashboard():
    if not require_role(['salesclerk']): return unauthorized()
    medicines = fetch_nested_medicines()
    return render_template('clerk_dashboard.html', medicines=medicines)

# --- Actions ---
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if not require_role(['admin', 'pharmacist']): return unauthorized()
        
    if request.method == 'POST':
        name = request.form['name'].strip()
        price_str = request.form['price']
        quantity_str = request.form['quantity']
        expiry_str = request.form['expiry_date']
        reorder_point_str = request.form.get('reorder_point', '10')
        manufacturer_id = request.form.get('manufacturer_id')
        
        # Validation
        if not name or not price_str or not quantity_str or not expiry_str or not manufacturer_id:
            flash('All fields are required.', 'danger')
            return redirect(url_for('add_medicine'))
            
        try:
            price = float(price_str)
            quantity = int(quantity_str)
            reorder_point = int(reorder_point_str)
            if price < 0 or quantity < 0 or reorder_point < 0:
                flash('Price, quantity, and reorder point cannot be negative.', 'danger')
                return redirect(url_for('add_medicine'))
            expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid input formats.', 'danger')
            return redirect(url_for('add_medicine'))
        
        # Expiry date must be strictly in the future
        if expiry <= datetime.now().date():
            flash('Invalid ExpiryDate: The expiry date must be a future date. Medicine was not added.', 'danger')
            return redirect(url_for('add_medicine'))
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO medicine (Name, Price, Quantity, ReorderPoint, ManufacturerID) VALUES (%s, %s, %s, %s, %s)",
                    (name, price, quantity, reorder_point, int(manufacturer_id))
                )
                new_medicine_id = cursor.lastrowid
                
                cursor.execute(
                    "INSERT INTO batch (MedicineID, ExpiryDate) VALUES (%s, %s)",
                    (new_medicine_id, expiry)
                )
            conn.commit()
        
        # If user is pharmacist, save advanced details to MongoDB
        if session.get('role') == 'pharmacist':
            description = request.form.get('description', '').strip()
            composition = request.form.get('composition', '').strip()
            dosage = request.form.get('dosage', '').strip()
            storage_instructions = request.form.get('storage_instructions', '').strip()
            doctor_consultation_required = request.form.get('doctor_consultation_required') == 'on'
            
            # Simple textareas with CSV separation (Restored Interface)
            common_uses = parse_csv_to_list(request.form.get('common_uses', ''))
            side_effects = parse_csv_to_list(request.form.get('side_effects', ''))
            precautions = parse_csv_to_list(request.form.get('precautions', ''))
            warnings = parse_csv_to_list(request.form.get('warnings', ''))
            
            medicine_doc = {
                'medicine_id': new_medicine_id,
                'description': description,
                'composition': composition,
                'dosage': dosage,
                'storage_instructions': storage_instructions,
                'common_uses': common_uses,
                'side_effects': side_effects,
                'precautions': precautions,
                'warnings': warnings,
                'doctor_consultation_required': doctor_consultation_required,
                'created_at': datetime.now()
            }
            medicine_details_collection.insert_one(medicine_doc)
        
        flash('Medicine added successfully!', 'success')
        return redirect_to_dashboard(session['role'])
        
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM manufacturer")
            manufacturers = cursor.fetchall()
            if not manufacturers:
                cursor.execute(
                    "INSERT INTO manufacturer (CompanyName, LicenseNo) VALUES (%s, %s)",
                    ("Standard Pharma", "1800-PHARMA")
                )
                conn.commit()
                cursor.execute("SELECT * FROM manufacturer")
                manufacturers = cursor.fetchall()
        
    return render_template('add_medicine.html', manufacturers=manufacturers)

@app.route('/medicine_details/<int:id>')
def medicine_details(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    
    medicines = fetch_nested_medicines(id)
    if not medicines:
        flash('Medicine not found in inventory.', 'warning')
        return redirect_to_dashboard(session['role'])
    
    medicine = medicines[0]
    details = medicine_details_collection.find_one({'medicine_id': id})
    
    return render_template('medicine_details.html', medicine=medicine, details=details)

@app.route('/update_medicine/<int:id>', methods=['GET', 'POST'])
def update_medicine(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    
    medicines = fetch_nested_medicines(id)
    if not medicines:
        flash('Medicine not found in inventory.', 'warning')
        return redirect_to_dashboard(session['role'])
    
    medicine = medicines[0]
        
    if request.method == 'POST':
        name = request.form['name'].strip()
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        reorder_point = int(request.form.get('reorder_point', 10))
        manufacturer_id = int(request.form['manufacturer_id'])
        
        if not name or price < 0 or quantity < 0 or reorder_point < 0:
            flash('Invalid data format. No negative numbers allowed.', 'danger')
            return redirect(url_for('update_medicine', id=id))
            
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE medicine SET Name=%s, Price=%s, Quantity=%s, ReorderPoint=%s, ManufacturerID=%s WHERE MedicineID=%s",
                    (name, price, quantity, reorder_point, manufacturer_id, id)
                )
            conn.commit()

        # Update MongoDB Clinic Specs (Restored Simple UI)
        if session.get('role') == 'pharmacist':
            description = request.form.get('description', '').strip()
            composition = request.form.get('composition', '').strip()
            dosage = request.form.get('dosage', '').strip()
            storage_instructions = request.form.get('storage_instructions', '').strip()
            doctor_consultation_required = request.form.get('doctor_consultation_required') == 'on'
            
            common_uses = parse_csv_to_list(request.form.get('common_uses', ''))
            side_effects = parse_csv_to_list(request.form.get('side_effects', ''))
            precautions = parse_csv_to_list(request.form.get('precautions', ''))
            warnings = parse_csv_to_list(request.form.get('warnings', ''))
            
            # Use upsert=True to create if it doesn't exist for legacy meds
            medicine_details_collection.update_one(
                {'medicine_id': id},
                {'$set': {
                    'description': description,
                    'composition': composition,
                    'dosage': dosage,
                    'storage_instructions': storage_instructions,
                    'common_uses': common_uses,
                    'side_effects': side_effects,
                    'precautions': precautions,
                    'warnings': warnings,
                    'doctor_consultation_required': doctor_consultation_required,
                    'updated_at': datetime.now()
                }},
                upsert=True
            )
            
        flash('Medicine updated successfully!', 'success')
        return redirect_to_dashboard(session['role'])
        
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM manufacturer")
            manufacturers = cursor.fetchall()
            
    # Fetch MongoDB details for the template
    details = medicine_details_collection.find_one({'medicine_id': id})
            
    return render_template('update_medicine.html', medicine=medicine, manufacturers=manufacturers, details=details)

@app.route('/delete_medicine/<int:id>', methods=['POST'])
def delete_medicine(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    
    medicines = fetch_nested_medicines(id)
    if not medicines:
        return redirect_to_dashboard(session['role'])
    
    medicine = medicines[0]
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Check sales history
            cursor.execute("SELECT * FROM sales_details WHERE MedicineID=%s", (id,))
            related_sales = cursor.fetchone()
            
            if related_sales:
                flash('Cannot delete medicine. It has recorded sales history.', 'danger')
                return redirect_to_dashboard(session['role'])
                
            cursor.execute("DELETE FROM batch WHERE MedicineID=%s", (id,))
            cursor.execute("DELETE FROM medicine WHERE MedicineID=%s", (id,))
        conn.commit()
        
    flash(f"{medicine['Name']} deleted completely.", 'warning')
    return redirect_to_dashboard(session['role'])

@app.route('/sell_medicine', methods=['GET', 'POST'])
def sell_medicine():
    if not require_role(['salesclerk']): return unauthorized()
        
    if request.method == 'POST':
        medicine_id_str = request.form.get('medicine_id')
        quantity_str = request.form.get('quantity')
        customer_id_str = request.form.get('customer_id', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        payment_method = request.form.get('payment_method', '').strip()
        
        if not medicine_id_str or not quantity_str or not payment_method:
            flash('Please select a medicine, quantity, and payment method.', 'danger')
            return redirect(url_for('sell_medicine'))
            
        sell_quantity = int(quantity_str)
        if sell_quantity <= 0:
            flash('Sale quantity must be greater than zero.', 'danger')
            return redirect(url_for('sell_medicine'))
            
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM medicine WHERE MedicineID=%s", (int(medicine_id_str),))
                medicine = cursor.fetchone()
                
                if not medicine:
                    flash('Medicine not found', 'danger')
                    return redirect(url_for('sell_medicine'))
                    
                if sell_quantity > medicine['Quantity']:
                    flash(f"Insufficient stock! Only {medicine['Quantity']} left.", 'danger')
                    return redirect(url_for('sell_medicine'))
                    
                # Setup Customer
                customer_id = None
                if customer_id_str:
                    requested_id = int(customer_id_str)
                    cursor.execute("SELECT * FROM customer WHERE CustomerID=%s", (requested_id,))
                    if cursor.fetchone():
                        customer_id = requested_id
                    elif customer_name and customer_phone:
                        # User typed an ID that doesn't exist, but gave a name/phone: forcefully create that ID
                        cursor.execute("INSERT INTO customer (CustomerID, Name, Phone) VALUES (%s, %s, %s)", (requested_id, customer_name, customer_phone))
                        customer_id = requested_id

                if not customer_id and customer_name and customer_phone:
                    cursor.execute("SELECT * FROM customer WHERE Phone=%s", (customer_phone,))
                    cust = cursor.fetchone()
                    if not cust:
                        cursor.execute("INSERT INTO customer (Name, Phone) VALUES (%s, %s)", (customer_name, customer_phone))
                        customer_id = cursor.lastrowid
                    else:
                        customer_id = cust['CustomerID']
                        
                # Transaction
                cursor.execute(
                    "UPDATE medicine SET Quantity = Quantity - %s WHERE MedicineID=%s",
                    (sell_quantity, medicine['MedicineID'])
                )
                
                cursor.execute(
                    "INSERT INTO sales_transaction (Date, PaymentMethod, CustomerID) VALUES (%s, %s, %s)",
                    (datetime.now().date(), payment_method, customer_id)
                )
                transaction_id = cursor.lastrowid
                
                cursor.execute(
                    "INSERT INTO sales_details (TransactionID, MedicineID, Quantity, UnitPrice) VALUES (%s, %s, %s, %s)",
                    (transaction_id, medicine['MedicineID'], sell_quantity, medicine['Price'])
                )
            conn.commit()
            
        total_amount = medicine['Price'] * sell_quantity
        flash(f'Sale successful! Total amount: ₹{total_amount:.2f}', 'success')
        return redirect_to_dashboard(session['role'])
        
    medicines = fetch_nested_medicines(only_in_stock=True)
    return render_template('sell_medicine.html', medicines=medicines)

@app.route('/sales_history')
def sales_history():
    if not require_role(['admin']): return unauthorized()
    sales = fetch_nested_sales()
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT SUM(Quantity * UnitPrice) AS total_sales FROM sales_details")
            result = cursor.fetchone()
            total_sales = result['total_sales'] if result and result['total_sales'] else 0
            
    return render_template('sales_history.html', sales=sales, total_sales=total_sales)

@app.route('/manufacturers')
def track_manufacturers():
    if not require_role(['admin']): return unauthorized()
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Need to nest contacts if used in HTML
            cursor.execute("""
                SELECT m.ManufacturerID, m.CompanyName, m.LicenseNo, 
                       c.ContactID, c.Phone, c.Email
                FROM manufacturer m
                LEFT JOIN manufacturer_contact c ON m.ManufacturerID = c.ManufacturerID
            """)
            rows = cursor.fetchall()
            
    mfgs_dict = {}
    for row in rows:
        mid = row['ManufacturerID']
        if mid not in mfgs_dict:
            mfgs_dict[mid] = {
                'ManufacturerID': mid,
                'CompanyName': row['CompanyName'],
                'LicenseNo': row['LicenseNo'],
                'contacts': []
            }
        if row['ContactID']:
            mfgs_dict[mid]['contacts'].append({
                'Phone': row['Phone'],
                'Email': row['Email']
            })
            
    manufacturers = list(mfgs_dict.values())
    return render_template('manufacturers.html', manufacturers=manufacturers)

@app.route('/add_manufacturer', methods=['GET', 'POST'])
def add_manufacturer():
    if not require_role(['admin']): return unauthorized()
    
    if request.method == 'POST':
        company_name = request.form['company_name'].strip()
        license_no = request.form['license_no'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()
        
        if not company_name or not license_no or not phone or not email:
            flash('All fields are required.', 'danger')
            return redirect(url_for('add_manufacturer'))
            
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO manufacturer (CompanyName, LicenseNo) VALUES (%s, %s)",
                    (company_name, license_no)
                )
                mfg_id = cursor.lastrowid
                
                cursor.execute(
                    "INSERT INTO manufacturer_contact (Phone, Email, ManufacturerID) VALUES (%s, %s, %s)",
                    (phone, email, mfg_id)
                )
            conn.commit()
        
        flash('Manufacturer successfully added!', 'success')
        return redirect(url_for('track_manufacturers'))
        
    return render_template('add_manufacturer.html')

def unauthorized():
    flash('Unauthorized Access. Your role does not permit viewing this page.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
