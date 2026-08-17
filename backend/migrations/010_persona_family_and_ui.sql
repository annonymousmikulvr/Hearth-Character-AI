ALTER TABLE personas ADD COLUMN family_tree TEXT;
ALTER TABLE personas ADD COLUMN relationships TEXT;

INSERT OR IGNORE INTO settings (key, value) VALUES ('custom_ui_packs', '[]');
