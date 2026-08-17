-- Deep character profile, filter level, avatar, family tree
-- Message delete / rewind support uses existing messages table

ALTER TABLE characters ADD COLUMN avatar_path TEXT;
ALTER TABLE characters ADD COLUMN filter_level TEXT NOT NULL DEFAULT 'mature';
-- filter_level: strict | moderate | mature | unfiltered

ALTER TABLE characters ADD COLUMN age TEXT;
ALTER TABLE characters ADD COLUMN pronouns TEXT;
ALTER TABLE characters ADD COLUMN height TEXT;
ALTER TABLE characters ADD COLUMN build TEXT;
ALTER TABLE characters ADD COLUMN hair TEXT;
ALTER TABLE characters ADD COLUMN eyes TEXT;
ALTER TABLE characters ADD COLUMN skin TEXT;
ALTER TABLE characters ADD COLUMN clothing TEXT;
ALTER TABLE characters ADD COLUMN appearance_description TEXT;

ALTER TABLE characters ADD COLUMN traits TEXT;  -- JSON array
ALTER TABLE characters ADD COLUMN likes TEXT;
ALTER TABLE characters ADD COLUMN dislikes TEXT;
ALTER TABLE characters ADD COLUMN habits TEXT;
ALTER TABLE characters ADD COLUMN speaking_style TEXT;
ALTER TABLE characters ADD COLUMN occupation TEXT;
ALTER TABLE characters ADD COLUMN location TEXT;
ALTER TABLE characters ADD COLUMN biography TEXT;
ALTER TABLE characters ADD COLUMN additional_facts TEXT;  -- JSON array
ALTER TABLE characters ADD COLUMN how_they_act TEXT;
ALTER TABLE characters ADD COLUMN how_they_respond TEXT;
ALTER TABLE characters ADD COLUMN custom_instructions TEXT;
ALTER TABLE characters ADD COLUMN family_tree TEXT;  -- JSON array of FamilyMember
ALTER TABLE characters ADD COLUMN relationships TEXT;  -- JSON array of freeform relationships
ALTER TABLE characters ADD COLUMN goals TEXT;
ALTER TABLE characters ADD COLUMN fears TEXT;
ALTER TABLE characters ADD COLUMN secrets TEXT;
ALTER TABLE characters ADD COLUMN image_gen_enabled INTEGER NOT NULL DEFAULT 0;
ALTER TABLE characters ADD COLUMN image_gen_style TEXT;

-- App settings for optional local image backend
INSERT OR IGNORE INTO settings (key, value) VALUES ('image_backend_url', '');
INSERT OR IGNORE INTO settings (key, value) VALUES ('image_backend_enabled', 'false');
INSERT OR IGNORE INTO settings (key, value) VALUES ('image_default_model', '');
