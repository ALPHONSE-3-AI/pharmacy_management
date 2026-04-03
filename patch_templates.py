import os

mapping = {
    'item.id ': 'item.MedicineID ',
    'item.id}': 'item.MedicineID}',
    'item.id)': 'item.MedicineID)',
    'item.name': 'item.Name',
    'item.price': 'item.Price',
    'item.quantity': 'item.Quantity',
    'item.reorder_point': 'item.ReorderPoint',
    
    'medicine.id ': 'medicine.MedicineID ',
    'medicine.id}': 'medicine.MedicineID}',
    'medicine.id)': 'medicine.MedicineID)',
    'medicine.name': 'medicine.Name',
    'medicine.price': 'medicine.Price',
    'medicine.quantity': 'medicine.Quantity',
    'medicine.reorder_point': 'medicine.ReorderPoint',
    'medicine.manufacturer_id': 'medicine.ManufacturerID',
    
    'sale.transaction_id': 'sale.TransactionID',
    'sale.date': 'sale.Date',
    'sale.total': 'sale.Total',
    'sale.payment_method': 'sale.PaymentMethod',
    'sale.customer.name': 'sale.customer.Name',
    'sale.customer.phone': 'sale.customer.Phone',
    
    'detail.medicine.name': 'detail.medicine.Name',
    'detail.quantity': 'detail.Quantity',
    'detail.unit_price': 'detail.UnitPrice',
    
    # UI Header text replacements
    '>Internal ID<': '>MedicineID<',
    '>Medicine Designation<': '>Name<',
    '>Expiry Deadline<': '>ExpiryDate<',
    '>Wholesale Value<': '>Price<',
    '>Warehouse Stock<': '>Quantity<',

    '>Reference ID<': '>MedicineID<',
    '>Article nomenclature<': '>Name<',
    '>Retail Price<': '>Price<',
    '>Availability<': '>Quantity<',
    
    '>Name / Batch Ref<': '>Name / BatchNo<',
    '>Stock<': '>Quantity<',
    '>Value<': '>Price<',

    '>Recent Trax<': '>SalesTransaction<',
    '>Global Inventory<': '>Medicine<',
    
    '>Entity Ref (ID)<': '>ManufacturerID<',
    '>Company Designation<': '>CompanyName<',
    '>Supplier License #<': '>LicenseNo<',
    '>Primary Contact (Phone)<': '>Phone<',
    '>Contact Email<': '>Email<',
    
    'sale.details[0] if sale.details else none': 'sale.details[0] if sale.details else none',
    'item.batches[0].expiry_date': 'item.batches[0].ExpiryDate'
}

def patch():
    templates_dir = 'templates'
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            for k, v in mapping.items():
                content = content.replace(k, v)
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

if __name__ == '__main__':
    patch()
