-- Final AI-authored content migration
ALTER TABLE ai_suggestions
ADD COLUMN IF NOT EXISTS suggested_content TEXT;

-- Existing suggestions remain readable. New suggestions are AI-rewritten.
UPDATE ai_suggestions AS suggestion
SET suggested_content = dump.raw_text
FROM braindumps AS dump
WHERE suggestion.brain_dump_id = dump.id
  AND (suggestion.suggested_content IS NULL OR btrim(suggestion.suggested_content) = '');
