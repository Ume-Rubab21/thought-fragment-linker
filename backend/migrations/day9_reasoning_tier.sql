-- Run once against the ThoughtLinker PostgreSQL database.
ALTER TABLE ai_suggestions ADD COLUMN IF NOT EXISTS reasoning_decision VARCHAR(30);
ALTER TABLE ai_suggestions ADD COLUMN IF NOT EXISTS reasoning TEXT;
ALTER TABLE ai_suggestions ADD COLUMN IF NOT EXISTS confidence_score INTEGER;
ALTER TABLE ai_suggestions ADD COLUMN IF NOT EXISTS reasoning_tier VARCHAR(20) NOT NULL DEFAULT 'small';
ALTER TABLE ai_suggestions DROP CONSTRAINT IF EXISTS ck_ai_suggestions_confidence_score;
ALTER TABLE ai_suggestions ADD CONSTRAINT ck_ai_suggestions_confidence_score CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 100));
