from pathlib import Path
import json, math, re, subprocess, tempfile

root = Path(__file__).resolve().parents[1]
src_path = root / 'mordor-static' / 'index.html'
out_path = root / 'mordor-faithful' / 'index.html'
html = src_path.read_text(encoding='utf-8')

marker = 'const EMBEDDED_DATA='
pos = html.find(marker)
if pos < 0:
    raise SystemExit('EMBEDDED_DATA marker not found in mordor-static/index.html')

# Decode the embedded PUBLIC v1.1 tables, then re-serialize as strict JSON.
decoder = json.JSONDecoder()
raw_start = pos + len(marker)
obj, consumed = decoder.raw_decode(html[raw_start:])
raw_end = raw_start + consumed

# Remove the giant data object from executable JavaScript. Mobile browsers now
# parse only the engine as JavaScript; the original data sits in an inert JSON
# element and is parsed after startup.
end = raw_end
while end < len(html) and html[end].isspace():
    end += 1
if end < len(html) and html[end] == ';':
    end += 1
html = html[:pos] + html[end:]

def clean(v):
    if isinstance(v, float) and not math.isfinite(v):
        return 0
    if isinstance(v, list):
        return [clean(x) for x in v]
    if isinstance(v, dict):
        return {k: clean(x) for k, x in v.items()}
    return v

obj = clean(obj)
data_json = json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('</', '<\\/')
data_tag = '<script id="mordor-data" type="application/json">' + data_json + '</script>\n'
main_script = '<script>\n(()=>{'
if main_script not in html:
    raise SystemExit('Main script start not found')
html = html.replace(main_script, data_tag + main_script, 1)

old = 'let data=EMBEDDED_DATA, state=null, encounter=null, current=\'town\';'
new = 'let data=JSON.parse(document.getElementById("mordor-data").textContent), state=null, encounter=null, current=\'town\';'
if old not in html:
    raise SystemExit('data initialization not found')
html = html.replace(old, new, 1)

# Correct the city name while preserving Dejenol as the dungeon name.
html = html.replace('City of Dejenol', 'City of Marlith')
html = html.replace('Mordor Web — instant static build', 'Mordor: The Depths of Dejenol — PUBLIC v1.1 Browser Edition')

# Independent startup-error reporter: a failure should display on the loading
# panel rather than looking like a permanent 10% load.
reporter = '''<script>
window.addEventListener('error',function(e){
  var t=document.getElementById('loadText'),p=document.getElementById('prog');
  if(t)t.textContent='Startup error: '+(e.message||'unknown browser error');
  if(p)p.value=0;
});
</script>\n'''
html = html.replace(data_tag + main_script, data_tag + reporter + main_script, 1)

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(html, encoding='utf-8')

# Syntax-check all ordinary inline scripts. The application/json element is
# intentionally ignored because it is data rather than executable source.
scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.S|re.I)
checked = 0
for script in scripts:
    if not script.strip():
        continue
    with tempfile.NamedTemporaryFile('w', suffix='.js', encoding='utf-8', delete=False) as f:
        f.write(script)
        name = f.name
    subprocess.run(['node', '--check', name], check=True)
    Path(name).unlink(missing_ok=True)
    checked += 1

print(f'Built {out_path} ({out_path.stat().st_size} bytes); checked {checked} executable scripts')
print('PUBLIC data:', len(obj.get('spells', [])), 'spells,', len(obj.get('items', [])), 'items,', len(obj.get('monsters', [])), 'monsters,', len(obj.get('floors', [])), 'floors')
