from app import app, db
import traceback

def test_routes():
    app.config['TESTING'] = True
    client = app.test_client()
    
    with app.app_context():
        # Test admin
        with client.session_transaction() as sess: sess['user_id'] = 1; sess['role'] = 'admin'
        for r in ['/admin/dashboard', '/add_medicine', '/sales_history', '/manufacturers']:
            try:
                res = client.get(r)
                if res.status_code == 200: print(f"OK: {r}")
                else: print(f"FAIL: {r} returned {res.status_code}")
            except Exception as e: print(f"ERROR on {r}: {type(e).__name__} - {e}")
            
        # Test pharmacst
        with client.session_transaction() as sess: sess['user_id'] = 1; sess['role'] = 'pharmacist'
        for r in ['/pharmacist/dashboard']:
            try:
                res = client.get(r)
                if res.status_code == 200: print(f"OK: {r}")
                else: print(f"FAIL: {r} returned {res.status_code}")
            except Exception as e: print(f"ERROR on {r}: {type(e).__name__} - {e}")
            
        # Test clerk
        with client.session_transaction() as sess: sess['user_id'] = 1; sess['role'] = 'salesclerk'
        for r in ['/clerk/dashboard', '/sell_medicine']:
            try:
                res = client.get(r)
                if res.status_code == 200: print(f"OK: {r}")
                else: print(f"FAIL: {r} returned {res.status_code}")
            except Exception as e: print(f"ERROR on {r}: {type(e).__name__} - {e}")

if __name__ == '__main__':
    test_routes()
