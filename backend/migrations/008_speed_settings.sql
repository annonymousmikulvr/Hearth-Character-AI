INSERT OR IGNORE INTO settings (key, value) VALUES
    ('generation_speed', 'balanced'),
    ('history_limit', '24'),
    ('fast_max_tokens', '256'),
    ('fast_num_ctx', '2048'),
    ('balanced_num_ctx', '4096'),
    ('quality_num_ctx', '8192');
