from app import app, db
from models import User

with app.app_context():
    # Make sure we have a test clerk
    clerk = User.query.filter_by(username='test_clerk').first()
    if not clerk:
        clerk = User(username='test_clerk', password='123', role='salesclerk')
        db.session.add(clerk)
        db.session.commit()

with app.test_client() as client:
    print("Testing /login/salesclerk Valid POST...")
    response = client.post('/login/salesclerk', data={
        'username': 'test_clerk',
        'password': '123'
    }, follow_redirects=True)
    
    print("Status:", response.status_code)
    if response.status_code == 500:
        print(response.get_data(as_text=True))
    elif 'Current Stock Reference' in response.get_data(as_text=True):
        print("Clerk dashboard loaded successfully!")
    else:
        print("Unexpected response:")
        print(response.get_data(as_text=True)[:500])
