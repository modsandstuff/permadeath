from pathlib import Path
import io,json,math,struct,sys,zipfile,re

zip_path=Path(sys.argv[1]); src_path=Path(sys.argv[2]); out_path=Path(sys.argv[3])
json_path=Path(sys.argv[4]) if len(sys.argv)>4 else out_path.parent.parent/'mordor-data'/'public-v11.json'
src=src_path.read_text(encoding='utf-8')
with zipfile.ZipFile(zip_path) as outer:
    wn=next(n for n in outer.namelist() if n.upper().endswith('MORDOR.WIP'))
    wip=outer.read(wn)
with zipfile.ZipFile(io.BytesIO(wip)) as inner:
    def get(name):
        n=next(x for x in inner.namelist() if x.upper().endswith(name))
        return inner.read(n)
    bg=get('MDATA1.MDR'); bs=get('MDATA2.MDR'); bi=get('MDATA3.MDR'); bm=get('MDATA5.MDR'); bd=get('MDATA11.MDR')

class R:
    def __init__(self,b,L,n):
        o=(n-1)*L; self.b=memoryview(b)[o:o+L]; self.p=0
    def i16(self): v=struct.unpack_from('<h',self.b,self.p)[0]; self.p+=2; return v
    def u16(self): v=struct.unpack_from('<H',self.b,self.p)[0]; self.p+=2; return v
    def i32(self): v=struct.unpack_from('<i',self.b,self.p)[0]; self.p+=4; return v
    def f32(self): v=struct.unpack_from('<f',self.b,self.p)[0]; self.p+=4; return v
    def cur(self): v=struct.unpack_from('<q',self.b,self.p)[0]; self.p+=8; return int(v/10000)
    def string(self,n=0):
        if not n:n=self.u16()
        if self.p+n>len(self.b): raise ValueError(f'string {n} exceeds record at {self.p}/{len(self.b)}')
        raw=bytes(self.b[self.p:self.p+n]); self.p+=n
        return raw.decode('cp1252',errors='replace').rstrip('\0').strip()

def clean_num(v):
    return v if not isinstance(v,float) or math.isfinite(v) else 0.0

def gameinfo(b):
    rec=1
    version=R(b,260,rec).string(); rec+=1
    counts=[]
    for _ in range(6): counts.append(R(b,260,rec).u16()); rec+=1
    nr,ng,nis,nit,nms,nmt=counts
    races=[]
    for _ in range(nr):
        r=R(b,260,rec);rec+=1
        x={'name':r.string()}
        x['min']=[r.i16() for _ in range(7)]; x['max']=[r.i16() for _ in range(7)]
        x['res']=[r.i16() for _ in range(12)]; x['alignment']=r.i32(); x['size']=r.i16(); x['bonusPoints']=r.i16(); x['maxAge']=r.i16(); x['expFactor']=clean_num(r.f32()); races.append(x)
    guilds=[]
    for _ in range(ng):
        r=R(b,260,rec);rec+=1
        x={'name':r.string(),'averageHits':r.i16(),'maxHitLevel':r.i16(),'minHits':r.i16(),'expFactor':clean_num(r.f32()),'unused1':r.i16()}
        x['req']=[r.i16() for _ in range(7)]; x['alignment']=r.i32(); x['abilityRates']=[clean_num(r.f32()) for _ in range(7)]
        x['quested']=r.i16(); x['unused2']=clean_num(r.f32()); x['questPercentage']=r.i16()
        x['spellMods']=[clean_num(r.f32()) for _ in range(19)]; x['spellCaps']=[clean_num(r.f32()) for _ in range(19)]
        x['raceMask']=r.i32(); x['goldFactor']=r.i16(); x['levelScale']=clean_num(r.f32()); x['attack']=clean_num(r.f32()); x['defence']=clean_num(r.f32()); x['maxADLevel']=r.i16(); x['adRate']=clean_num(r.f32()); x['unused3']=r.i16(); x['unused4']=r.i16(); guilds.append(x)
    item_sub=[]
    for _ in range(nis):
        r=R(b,260,rec);rec+=1; item_sub.append({'name':r.string(),'itemType':r.i16()})
    item_types=[]
    for _ in range(nit):
        r=R(b,260,rec);rec+=1; item_types.append({'name':r.string(),'equippable':r.i16()})
    mon_sub=[]
    for _ in range(nms):
        r=R(b,260,rec);rec+=1; mon_sub.append({'name':r.string(),'monsterType':r.i16()})
    mon_types=[]
    for _ in range(nmt):
        r=R(b,260,rec);rec+=1; mon_types.append({'name':r.string(),'unused':r.i16()})
    return {'version':version,'races':races,'guilds':guilds,'itemSubtypes':item_sub,'itemTypes':item_types,'monsterSubtypes':mon_sub,'monsterTypes':mon_types}

def spells(b):
    n=R(b,75,2).u16(); out=[]
    for k in range(n):
        r=R(b,75,3+k)
        x={'name':r.string(),'id':r.i16(),'cat':r.i16(),'level':r.i16(),'cost':r.i16(),'zero':r.i16(),'kill':r.i16(),'monster':r.i16(),'group':r.i16(),'d1':r.i16(),'d2':r.i16(),'effect':r.i16()}
        x['req']=[r.i16() for _ in range(7)];x['resist']=r.i16();out.append(x)
    return out

def items(b):
    n=R(b,125,3).u16(); out=[]
    for k in range(n):
        r=R(b,125,4+k)
        x={'name':r.string(),'id':r.i16(),'att':r.i16(),'def':r.i16(),'price':r.i32(),'floor':r.i16(),'rarity':r.i16(),'abilities':r.i32(),'swings':r.i16(),'special':r.i16(),'spellIndex':r.i16(),'spellId':r.i16(),'charges':r.i32(),'guilds':r.i32(),'scale':r.i16(),'damage':clean_num(r.f32()),'align':r.i32(),'hands':r.i16(),'type':r.i16(),'resFlags':r.i32()}
        x['req']=[r.i16() for _ in range(7)];x['mods']=[r.i16() for _ in range(7)];x['cursed']=r.i16();x['spellLvl']=r.i16();x['restricted']=r.i16();out.append(x)
    return out

def monsters(b):
    n=R(b,160,3).u16();out=[]
    for k in range(n):
        r=R(b,160,4+k)
        x={'name':r.string(),'att':r.i16(),'def':r.i16(),'id':r.i16(),'hits':r.i16(),'groups':r.i16(),'pic':r.i16(),'lock':r.i16(),'found':r.i16()}
        x['res']=[r.i16() for _ in range(12)];x['props']=r.i32();x['special']=r.i32();x['spellFlags']=r.i32();x['chance']=r.i16();x['box']=[r.i16() for _ in range(4)];x['align']=r.i16();x['ingroup']=r.i16();x['goldFactor']=r.i32();x['traps']=r.i32();x['guildLevel']=r.i16();x['stats']=[r.i16() for _ in range(7)];x['type']=r.i16();x['damage']=clean_num(r.f32());x['companionType']=r.i16();x['spawnMode']=r.i16();x['companionId']=r.i16();x['items']=[r.i16() for _ in range(11)];x['subtype']=r.i16();x['companionSubtype']=r.i16();x['size']=r.i16();x['dropLevel']=r.i16();x['itemChance']=r.i16();out.append(x)
    return out

def dungeon(b):
    levels=R(b,20,1).u16();offs=[R(b,20,2+i).u16() for i in range(levels)];out=[]
    for off in offs:
        rec=off;r=R(b,20,rec);rec+=1
        w,h,lv=r.u16(),r.u16(),r.u16();na,nc,nt=r.u16(),r.u16(),r.u16()
        f={'w':w,'h':h,'level':lv,'fields':[],'areas':[],'tele':[],'chutes':[]}
        for _ in range(w*h):
            r=R(b,20,rec);rec+=1;f['fields'].append({'area':r.i16(),'flags':r.cur()})
        r=R(b,20,rec);rec+=1;r.u16()
        for _ in range(201):
            r=R(b,20,rec);rec+=1;f['areas'].append({'spawn':r.i32(),'lair':r.i16()})
        r=R(b,20,rec);rec+=1;r.u16()
        for _ in range(nt):
            r=R(b,20,rec);rec+=1;t={'x':r.i16(),'y':r.i16(),'x2':r.i16(),'y2':r.i16(),'z2':r.i16()}
            if t['x']>0 and t['y']>0:f['tele'].append(t)
        r=R(b,20,rec);rec+=1;r.u16()
        for _ in range(nc):
            r=R(b,20,rec);rec+=1;c={'x':r.i16(),'y':r.i16(),'depth':r.i16()}
            if c['x']>0 and c['y']>0:f['chutes'].append(c)
        out.append(f)
    return out

data={'game':gameinfo(bg),'spells':spells(bs),'items':items(bi),'monsters':monsters(bm),'floors':dungeon(bd)}
print('parsed:',len(data['game']['races']),'races,',len(data['game']['guilds']),'guilds,',len(data['spells']),'spells,',len(data['items']),'items,',len(data['monsters']),'monsters,',len(data['floors']),'floors')
packed=json.dumps(data,separators=(',',':'),ensure_ascii=True,allow_nan=False)
json_path.parent.mkdir(parents=True,exist_ok=True);json_path.write_text(packed,encoding='utf-8')
print('wrote',json_path,json_path.stat().st_size,'bytes')

src=src.replace('<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>','')
if "const SHARE='https://raw.githubusercontent.com/matteo-prosperi/DungeonsOfDejremake/main/tests/fixtures/MORDOR11.ZIP';" in src:
    src=src.replace("const SHARE='https://raw.githubusercontent.com/matteo-prosperi/DungeonsOfDejremake/main/tests/fixtures/MORDOR11.ZIP';",'const EMBEDDED_DATA='+packed+';')
    pat=r"let data=\{spells:\[\],items:\[\],monsters:\[\],floors:\[\]\}, state=null, encounter=null, current='town';\s*let td=new TextDecoder\('windows-1252'\);.*?\$\('#zipFile'\)\.addEventListener\('change'.*?\);\s*function fresh"
    replacement="let data=EMBEDDED_DATA, state=null, encounter=null, current='town';\nfunction fresh"
    src,n=re.subn(pat,replacement,src,count=1,flags=re.S)
    if n!=1: raise SystemExit(f'could not strip runtime parser: {n}')
    src=src.replace("setInterval(()=>$('#clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),1000);$('#clock').textContent='';autoLoad();", "setInterval(()=>$('#clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'}),1000);$('#clock').textContent='';$('#prog').value=100;startGame();")
elif 'const EMBEDDED_DATA=' in src:
    marker='const EMBEDDED_DATA='; p=src.index(marker)+len(marker); obj,used=json.JSONDecoder().raw_decode(src[p:]); e=p+used
    src=src[:p]+packed+src[e:]
else:
    raise SystemExit('No data marker found in source HTML')
src=src.replace('Downloading the original 2.5 MB shareware package.','Starting embedded PUBLIC v1.1 data. No download, decoding or decompression is required.')
out_path.parent.mkdir(parents=True,exist_ok=True);out_path.write_text(src,encoding='utf-8')
print('built',out_path,out_path.stat().st_size,'bytes')
