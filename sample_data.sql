-- Sample data for KFactor WebApp
-- Insert sample cars
INSERT INTO `car`(`id`, `model`, `registration_number`, `year`, `capacity`, `fuel_type`, `is_active`, `created_at`) VALUES
(1, 'Toyota Hilux', 'ABC123GP', 2020, 1000, 'Diesel', 1, NOW()),
(2, 'Ford Ranger', 'DEF456GP', 2021, 1200, 'Diesel', 1, NOW()),
(3, 'Nissan Navara', 'GHI789GP', 2019, 1100, 'Diesel', 1, NOW()),
(4, 'Isuzu D-Max', 'JKL012GP', 2022, 1300, 'Diesel', 1, NOW()),
(5, 'Mitsubishi Triton', 'MNO345GP', 2020, 1150, 'Diesel', 0, NOW());

-- Insert sample users
INSERT INTO `user`(`id`, `username`, `password_hash`, `role`, `employee_id`, `created_at`) VALUES
(1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'super_admin', NULL, NOW()),
(2, 'john.doe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'driver', 1, NOW()),
(3, 'jane.smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'driver', 2, NOW()),
(4, 'mike.wilson', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'admin', 3, NOW()),
(5, 'sarah.jones', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2.', 'driver', 4, NOW());

-- Insert sample employees (if not already exists)
INSERT INTO `employee`(`id`, `employee_id`, `first_name`, `last_name`, `date_of_birth`, `hire_date`, `phone`, `email`, `address`, `next_of_kin_name`, `next_of_kin_phone`, `next_of_kin_relationship`, `is_active`, `created_at`) VALUES
(1, 'EMP001', 'John', 'Doe', '1990-05-15', '2020-01-15', '+27123456789', 'john.doe@kfactor.com', '123 Main St, Johannesburg', 'Jane Doe', '+27123456788', 'Spouse', 1, NOW()),
(2, 'EMP002', 'Jane', 'Smith', '1988-08-22', '2020-03-20', '+27123456790', 'jane.smith@kfactor.com', '456 Oak Ave, Cape Town', 'John Smith', '+27123456791', 'Spouse', 1, NOW()),
(3, 'EMP003', 'Mike', 'Wilson', '1985-12-10', '2019-11-10', '+27123456792', 'mike.wilson@kfactor.com', '789 Pine Rd, Durban', 'Mary Wilson', '+27123456793', 'Spouse', 1, NOW()),
(4, 'EMP004', 'Sarah', 'Jones', '1992-03-28', '2021-06-15', '+27123456794', 'sarah.jones@kfactor.com', '321 Elm St, Pretoria', 'David Jones', '+27123456795', 'Spouse', 1, NOW()),
(5, 'EMP005', 'David', 'Brown', '1987-07-14', '2021-09-01', '+27123456796', 'david.brown@kfactor.com', '654 Maple Dr, Bloemfontein', 'Lisa Brown', '+27123456797', 'Spouse', 1, NOW());

-- Insert sample car service history
INSERT INTO `car_service_history`(`id`, `car_id`, `service_date`, `service_type`, `description`, `cost`, `service_provider`, `next_service_date`, `created_at`) VALUES
(1, 1, '2024-01-15', 'Oil Change', 'Regular oil change and filter replacement', 850.00, 'Toyota Service Center', '2024-07-15', NOW()),
(2, 1, '2024-02-20', 'Brake Service', 'Brake pad replacement and brake fluid check', 1200.00, 'Toyota Service Center', '2024-08-20', NOW()),
(3, 2, '2024-01-10', 'Oil Change', 'Regular oil change and filter replacement', 900.00, 'Ford Service Center', '2024-07-10', NOW()),
(4, 3, '2024-03-05', 'Tire Replacement', 'All four tires replaced', 3200.00, 'Tire Express', '2024-09-05', NOW()),
(5, 4, '2024-02-28', 'Oil Change', 'Regular oil change and filter replacement', 950.00, 'Isuzu Service Center', '2024-08-28', NOW());

-- Note: The password hash above is for 'password123' - you should change this in production
-- To generate a new password hash, you can use Python:
-- from werkzeug.security import generate_password_hash
-- print(generate_password_hash('your_password')) 