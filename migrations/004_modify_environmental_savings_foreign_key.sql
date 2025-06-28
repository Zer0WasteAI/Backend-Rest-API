-- Migration: Modify environmental_savings foreign key constraint
-- Purpose: Allow environmental_savings to reference both recipes and recipes_generated
-- Date: 2025-06-24

-- Drop the existing foreign key constraint
ALTER TABLE environmental_savings 
DROP FOREIGN KEY environmental_savings_ibfk_2;

-- Add new fields to track source type
ALTER TABLE environmental_savings 
ADD COLUMN recipe_source_type VARCHAR(20) DEFAULT 'manual' AFTER recipe_uid;

-- Update existing records to mark them as 'manual' (saved recipes)
UPDATE environmental_savings 
SET recipe_source_type = 'manual' 
WHERE recipe_source_type IS NULL;

-- Make the new field NOT NULL
ALTER TABLE environmental_savings 
MODIFY COLUMN recipe_source_type VARCHAR(20) NOT NULL DEFAULT 'manual';

-- Add index for better performance
CREATE INDEX idx_environmental_savings_source_type ON environmental_savings(recipe_source_type);
CREATE INDEX idx_environmental_savings_recipe_uid_source ON environmental_savings(recipe_uid, recipe_source_type); 