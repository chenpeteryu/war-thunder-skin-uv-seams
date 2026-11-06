from pathlib import Path
import io,json,re,struct,hashlib,shutil
import numpy as np
import cv2
from PIL import Image,ImageDraw
from build_missiles import ROOT,LIB,PROJECT,OUT,PREVIEW,TARGETS,decode_header,unpack_level,pack_level,rgba

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def read_levels(p):
    data=p.read_bytes();h,w=struct.unpack_from('<II',data,12);levels=max(1,struct.unpack_from('<I',data,28)[0])
    fourcc=data[84:88];out=[];pos=128;ww,hh=w,h
    if fourcc==b'\0\0\0\0':
        _,_,_,masks,shifts=decode_header(data)
        for level in range(levels):
            sz=ww*hh*4;out.append(unpack_level(data[pos:pos+sz],ww,hh,masks,shifts));pos+=sz;ww=max(1,ww//2);hh=max(1,hh//2)
        return data[:128],out,False
    if fourcc not in (b'DXT1',b'DXT3',b'DXT5',b'ATI1',b'ATI2'):raise ValueError(f'Unsupported DDS format {fourcc!r}: {p}')
    for level in range(levels):
        sz=max(1,(ww+3)//4)*max(1,(hh+3)//4)*(8 if fourcc in (b'DXT1',b'ATI1') else 16)
        header=bytearray(data[:128]);struct.pack_into('<II',header,12,hh,ww);struct.pack_into('<I',header,28,1)
        out.append(np.array(Image.open(io.BytesIO(bytes(header)+data[pos:pos+sz])).convert('RGBA')))
        pos+=sz;ww=max(1,ww//2);hh=max(1,hh//2)
    assert pos==len(data)
    return data[:128],out,True

def write_levels(path,source_header,levels,compressed):
    if not compressed:
        header=source_header;_,_,_,masks,shifts=decode_header(header)
    else:
        b=io.BytesIO();Image.fromarray(levels[0]).save(b,format='DDS');header=bytearray(b.getvalue()[:128])
        struct.pack_into('<I',header,28,max(1,len(levels)))
        if len(levels)>1:
            flags=struct.unpack_from('<I',header,8)[0];struct.pack_into('<I',header,8,flags|0x20000)
            struct.pack_into('<I',header,108,0x401008)
        header=bytes(header);_,_,_,masks,shifts=decode_header(header)
    path.write_bytes(header+b''.join(pack_level(a,shifts) for a in levels))

def modes(a):
    rgb=a[:,:,:3].astype(np.float32);lum=np.rint(rgb.mean(2)).astype(np.uint8);sat=rgb.max(2)-rgb.min(2)
    dark=(lum>25)&(lum<115)&(sat<10);light=(lum>155)&(lum<250)&(sat<10)
    return (int(np.bincount(lum[dark],minlength=256).argmax()) if dark.any() else 56,
            int(np.bincount(lum[light],minlength=256).argmax()) if light.any() else 229)

def masks(a):
    rgb=a[:,:,:3].astype(np.float32);r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    yellow=(r>180)&(g>180)&(b<135)&(r-b>100)&(g-b>100)&(np.abs(r-g)<55)
    count,labels,stats,_=cv2.connectedComponentsWithStats(yellow.astype(np.uint8),8)
    selected=[];area_total=a.shape[0]*a.shape[1]
    for idx in range(1,count):
        x,y,w,h,area=stats[idx];ratio=max(w,h)/max(1,min(w,h));fill=area/(w*h)
        # Retain narrow warning bars and small warning/maintenance symbols.
        # Do not turn the large DANGER lettering or whole colored panels yellow.
        bar=ratio>7 and area>area_total*.00003
        symbol=area_total*.000005<area<area_total*.00023 and .42<w/max(1,h)<2.4 and .22<fill<.78
        if bar or symbol:selected.append(idx)
    accent=np.isin(labels,selected).astype(np.uint8)*255
    if np.mean(accent>0)>.012:
        # Some legacy skins have very large yellow bands. Retain symbols first,
        # then use four short sections of an existing stripe instead of keeping
        # a whole dominant yellow panel. No mark is moved outside its source mask.
        limited=np.zeros_like(accent);budget=round(area_total*.009)
        for idx in sorted(selected,key=lambda z:stats[z,cv2.CC_STAT_AREA]):
            ys,xs=np.nonzero(labels==idx)
            if not budget:break
            if len(xs)<=budget:limited[ys,xs]=255;budget-=len(xs);continue
            pos=ys if stats[idx,cv2.CC_STAT_HEIGHT]>=stats[idx,cv2.CC_STAT_WIDTH] else xs
            centers=np.linspace(float(pos.min()),float(pos.max()),6)[1:-1]
            distance=np.min(np.abs(pos[:,None]-centers[None,:]),axis=1)
            pick=np.argsort(distance,kind='stable')[:budget]
            limited[ys[pick],xs[pick]]=255;budget=0
        accent=limited
    gray=cv2.cvtColor(a[:,:,:3],cv2.COLOR_RGB2GRAY).astype(np.float32)
    background=cv2.GaussianBlur(gray,(0,0),max(2,a.shape[1]/300))
    small=((gray<115)&(background>175)&((rgb.max(2)-rgb.min(2))<30)).astype(np.uint8)
    count,labels,stats,_=cv2.connectedComponentsWithStats(small,8)
    ids=np.flatnonzero((stats[:,cv2.CC_STAT_AREA]>2)&(stats[:,cv2.CC_STAT_AREA]<area_total*.0015));ids=ids[ids!=0]
    marks=np.isin(labels,ids).astype(np.uint8)*255
    return accent,marks

def run():
    fresh=ROOT/'Endfield_Fresh_Contours'
    before={str(p.relative_to(fresh)):digest(p) for p in fresh.rglob('*') if p.is_file()}
    # Extract measured HIGH samples at the actual user's reference positions.
    source=rgba(ROOT/'J10C_ENDFIELD_8K/body_c.dds');k=source.shape[0]/1536
    body=int(np.median(source[round(685*k):round(725*k),round(350*k):round(600*k),0]))
    yellow=np.median(source[(source[:,:,0]>210)&(source[:,:,1]>225)&(source[:,:,2]>15)&(source[:,:,2]<150),:3],axis=0)
    del source
    source=rgba(ROOT/'J_16_ENDFIELD_HIGH/body_c.dds');k=source.shape[0]/1536
    dark=int(np.median(source[round(390*k):round(440*k),round(340*k):round(440*k),0]));lit=187
    del source
    sources={p.name:p for p in LIB.glob('*.dds')};needed={};legacy=[]
    for skin in TARGETS:
        needed[skin]=set()
        for blk in (ROOT/skin).glob('*.blk'):
            for block in re.findall(r'(?:replace_tex|set_tex)\s*\{[^{}]*\}',blk.read_text(encoding='utf-8-sig')):
                fr=re.search(r'from:t\s*=\s*"([^"]+)"',block);to=re.search(r'to:t\s*=\s*"([^"]+)"',block)
                if not fr or not to or not re.search(r'missile|su_r_73|^pl_8',fr[1]):continue
                name=to[1];needed[skin].add(name)
                if name not in sources:
                    matches=list(fresh.rglob(name))
                    preferred=fresh/'J15T'/name
                    if preferred.exists():sources[name]=preferred
                    elif matches:sources[name]=matches[0]
                    else:raise FileNotFoundError(f'No retained original source for {name}')
                    legacy.append(name)
    report={'revision':'HIGH v2 measured palette + sparse fluorescent accents; complete installed missile coverage',
      'palette':{'body_from_J10C':[body]*3,'dark_from_J16':[dark]*3,'lit_gray':[lit]*3,'fluorescent_from_J10C':yellow.tolist()},
      'material_R':102,'material_B':178,'files':[],'installed':[],'legacy_added':legacy,'fresh_unchanged':False,'runtime_verified':False}
    previews={};OUT.mkdir(exist_ok=True)
    for name,p in sorted(sources.items()):
        header,old_levels,compressed=read_levels(p);normal=p.stem.endswith('_n');base=old_levels[0];new_levels=[]
        if normal:
            cr=float(np.median(base[:,:,0]));cb=float(np.median(base[:,:,2]))
        else:
            dm,lm=modes(base);accent,marks=masks(base)
            x=np.array([0,20,dm,115,155,lm,255],float);y=np.array([28,47,dark,126,151,body,lit],float)
            # Some models' material histogram has a different mode: keep LUT monotone.
            order=np.argsort(x);x=x[order];y=np.maximum.accumulate(y[order]);unique=np.r_[True,np.diff(x)>0];x=x[unique];y=y[unique]
        for level,old in enumerate(old_levels):
            a=old.copy()
            if normal:
                a[:,:,0]=np.clip(np.rint(102+(old[:,:,0].astype(float)-cr)*.55),30,215).astype(np.uint8)
                a[:,:,2]=np.clip(np.rint(178+(old[:,:,2].astype(float)-cb)*.45),25,235).astype(np.uint8)
                assert np.array_equal(a[:,:,1],old[:,:,1]) and np.array_equal(a[:,:,3],old[:,:,3])
            else:
                rgb=old[:,:,:3].astype(np.float32);lum=rgb.mean(2);neutral=np.interp(lum,x,y)
                color=neutral[:,:,None]+(rgb-lum[:,:,None])*.035
                am=np.array(Image.fromarray(accent).resize((a.shape[1],a.shape[0]),Image.Resampling.BOX),dtype=float)/255
                mm=np.array(Image.fromarray(marks).resize((a.shape[1],a.shape[0]),Image.Resampling.BOX),dtype=float)/255
                mark_tone=134+np.clip(lum/115,0,1)*10
                color=color*(1-mm[:,:,None])+mark_tone[:,:,None]*mm[:,:,None]
                color=color*(1-am[:,:,None])+yellow*am[:,:,None]
                a[:,:,:3]=np.clip(np.rint(color),0,255).astype(np.uint8)
                assert np.array_equal(a[:,:,3],old[:,:,3])
            new_levels.append(a)
        target=OUT/name;write_levels(target,header,new_levels,compressed)
        _,check,_=read_levels(target)
        assert len(check)==len(old_levels)
        for old,new,out in zip(old_levels,new_levels,check):
            assert np.array_equal(out,new) and old.shape==out.shape
            if normal:assert np.array_equal(out[:,:,[1,3]],old[:,:,[1,3]])
            else:assert np.array_equal(out[:,:,3],old[:,:,3])
        r={'name':name,'source':str(p),'size':[base.shape[1],base.shape[0]],'mips':len(old_levels),
           'all_mips_pixel_addresses_unchanged':True,'GA_exact_all_mips':True if normal else None,
           'alpha_exact_all_mips':True if not normal else None,
           'DXT_decoded_to_lossless_RGBA':compressed,'sha256':digest(target)}
        if not normal:r['fluorescent_fraction']=float(np.mean(accent>0));r['source_gray_modes']=[dm,lm]
        report['files'].append(r)
        if name in ['pl_12a_missile_c.dds','su_r_77_missile_c.dds','us_aim_120c_missile_c.dds','su_kh_29_missile_c.dds','cn_ld_10_missile_c.dds']:
            previews[name]=(base,new_levels[0])
    for skin,files in needed.items():
        for name in sorted(files):
            shutil.copyfile(OUT/name,ROOT/skin/name);assert digest(OUT/name)==digest(ROOT/skin/name)
            report['installed'].append({'skin':skin,'file':name})
    assert all((fresh/rel).exists() and digest(fresh/rel)==h for rel,h in before.items())
    assert len(before)==sum(1 for p in fresh.rglob('*') if p.is_file())
    report['fresh_unchanged']=True;report['fresh_files_verified']=len(before)
    canvas=Image.new('RGB',(1400,220+len(previews)*445),(40,40,40));draw=ImageDraw.Draw(canvas)
    ref=Image.fromarray(rgba(ROOT/'J10C_ENDFIELD_8K/body_c.dds'));k=ref.width/1536
    ref=ref.crop(tuple(round(z*k) for z in (300,650,1100,950)));ref.thumbnail((650,185));canvas.paste(ref,(15,25))
    draw.text((730,25),'HIGH reference palette',fill='white')
    for j,(label,col) in enumerate([('BODY',body),('DARK',dark),('LIT',lit),('ACCENT',yellow)]):
        color=tuple(int(z) for z in col) if hasattr(col,'__len__') else (col,col,col)
        draw.rectangle((730+j*155,70,860+j*155,125),fill=color);draw.text((730+j*155,140),label+' '+str(color),fill='white')
    for row,(name,arrays) in enumerate(previews.items()):
        y=220+row*445;draw.text((15,y+5),name+' | retained original (left) / HIGH v2 (right)',fill='white')
        for col,a in enumerate(arrays):
            im=Image.fromarray(a[:,:,:3]);im.thumbnail((680,405));canvas.paste(im,(15+700*col,y+30))
    canvas.save(PREVIEW/'HIGH_missile_v2_comparison.jpg',quality=96)
    report['preview']=str(PREVIEW/'HIGH_missile_v2_comparison.jpg')
    (PROJECT/'validation_v2.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'generated':len(report['files']),'installed':len(report['installed']),'legacy_added':legacy,
       'fresh_files_verified':len(before),'palette':report['palette']},indent=2),flush=True)

if __name__=='__main__':run()
