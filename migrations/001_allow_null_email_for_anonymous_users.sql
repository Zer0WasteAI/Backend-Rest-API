-- Migration: 001_allow_null_email_for_anonymous_users.sql
-- Date: 2025-06-05
-- Description: Allow NULL values in email column for anonymous users
-- Author: Rafael Primo

-- Remove unique constraint temporarily
ALTER TABLE users DROP INDEX email;

-- Modify column to allow NULL
ALTER TABLE users MODIFY email VARCHAR(120) NULL;

-- Clean up any existing duplicate empty emails (convert to NULL except first one)
UPDATE users SET email = NULL 
WHERE email = '' AND uid != (
    SELECT uid FROM (
        SELECT uid FROM users WHERE email = '' LIMIT 1
    ) AS temp
);

-- Recreate unique index (MySQL allows multiple NULL values in unique indexes)
ALTER TABLE users ADD UNIQUE INDEX email (email);

-- Verification query (uncomment to test)
-- SELECT 'Migration completed successfully' as status;
-- DESCRIBE users; 