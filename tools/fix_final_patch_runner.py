from pathlib import Path

path = Path('.sol-final/patch.py')
text = path.read_text(encoding='utf-8')
repairs = {
    "control": "control",
    "test": "test",
}
counts = {}
for lhs, variable in repairs.items():
    old = f"{lhs} = replace_once(\n    '"
    new = f"{lhs} = replace_once(\n    {variable},\n    '"
    count = text.count(old)
    counts[lhs] = count
    text = text.replace(old, new)
if sum(counts.values()) < 1:
    raise SystemExit('no missing transform receiver found; refusing unexpected patch source')
text = text.replace('{"protected_path", "file_missing"}', '{"protected_path", "file_missing", "path_outside_root"}')
path.write_text(text, encoding='utf-8')
print(f'repaired transform receivers: {counts}')
