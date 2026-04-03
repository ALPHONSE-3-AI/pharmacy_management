from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(50), unique=True, nullable=False)
    Password = db.Column(db.String(50), nullable=False)
    Role = db.Column(db.String(20), nullable=False) # admin, pharmacist, salesclerk

class Manufacturer(db.Model):
    __tablename__ = 'manufacturer'
    ManufacturerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CompanyName = db.Column(db.String(100), nullable=False)
    LicenseNo = db.Column(db.String(100), nullable=False)

class ManufacturerContact(db.Model):
    __tablename__ = 'manufacturer_contact'
    ContactID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Phone = db.Column(db.String(15), nullable=False)
    Email = db.Column(db.String(100), nullable=False)
    ManufacturerID = db.Column(db.Integer, db.ForeignKey('manufacturer.ManufacturerID'), nullable=False)
    manufacturer = db.relationship('Manufacturer', backref=db.backref('contacts', lazy=True))

class Medicine(db.Model):
    __tablename__ = 'medicine'
    MedicineID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Price = db.Column(db.Float, nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    ExpiryDate = db.Column(db.Date, nullable=True)
    ManufacturerID = db.Column(db.Integer, db.ForeignKey('manufacturer.ManufacturerID'), nullable=False)
    ReorderPoint = db.Column(db.Integer, nullable=False, default=10)
    manufacturer = db.relationship('Manufacturer', backref=db.backref('medicines', lazy=True))

class Batch(db.Model):
    __tablename__ = 'batch'
    BatchNo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    MedicineID = db.Column(db.Integer, db.ForeignKey('medicine.MedicineID'), nullable=False)
    ExpiryDate = db.Column(db.Date, nullable=False)
    medicine = db.relationship('Medicine', backref=db.backref('batches', lazy=True))

class Customer(db.Model):
    __tablename__ = 'customer'
    CustomerID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(100), nullable=False)
    Phone = db.Column(db.String(20), nullable=False)

class SalesTransaction(db.Model):
    __tablename__ = 'sales_transaction'
    TransactionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Date = db.Column(db.Date, nullable=False)
    PaymentMethod = db.Column(db.String(50), nullable=False)
    CustomerID = db.Column(db.Integer, db.ForeignKey('customer.CustomerID'), nullable=True)
    customer = db.relationship('Customer', backref=db.backref('transactions', lazy=True))

class SalesDetails(db.Model):
    __tablename__ = 'sales_details'
    SalesDetailsID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TransactionID = db.Column(db.Integer, db.ForeignKey('sales_transaction.TransactionID'), nullable=False)
    MedicineID = db.Column(db.Integer, db.ForeignKey('medicine.MedicineID'), nullable=False)
    Quantity = db.Column(db.Integer, nullable=False)
    UnitPrice = db.Column(db.Float, nullable=False)
    transaction = db.relationship('SalesTransaction', backref=db.backref('details', lazy=True))
    medicine = db.relationship('Medicine')
