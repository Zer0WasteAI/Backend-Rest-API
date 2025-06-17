-- Migration 002: Add image_path column to recipes table for Firebase signed URLs
-- Other tables already have varchar(1000) for image_path

-- Add image_path column to recipes table (it doesn't exist yet)
ALTER TABLE recipes ADD COLUMN image_path VARCHAR(1000) NULL;

-- Add index on image_path for performance (first 255 chars)
CREATE INDEX idx_recipes_image_path ON recipes (image_path(255)); 