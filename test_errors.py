from app import app, db
from flask import render_template
from models import Medicine, SalesTransaction

def test():
    with app.test_request_context('/admin/dashboard'):
        try:
            medicines = Medicine.query.all()
            sales = SalesTransaction.query.order_by(SalesTransaction.date.desc(), SalesTransaction.transaction_id.desc()).all()
            res = render_template('admin_dashboard.html', medicines=medicines, sales=sales)
            print("Admin Dashboard Success")
        except Exception as e:
            print("Admin Dashboard Error:", type(e).__name__, str(e))
            
    with app.test_request_context('/pharmacist/dashboard'):
        try:
            medicines = Medicine.query.all()
            res = render_template('pharmacist_dashboard.html', medicines=medicines)
            print("Pharmacist Dashboard Success")
        except Exception as e:
            print("Pharmacist Dashboard Error:", type(e).__name__, str(e))
            
    with app.test_request_context('/clerk/dashboard'):
        try:
            medicines = Medicine.query.all()
            res = render_template('clerk_dashboard.html', medicines=medicines)
            print("Clerk Dashboard Success")
        except Exception as e:
            print("Clerk Dashboard Error:", type(e).__name__, str(e))

if __name__ == '__main__':
    test()
