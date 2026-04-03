import os

files = [
    'templates/admin_dashboard.html',
    'templates/add_medicine.html',
    'templates/clerk_dashboard.html',
    'templates/pharmacist_dashboard.html',
    'templates/sales_history.html',
    'templates/sell_medicine.html',
    'templates/update_medicine.html',
    'templates/dashboard.html',
]

for filepath in files:
    if not os.path.exists(filepath):
        print(f'SKIP: {filepath}')
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Replace every dollar sign that appears before a price with rupee symbol
    new_content = content.replace('${{', '₹{{').replace('($)', '(₹)').replace('Price ($)', 'Price (₹)').replace('(${{', '(₹{{')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    if new_content != content:
        print(f'UPDATED: {filepath}')
    else:
        print(f'NO CHANGE: {filepath}')
