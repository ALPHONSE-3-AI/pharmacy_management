import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from models import db, User, Manufacturer, ManufacturerContact, Medicine, Batch, Customer, SalesTransaction, SalesDetails

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

# Database configuration
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', '')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'pharmacy')

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- Role enforcement helpers ---
def require_role(roles):
    """Check if the user has one of the required roles"""
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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(Username=username, Password=password, Role=role).first()
        if user:
            session['user_id'] = user.UserID
            session['role'] = user.Role
            session['username'] = user.Username
            flash(f'Logged in successfully as {role.capitalize()}!', 'success')
            return redirect_to_dashboard(role)
        else:
            flash('Invalid credentials or you selected the incorrect role portal.', 'danger')
            
    return render_template('login.html', role=role)

@app.route('/signup/<role>', methods=['GET', 'POST'])
def signup(role):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Fields cannot be empty!', 'danger')
            return redirect(url_for('signup', role=role))
            
        if User.query.filter_by(Username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('signup', role=role))
            
        new_user = User(Username=username, Password=password, Role=role)
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'Account created successfully! You can now log in as {role.capitalize()}.', 'success')
        return redirect(url_for('login', role=role))
        
    return render_template('signup.html', role=role)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# --- Dashboards ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not require_role(['admin']): return unauthorized()
    medicines = Medicine.query.all()
    sales = SalesTransaction.query.order_by(SalesTransaction.Date.desc(), SalesTransaction.TransactionID.desc()).all()
    return render_template('admin_dashboard.html', medicines=medicines, sales=sales)

@app.route('/pharmacist/dashboard')
def pharmacist_dashboard():
    if not require_role(['pharmacist']): return unauthorized()
    medicines = Medicine.query.all()
    return render_template('pharmacist_dashboard.html', medicines=medicines)

@app.route('/clerk/dashboard')
def clerk_dashboard():
    if not require_role(['salesclerk']): return unauthorized()
    medicines = Medicine.query.all()
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
        
        new_medicine = Medicine(Name=name, Price=price, Quantity=quantity, ReorderPoint=reorder_point, ManufacturerID=int(manufacturer_id))
        db.session.add(new_medicine)
        db.session.flush()
        
        new_batch = Batch(MedicineID=new_medicine.MedicineID, ExpiryDate=expiry)
        db.session.add(new_batch)
        db.session.commit()
        
        flash('Medicine added successfully!', 'success')
        return redirect_to_dashboard(session['role'])
        
    manufacturers = Manufacturer.query.all()
    if not manufacturers:
        seed = Manufacturer(CompanyName="Standard Pharma", LicenseNo="1800-PHARMA")
        db.session.add(seed)
        db.session.commit()
        manufacturers = [seed]
        
    return render_template('add_medicine.html', manufacturers=manufacturers)

@app.route('/update_medicine/<int:id>', methods=['GET', 'POST'])
def update_medicine(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    
    medicine = Medicine.query.filter_by(MedicineID=id).first_or_404()
    if request.method == 'POST':
        name = request.form['name'].strip()
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        reorder_point = int(request.form.get('reorder_point', 10))
        
        if not name or price < 0 or quantity < 0 or reorder_point < 0:
            flash('Invalid data format. No negative numbers allowed.', 'danger')
            return redirect(url_for('update_medicine', id=id))
            
        medicine.Name = name
        medicine.Price = price
        medicine.Quantity = quantity
        medicine.ReorderPoint = reorder_point
        medicine.ManufacturerID = int(request.form['manufacturer_id'])
        
        db.session.commit()
        flash('Medicine updated successfully!', 'success')
        return redirect_to_dashboard(session['role'])
        
    manufacturers = Manufacturer.query.all()
    return render_template('update_medicine.html', medicine=medicine, manufacturers=manufacturers)

@app.route('/delete_medicine/<int:id>', methods=['POST'])
def delete_medicine(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    medicine = Medicine.query.filter_by(MedicineID=id).first_or_404()
    
    # Optional logic: block if sales history exists
    related_sales = SalesDetails.query.filter_by(MedicineID=medicine.MedicineID).first()
    if related_sales:
        flash('Cannot delete medicine. It has recorded sales history.', 'danger')
        return redirect_to_dashboard(session['role'])
        
    Batch.query.filter_by(MedicineID=medicine.MedicineID).delete()
    db.session.delete(medicine)
    db.session.commit()
    flash(f'{medicine.Name} deleted completely.', 'warning')
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
            
        medicine = Medicine.query.get(int(medicine_id_str))
        if sell_quantity > medicine.Quantity:
            flash(f'Insufficient stock! Only {medicine.Quantity} left.', 'danger')
            return redirect(url_for('sell_medicine'))
            
        medicine.Quantity -= sell_quantity
        
        customer_id = None
        if customer_id_str:
            customer = Customer.query.get(int(customer_id_str))
            if customer:
                customer_id = customer.CustomerID
                
        if not customer_id and customer_name and customer_phone:
            customer = Customer.query.filter_by(Phone=customer_phone).first()
            if not customer:
                customer = Customer(Name=customer_name, Phone=customer_phone)
                db.session.add(customer)
                db.session.flush()
            customer_id = customer.CustomerID
            
        transaction = SalesTransaction(
            Date=datetime.now().date(),
            PaymentMethod=payment_method,
            CustomerID=customer_id
        )
        db.session.add(transaction)
        db.session.flush()
        
        details = SalesDetails(
            TransactionID=transaction.TransactionID,
            MedicineID=medicine.MedicineID,
            Quantity=sell_quantity,
            UnitPrice=medicine.Price
        )
        db.session.add(details)
        db.session.commit()
        total_amount = medicine.Price * sell_quantity
        
        flash(f'Sale successful! Total amount: ₹{total_amount:.2f}', 'success')
        return redirect_to_dashboard(session['role'])
        
    medicines = Medicine.query.filter(Medicine.Quantity > 0).all()
    return render_template('sell_medicine.html', medicines=medicines)

@app.route('/sales_history')
def sales_history():
    if not require_role(['admin']): return unauthorized()
        
    sales = SalesTransaction.query.order_by(SalesTransaction.Date.desc(), SalesTransaction.TransactionID.desc()).all()
    return render_template('sales_history.html', sales=sales)

@app.route('/manufacturers')
def track_manufacturers():
    if not require_role(['admin']): return unauthorized()
    manufacturers = Manufacturer.query.all()
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
            
        mfg = Manufacturer(CompanyName=company_name, LicenseNo=license_no)
        db.session.add(mfg)
        db.session.flush()
        
        contact = ManufacturerContact(Phone=phone, Email=email, ManufacturerID=mfg.ManufacturerID)
        db.session.add(contact)
        db.session.commit()
        
        flash('Manufacturer successfully added!', 'success')
        return redirect(url_for('track_manufacturers'))
        
    return render_template('add_manufacturer.html')

def unauthorized():
    flash('Unauthorized Access. Your role does not permit viewing this page.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
