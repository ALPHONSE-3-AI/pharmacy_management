with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

mapping = {
    'user.id': 'user.UserID',
    'user.role': 'user.Role',
    'user.username': 'user.Username',
    
    'Medicine.quantity': 'Medicine.Quantity',
    'medicine.id': 'medicine.MedicineID',
    'medicine.name': 'medicine.Name',
    'medicine.price': 'medicine.Price',
    'medicine.quantity': 'medicine.Quantity',
    'medicine.reorder_point': 'medicine.ReorderPoint',
    'medicine.manufacturer_id': 'medicine.ManufacturerID',
    
    'Batch.medicine_id': 'Batch.MedicineID',
    
    'customer.customer_id': 'customer.CustomerID',
    'Customer.phone': 'Customer.Phone',
    
    'SalesTransaction.date': 'SalesTransaction.Date',
    'SalesTransaction.transaction_id': 'SalesTransaction.TransactionID',
    'transaction.transaction_id': 'transaction.TransactionID',
    
    'SalesDetails.medicine_id': 'SalesDetails.MedicineID',
    
    'name=name': 'Name=name',
    'price=price': 'Price=price',
    'quantity=quantity': 'Quantity=quantity',
    'reorder_point=reorder_point': 'ReorderPoint=reorder_point',
    'manufacturer_id=int(manufacturer_id)': 'ManufacturerID=int(manufacturer_id)',
    
    'medicine_id=new_medicine.MedicineID': 'MedicineID=new_medicine.MedicineID',
    'medicine_id=new_medicine.id': 'MedicineID=new_medicine.MedicineID',
    'expiry_date=expiry': 'ExpiryDate=expiry',
    
    'name=customer_name': 'Name=customer_name',
    'phone=customer_phone': 'Phone=customer_phone',
    
    'date=datetime.now().date()': 'Date=datetime.now().date()',
    'payment_method=payment_method': 'PaymentMethod=payment_method',
    'customer_id=customer_id': 'CustomerID=customer_id',
    
    'transaction_id=transaction.TransactionID': 'TransactionID=transaction.TransactionID',
    'medicine_id=medicine.MedicineID': 'MedicineID=medicine.MedicineID',
    'unit_price=medicine.price': 'UnitPrice=medicine.Price',
    'unit_price=medicine.Price': 'UnitPrice=medicine.Price'
}

for k, v in mapping.items():
    text = text.replace(k, v)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
