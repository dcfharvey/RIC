from pathlib import Path

path = Path('.sol-final/patch.py')
text = path.read_text(encoding='utf-8')
old = "control = replace_once(\n    '"
new = "control = replace_once(\n    control,\n    '"
count = text.count(old)
if count < 1:
    raise SystemExit('no missing control argument found; refusing unexpected patch source')
text = text.replace(old, new)
text = text.replace('{"protected_path", "file_missing"}', '{"protected_path", "file_missing", "path_outside_root"}')
path.write_text(text, encoding='utf-8')
print(f'repaired {count} control transform calls')
