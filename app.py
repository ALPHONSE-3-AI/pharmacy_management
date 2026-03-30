import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from models import db, User, Manufacturer, Medicine, Sales

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
        
        user = User.query.filter_by(username=username, password=password, role=role).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
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
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('signup', role=role))
            
        new_user = User(username=username, password=password, role=role)
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
    sales = Sales.query.order_by(Sales.date.desc(), Sales.id.desc()).all()
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
        expiry_str = request.form['expiry']
        manufacturer_id = request.form.get('manufacturer_id')
        
        # Validation
        if not name or not price_str or not quantity_str or not expiry_str or not manufacturer_id:
            flash('All fields are required.', 'danger')
            return redirect(url_for('add_medicine'))
            
        try:
            price = float(price_str)
            quantity = int(quantity_str)
            if price < 0 or quantity < 0:
                flash('Price and quantity cannot be negative.', 'danger')
                return redirect(url_for('add_medicine'))
            expiry = datetime.strptime(expiry_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid input formats.', 'danger')
            return redirect(url_for('add_medicine'))
        
        new_medicine = Medicine(name=name, price=price, quantity=quantity, expiry=expiry, manufacturer_id=int(manufacturer_id))
        db.session.add(new_medicine)
        db.session.commit()
        
        flash('Medicine added successfully!', 'success')
        return redirect_to_dashboard(session['role'])
        
    manufacturers = Manufacturer.query.all()
    if not manufacturers:
        seed = Manufacturer(name="Standard Pharma", contact="1800-PHARMA")
        db.session.add(seed)
        db.session.commit()
        manufacturers = [seed]
        
    return render_template('add_medicine.html', manufacturers=manufacturers)

@app.route('/update_medicine/<int:id>', methods=['GET', 'POST'])
def update_medicine(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    
    medicine = Medicine.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form['name'].strip()
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        
        if not name or price < 0 or quantity < 0:
            flash('Invalid data format. No negative numbers allowed.', 'danger')
            return redirect(url_for('update_medicine', id=id))
            
        medicine.name = name
        medicine.price = price
        medicine.quantity = quantity
        medicine.expiry = datetime.strptime(request.form['expiry'], '%Y-%m-%d').date()
        medicine.manufacturer_id = int(request.form['manufacturer_id'])
        
        db.session.commit()
        flash('Medicine updated successfully!', 'success')
        return redirect_to_dashboard(session['role'])
        
    manufacturers = Manufacturer.query.all()
    return render_template('update_medicine.html', medicine=medicine, manufacturers=manufacturers)

@app.route('/delete_medicine/<int:id>', methods=['POST'])
def delete_medicine(id):
    if not require_role(['admin', 'pharmacist']): return unauthorized()
    medicine = Medicine.query.get_or_404(id)
    
    # Optional logic: block if sales history exists
    related_sales = Sales.query.filter_by(medicine_id=medicine.id).first()
    if related_sales:
        flash('Cannot delete medicine. It has recorded sales history.', 'danger')
        return redirect_to_dashboard(session['role'])
        
    db.session.delete(medicine)
    db.session.commit()
    flash(f'{medicine.name} deleted completely.', 'warning')
    return redirect_to_dashboard(session['role'])

@app.route('/sell_medicine', methods=['GET', 'POST'])
def sell_medicine():
    if not require_role(['salesclerk']): return unauthorized()
        
    if request.method == 'POST':
        medicine_id_str = request.form.get('medicine_id')
        quantity_str = request.form.get('quantity')
        
        if not medicine_id_str or not quantity_str:
            flash('Please select a medicine and quantity.', 'danger')
            return redirect(url_for('sell_medicine'))
            
        sell_quantity = int(quantity_str)
        if sell_quantity <= 0:
            flash('Sale quantity must be greater than zero.', 'danger')
            return redirect(url_for('sell_medicine'))
            
        medicine = Medicine.query.get(int(medicine_id_str))
        if sell_quantity > medicine.quantity:
            flash(f'Insufficient stock! Only {medicine.quantity} left.', 'danger')
            return redirect(url_for('sell_medicine'))
            
        medicine.quantity -= sell_quantity
        total_amount = medicine.price * sell_quantity
        
        sale_record = Sales(
            medicine_id=medicine.id,
            quantity=sell_quantity,
            total=total_amount,
            date=datetime.now().date()
        )
        db.session.add(sale_record)
        db.session.commit()
        
        flash(f'Sale successful! Total amount: ${total_amount:.2f}', 'success')
        return redirect_to_dashboard(session['role'])
        
    medicines = Medicine.query.filter(Medicine.quantity > 0).all()
    return render_template('sell_medicine.html', medicines=medicines)

@app.route('/sales_history')
def sales_history():
    if not require_role(['admin']): return unauthorized()
        
    sales = Sales.query.order_by(Sales.date.desc(), Sales.id.desc()).all()
    return render_template('sales_history.html', sales=sales)

def unauthorized():
    flash('Unauthorized Access. Your role does not permit viewing this page.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
