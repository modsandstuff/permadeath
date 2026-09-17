from pathlib import Path
import io,json,struct,sys,zipfile

zip_path=Path(sys.argv[1]); src_path=Path(sys.argv[2]); out_path=Path(sys.argv[3])
src=src_path.read_text()
with zipfile.ZipFile(zip_path) as outer:
    wn=next(n for n in outer.namelist() if n.upper().endswith('MORDOR.WIP'))
    wip=outer.read(wn)
with zipfile.ZipFile(io.BytesIO(wip)) as inner:
    def get(name):
        n=next(x for x in inner.namelist() if x.upper().endswith(name))
        return inner.read(n)
    bs=get('MDATA2.MDR'); bi=get('MDATA3.MDR'); bm=get('MDATA5.MDR'); bd=get('MDATA11.MDR')

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

def spells(b):
    n=R(b,75,2).u16(); out=[]
    for k in range(n):
        r=R(b,75,3+k)
        x={'name':r.string(),'id':r.i16(),'cat':r.i16(),'level':r.i16(),'u4':r.i16(),'kill':r.i16(),'monster':r.i16(),'group':r.i16(),'d1':r.i16(),'d2':r.i16(),'effect':r.i16()}
        x['req']=[r.i16() for _ in range(7)];x['resist']=r.i16();out.append(x)
    return out

def items(b):
    n=R(b,125,3).u16(); out=[]
    for k in range(n):
        r=R(b,125,4+k)
        x={'name':r.string(),'id':r.i16(),'att':r.i16(),'def':r.i16(),'price':r.i32(),'floor':r.i16(),'rarity':r.i16(),'abilities':r.i32(),'swings':r.i16(),'special':r.i16(),'spellIndex':r.i16(),'spellId':r.i16(),'charges':r.i32(),'guilds':r.i32(),'scale':r.i16(),'damage':r.f32(),'align':r.i32(),'hands':r.i16(),'type':r.i16(),'resFlags':r.i32()}
        x['req']=[r.i16() for _ in range(7)];x['mods']=[r.i16() for _ in range(7)];x['cursed']=r.i16();x['spellLvl']=r.i16();x['restricted']=r.i16();out.append(x)
    return out

def monsters(b):
    n=R(b,160,3).u16();out=[]
    for k in range(n):
        r=R(b,160,4+k)
        x={'name':r.string(),'att':r.i16(),'def':r.i16(),'id':r.i16(),'hits':r.i16(),'groups':r.i16(),'pic':r.i16(),'lock':r.i16(),'found':r.i16()}
        x['res']=[r.i16() for _ in range(12)];x['props']=r.i32();x['special']=r.i32();x['spellFlags']=r.i32();x['chance']=r.i16();x['box']=[r.i16() for _ in range(4)];x['align']=r.i16();x['ingroup']=r.i16();x['goldFactor']=r.i32();x['traps']=r.i32();x['guildLevel']=r.i16();x['stats']=[r.i16() for _ in range(7)];x['type']=r.i16();x['damage']=r.f32();x['companionType']=r.i16();x['spawnMode']=r.i16();x['companionId']=r.i16();x['items']=[r.i16() for _ in range(11)];x['subtype']=r.i16();x['companionSubtype']=r.i16();x['size']=r.i16();x['dropLevel']=r.i16();x['itemChance']=r.i16();out.append(x)
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

data={'spells':spells(bs),'items':items(bi),'monsters':monsters(bm),'floors':dungeon(bd)}
print('parsed:',len(data['spells']),'spells,',len(data['items']),'items,',len(data['monsters']),'monsters,',len(data['floors']),'floors')
packed=json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
src=src.replace('<script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>','')
src=src.replace("const SHARE='https://raw.githubusercontent.com/matteo-prosperi/DungeonsOfDejremake/main/tests/fixtures/MORDOR11.ZIP';",'const EMBEDDED_DATA='+packed+';')
old="async function autoLoad(){try{let res=await fetch(SHARE,{cache:'force-cache'});if(!res.ok)throw Error('HTTP '+res.status);readPackage(await res.arrayBuffer())}catch(e){$('#loadText').textContent='Automatic download failed: '+e.message;$('#manual').hidden=false;$('#prog').value=0}}"
new="function autoLoad(){try{$('#loadText').textContent='Starting embedded Mordor data…';$('#prog').value=100;data=EMBEDDED_DATA;startGame()}catch(e){$('#loadText').textContent='Embedded data error: '+e.message;$('#prog').value=0}}"
if old not in src:raise SystemExit('autoLoad signature not found')
src=src.replace(old,new)
src=src.replace('Downloading the original 2.5 MB shareware package.','Starting embedded PUBLIC v1.1 data. No download or decompression is required.')
src=src.replace('The PUBLIC/shareware package is loaded at runtime.','The PUBLIC/shareware records are pre-extracted and embedded in this page.')
src=src.replace('<title>Mordor Web — unofficial shareware browser adaptation</title>','<title>Mordor Web — static embedded build</title>')
out_path.parent.mkdir(parents=True,exist_ok=True);out_path.write_text(src)
print('built',out_path,out_path.stat().st_size,'bytes')
