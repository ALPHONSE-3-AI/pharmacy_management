-- Refined Triggers for Stock Alerts
-- Deletes old alerts and handles uniqueness

USE pharmacy;

-- 1. Clear existing alerts to start fresh if needed (optional, but good for cleanup)
DELETE FROM stock_alert;

-- 2. Drop existing triggers to redefine them
DROP TRIGGER IF EXISTS low_stock_trigger;
DROP TRIGGER IF EXISTS low_stock_trigger_update;

-- 3. Trigger for NEW medicines
DELIMITER //
CREATE TRIGGER low_stock_trigger
AFTER INSERT ON medicine
FOR EACH ROW
BEGIN
    IF NEW.Quantity < NEW.ReorderPoint THEN
        -- Insert ONLY if no alert already exists for this medicine
        INSERT INTO stock_alert (medicine_id, message, created_at)
        SELECT NEW.MedicineID, 
               CONCAT('Stock alert: ', NEW.Name, ' is low (', NEW.Quantity, ' units remaining).'),
               NOW()
        WHERE NOT EXISTS (SELECT 1 FROM stock_alert WHERE medicine_id = NEW.MedicineID);
    END IF;
END //
DELIMITER ;

-- 4. Trigger for UPDATED medicines (Restocking or Sales)
DELIMITER //
CREATE TRIGGER low_stock_trigger_update
AFTER UPDATE ON medicine
FOR EACH ROW
BEGIN
    -- CASE A: Low Stock (below reorder point)
    IF NEW.Quantity < NEW.ReorderPoint THEN
        -- Insert ONLY if no alert already exists for this medicine
        INSERT INTO stock_alert (medicine_id, message, created_at)
        SELECT NEW.MedicineID, 
               CONCAT('Stock alert: ', NEW.Name, ' is low (', NEW.Quantity, ' units remaining).'),
               NOW()
        WHERE NOT EXISTS (SELECT 1 FROM stock_alert WHERE medicine_id = NEW.MedicineID);
        
        -- Optional: Update message if quantity changed but it's still low
        UPDATE stock_alert 
        SET message = CONCAT('Stock alert: ', NEW.Name, ' is low (', NEW.Quantity, ' units remaining).')
        WHERE medicine_id = NEW.MedicineID;
        
    -- CASE B: Restocked (at or above reorder point)
    ELSE
        -- Remove the alert because stock is now sufficient
        DELETE FROM stock_alert WHERE medicine_id = NEW.MedicineID;
    END IF;
END //
DELIMITER ;
