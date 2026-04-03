# Pharmacy Management System: Technical Specifications

This document outlines the current architectural state of your Pharmacy Management System as developed through our iterative sessions.

## 1. Database Schema (Full ER Mapping)

As per our extensive refactoring, all tables and columns now strictly adhere to the ER Diagram attributes:

### `users`
- `UserID` (Int, PK, Auto_Increment)
- `Username` (Varchar 50)
- `Password` (Varchar 50)
- `Role` (admin, pharmacist, salesclerk)

### `medicine`
- `MedicineID` (Int, PK, Auto_Increment)
- `Name` (Varchar 100)
- `Price` (Float)
- `Quantity` (Int)
- `ExpiryDate` (Date)
- `ManufacturerID` (Fk, Int)
- `ReorderPoint` (Int, Default: 10)

### `batch`
- `BatchNo` (Int, PK, Auto_Increment)
- `MedicineID` (Fk, Int)
- `ExpiryDate` (Date)

### `customer`
- `CustomerID` (Int, PK, Auto_Increment)
- `Name` (Varchar 100)
- `Phone` (Varchar 15)

### `sales_transaction`
- `TransactionID` (Int, PK, Auto_Increment)
- `Date` (Date)
- `PaymentMethod` (Varchar 50)
- `CustomerID` (Fk, Int, Nullable)

### `sales_details`
- `SalesDetailsID` (Int, PK, Auto_Increment)
- `TransactionID` (Fk, Int)
- `MedicineID` (Fk, Int)
- `Quantity` (Int)
- `UnitPrice` (Float)

### `manufacturer` & `manufacturer_contact`
- `ManufacturerID` (Int, PK)
- `CompanyName` (Varchar 100)
- `LicenseNo` (Varchar 100)
- `ContactID` (Int, PK)
- `Phone` (Varchar 15)
- `Email` (Varchar 100)

## 2. Role-Based Access (Rbac)
- **Admin**: Full oversight, inventory management, sales logs (Ledger), and Manufacturer portal.
- **Pharmacist**: Inventory registry intake, price updates, and medicine catalog maintenance.
- **Sales Clerk**: Access to Point of Sale (POS), medicine lookup, and recording sales transactions.

## 3. Core Logic & Safety
- **Currency**: All financial values are expressed in Rupees (₹) across the UI and backend messages.
- **Validation**: Medicine cannot be added with an `ExpiryDate` in the past (handled by JS on frontend and Python on backend).
- **Checkout**: Sales clerking allows linking a sale via a `CustomerID` or dynamic creation of a new customer record via Name + Phone.

## 4. How to Run the System
1. Ensure the virtual environment is active: `.\venv\Scripts\activate`
2. Run the application: `python app.py`
3. Access the dashboard at: `http://127.0.0.1:5000`

---
*Created for the Pharmacy Management System project. Last updated: April 3, 2026.*
