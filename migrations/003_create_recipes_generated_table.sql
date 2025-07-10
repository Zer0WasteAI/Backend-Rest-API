-- Migration: Create recipes_generated table
-- Purpose: Store auto-generated recipes from both custom and inventory generation
-- Date: 2025-06-24

CREATE TABLE IF NOT EXISTS recipes_generated (
    uid VARCHAR(36) PRIMARY KEY,
    user_uid VARCHAR(36) NOT NULL,
    generation_id VARCHAR(36) NOT NULL,
    
    -- Recipe fields
    title VARCHAR(255) NOT NULL,
    description TEXT(500),
    duration VARCHAR(50),
    difficulty VARCHAR(50),
    servings INT,
    category VARCHAR(50),
    
    -- Recipe data (JSON)
    recipe_data JSON NOT NULL,
    
    -- Metadata
    generation_type VARCHAR(20) NOT NULL,
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    image_path VARCHAR(1000),
    image_status VARCHAR(50) DEFAULT 'generating',
    
    -- Indexes
    INDEX idx_user_uid (user_uid),
    INDEX idx_generation_id (generation_id),
    INDEX idx_title (title),
    INDEX idx_user_title (user_uid, title),
    INDEX idx_generated_at (generated_at),
    
    -- Foreign keys
    FOREIGN KEY (user_uid) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (generation_id) REFERENCES generations(uid) ON DELETE CASCADE
);

-- Add comment
ALTER TABLE recipes_generated COMMENT = 'Stores automatically generated recipes from AI generation endpoints'; 