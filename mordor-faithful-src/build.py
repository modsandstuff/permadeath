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

decoder = json.JSONDecoder()
raw_start = pos + len(marker)
obj, consumed = decoder.raw_decode(html[raw_start:])
raw_end = raw_start + consumed

# Keep the original PUBLIC data, but remove the giant object literal from the
# executable JS source. Android only has to parse the game engine as JS.
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

# The prior static prototype contained a real syntax error in its About click
# handler. Fix that source defect in the generated edition.
bad_about = "$('#about').onclick=()=>dialog(`"
if bad_about not in html:
    raise SystemExit('About handler pattern not found')
html = html.replace(bad_about, "$('#about').onclick=()=>{dialog(`", 1)

# Correct town name from the original game/manual; Dejenol is the dungeon.
html = html.replace('City of Dejenol', 'City of Marlith')
html = html.replace('Mordor Web — instant static build', 'Mordor: The Depths of Dejenol — PUBLIC v1.1 Browser Edition')

# Independent startup-error reporter so any future browser incompatibility is
# shown on the loading panel instead of freezing at 10%.
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

# Syntax-check every executable inline script. application/json is deliberately
# excluded because it is data, not source code.
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
