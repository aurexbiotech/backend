-- ========================================================
-- AUREX Hospital Management System (HMS) Database Setup
-- Paste and run this script in MySQL Workbench
-- ========================================================

-- 1. Create the database schema if it doesn't already exist
CREATE DATABASE IF NOT EXISTS aurex
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2. Select the database
USE aurex;

-- 3. Create the users table
CREATE TABLE IF NOT EXISTS users (
  id VARCHAR(36) NOT NULL PRIMARY KEY,
  full_name VARCHAR(150) NOT NULL,
  email VARCHAR(191) NOT NULL UNIQUE,
  phone_number VARCHAR(30) NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'patient',
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_users_email (email),
  INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Seed all 8 HMS roles + Admin (Password for all accounts: Password123!)
-- Hash algorithm: Argon2id
INSERT INTO users (id, full_name, email, phone_number, password_hash, role, is_active)
VALUES
  (
    '10000000-0000-0000-0000-000000000001',
    'Elena Vance (Patient)',
    'patient@aurex.com',
    '555-0101',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'patient',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000002',
    'Dr. Sarah Chen (Doctor)',
    'doctor@aurex.com',
    '555-0102',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'doctor',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000003',
    'Nurse James Wilson',
    'nurse@aurex.com',
    '555-0103',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'nurse',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000004',
    'Marcus Wright (Laboratory)',
    'lab@aurex.com',
    '555-0104',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'laboratory',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000005',
    'Priya Patel (Pharmacy)',
    'pharmacy@aurex.com',
    '555-0105',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'pharmacy',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000006',
    'Alex Martinez (Front Desk)',
    'frontdesk@aurex.com',
    '555-0106',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'front_desk',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000007',
    'Karen O\'Connor (Insurance)',
    'insurance@aurex.com',
    '555-0107',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'insurance',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000008',
    'David Sterling (Department Head)',
    'department@aurex.com',
    '555-0108',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'department',
    1
  ),
  (
    '10000000-0000-0000-0000-000000000009',
    'System Administrator',
    'admin@aurex.com',
    '555-0109',
    '$argon2id$v=19$m=65536,t=3,p=4$ZsRjkIFTKGf2gOFl6M+cNA$QxfO3f4oosxQrCUIVZiss7rXZ2UScuC76cUTwk1T0IU',
    'administrator',
    1
  )
ON DUPLICATE KEY UPDATE
  full_name = VALUES(full_name),
  phone_number = VALUES(phone_number),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  is_active = 1;

-- 5. Verification Query: View all created users and their roles
SELECT id, full_name, email, role, is_active, created_at
FROM users
ORDER BY created_at ASC;
