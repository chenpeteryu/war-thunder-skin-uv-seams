from pathlib import Path
import json,sys,argparse,hashlib
import numpy as np,cv2
from PIL import Image
from apply_sm_material_surface_repair import read
from sm_reference_text_mask import text_mask
from apply_sm_touchup_20261110 import erase_reference
parser=argparse.ArgumentParser(description="Rebuild SM/SM2 continuous reference structure paths without native-skin crossfade")
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--baseline-dir',type=Path,required=True);parser.add_argument('--original-reference-dir',type=Path,required=True);parser.add_argument('--j16-color',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
R=args.root;P=args.output;P.mkdir(parents=True,exist_ok=True);(P/'labels_only').mkdir(exist_ok=True);(P/'candidate').mkdir(exist_ok=True)
for m,var in [('su_30sm','SM'),('su_30sm2','SM2')]:
 short='su30sm2' if var=='SM2' else 'su30sm';profile=R/f'config/recipes/{short}_touchup_20261110.json'
 if profile.exists():
  d=json.loads(profile.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
  for f,key in [(args.baseline_dir/f'{m}_c.dds','input_C_sha256'),(args.original_reference_dir/f'{m}_c.png','original_reference_C_sha256'),(args.j16_color,'J16_C_sha256'),(R/d['geometry'],'geometry_sha256')]:assert sha(f)==d[key],key
 c=read(args.baseline_dir/f'{m}_c.dds');orig=read(args.original_reference_dir/f'{m}_c.png');x0,y0,x1,y1=[840,704,1013,928];a=text_mask('SU-30\n'+var+'\nIRKUTSK',x1-x0,y1-y0,-90,'condensed',False);mask=a>0;mask[:,:62]=False;clean=erase_reference(orig,[x0,y0,x1,y1]);c[y0:y1,x0:x1,:3][mask]=clean[mask];Image.fromarray(c).save(P/'labels_only'/f'{m}_c.png',compress_level=1)
F=4096;W,H=2400,1200;bounds=(-7.2,-.65,-.6,1.65)
def raster(q,width=W,height=H):
 x0,y0=np.maximum(np.floor(q.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(q.max(0)).astype(int),[width-1,height-1]);
 if x0>x1 or y0>y1:return None
 yy,xx=np.mgrid[y0:y1+1,x0:x1+1];a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
 if abs(den)<1e-10:return None
 w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w2=1-w0-w1
 return x0,y0,x1,y1,np.stack([w0,w1,w2],2),(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
def bake(g,names,side,outer):
 xyz=g['triangle_xyz'];cent=xyz.mean(1);part=np.array(names)[g['triangle_part']];face=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);face/=np.maximum(np.linalg.norm(face,axis=1)[:,None],1e-12)
 keep=((part=='tail')|np.char.startswith(part,'rudder'))&(cent[:,2]*side>1.6)&(face[:,2]*side*(-1 if outer else 1)>.16)&(xyz[:,:,1].min(1)<1.7)&(xyz[:,:,1].max(1)>-.65)
 uvout=np.zeros((H,W,2),np.float32);depth=np.full((H,W),-1e6,np.float32);valid=np.zeros((H,W),bool)
 for pos,uv in zip(xyz[keep],g['triangle_uv'][keep]):
  q=np.column_stack([(pos[:,0]-bounds[0])/(bounds[2]-bounds[0])*(W-1),(bounds[3]-pos[:,1])/(bounds[3]-bounds[1])*(H-1)]);r=raster(q)
  if r is None:continue
  x0,y0,x1,y1,w,inside=r;z=(w*pos[:,2]).sum(2)*side*(1 if outer else -1);v=depth[y0:y1+1,x0:x1+1];take=inside&(z>v);v[take]=z[take];uvout[y0:y1+1,x0:x1+1][take]=(w[:,:,:,None]*uv[None,None]).sum(2)[take];valid[y0:y1+1,x0:x1+1][take]=True
 return uvout,valid
sg=dict(np.load(R/'aircraft/j16/j_16_c/geometry.npz'));sn=json.loads((R/'aircraft/j16/j_16_c/metadata.json').read_text(encoding='utf-8'))['part_names'];source=read(args.j16_color);gray=cv2.cvtColor(source[:,:,:3],cv2.COLOR_RGB2GRAY);closed=cv2.morphologyEx(gray,cv2.MORPH_CLOSE,np.ones((19,19),np.uint8));ink=np.clip(gray.astype(float)-closed.astype(float),-150,0).astype('float32');ink[gray>95]=0
bakes={(s,o):bake(sg,sn,s,o) for s in [-1,1] for o in [False,True]};print('4 raw UV side-plane maps built',flush=True)
ink_planes={}
for key,(uv,valid) in bakes.items():
 plane=cv2.remap(gray,uv[:,:,0]*source.shape[1]-.5,(1-uv[:,:,1])*source.shape[0]-.5,cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP);plane[~valid]=170
 close=cv2.morphologyEx(plane,cv2.MORPH_CLOSE,np.ones((19,19),np.uint8));raw=np.clip(plane.astype(float)-close.astype(float),-150,0).astype('float32');raw[plane>95]=0
 lines=cv2.HoughLinesP(((raw<-15)*255).astype('uint8'),1,np.pi/1440,70,minLineLength=160,maxLineGap=3);long=np.zeros((H,W),np.uint8)
 if lines is not None:
  for x1,y1,x2,y2 in lines[:,0]:cv2.line(long,(x1,y1),(x2,y2),255,4,cv2.LINE_AA)
 # Continuous long reference structure paths above the lower technical stencil:
 # discard repeated short hatch strokes, without copying foreign manufacturer's ink.
 yy=np.arange(H)[:,None];world_y=bounds[3]-yy/(H-1)*(bounds[3]-bounds[1]);ink_planes[key]=np.where(world_y>.45,-110*long.astype('float32')/255,raw).astype('float32')
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
for short,m in [('su30sm','su_30sm'),('su30sm2','su_30sm2')]:
 c=np.array(Image.open(P/'labels_only'/f'{m}_c.png'));base=c.copy();g=dict(np.load(R/f'aircraft/{short}/{m}_c/geometry.npz'));names=json.loads((R/f'aircraft/{short}/{m}_c/metadata.json').read_text(encoding='utf-8'))['part_names'];xyz=g['triangle_xyz'];cent=xyz.mean(1);part=np.array(names)[g['triangle_part']];face=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);face/=np.maximum(np.linalg.norm(face,axis=1)[:,None],1e-12)
 weight=np.zeros((F,F),np.float32);sxy=np.zeros((F,F,2),np.float32);ink_weight=weight.copy();ink_delta=weight.copy()
 keep=((part=='tail')|np.char.startswith(part,'rudder'))&(abs(cent[:,2])>1.6)&(abs(face[:,2])>.16)&(xyz[:,:,1].min(1)<1.65)&(xyz[:,:,1].max(1)>-.65)&(xyz[:,:,0].max(1)>-7.1)
 for tid in np.flatnonzero(keep):
  uv=g['triangle_uv'][tid];pos=xyz[tid];q=np.column_stack([uv[:,0]*F-.5,(1-uv[:,1])*F-.5]);r=raster(q,F,F)
  if r is None:continue
  x0,y0,x1,y1,bary,inside=r;p=(bary[:,:,:,None]*pos[None,None]).sum(2);side=1 if cent[tid,2]>0 else -1;outer=bool(face[tid,2]*side<0);buv,valid=bakes[side,outer]
  px=((p[:,:,0]-bounds[0])/(bounds[2]-bounds[0])*(W-1)).astype('float32');py=((bounds[3]-p[:,:,1])/(bounds[3]-bounds[1])*(H-1)).astype('float32');srcuv=cv2.remap(buv,px,py,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT);ok=cv2.remap(valid.astype('uint8'),px,py,cv2.INTER_NEAREST)>0
  w=smooth(-.65,-.35,p[:,:,1])*(1-smooth(1.4,1.65,p[:,:,1]))*smooth(-7.05,-6.65,p[:,:,0])*(1-smooth(-1.1,-.8,p[:,:,0]))*smooth(1.65,1.9,abs(p[:,:,2]));w[~inside]=0;v=weight[y0:y1+1,x0:x1+1];take=w>v;v[take]=w[take];dest=sxy[y0:y1+1,x0:x1+1];dest[take,0]=srcuv[take,0]*source.shape[1]-.5;dest[take,1]=(1-srcuv[take,1])*source.shape[0]-.5
  # Exclude source manufacturer logo while retaining the surrounding panel boundary.
  foreign=(p[:,:,0]>-3.95)&(p[:,:,0]<-3.15)&(p[:,:,1]>.28)&(p[:,:,1]<1.40)
  ink_weight[y0:y1+1,x0:x1+1][take]=(w*ok*(~foreign))[take]
  delta=cv2.remap(ink_planes[side,outer],px,py,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);ink_delta[y0:y1+1,x0:x1+1][take]=delta[take]
 # Preserve approved glyphs precisely; preserve whole original world/project artworks.
 protect=np.load(R/f'config/recipes/{short}_surface_adaptation.npz')['marking_ink_alpha_u8']>0;protect=cv2.dilate(protect.astype('uint8'),np.ones((3,3),np.uint8))>0
 for box in [[985,945,1205,1160],[1010,270,1137,323],[323,16,351,92]]:
  x0,y0,x1,y1=np.rint(np.array(box)*F/1536).astype(int);protect[y0:y1,x0:x1]=True
 weight[protect]=0;ink_weight[protect]=0
 ix=np.flatnonzero(weight.ravel()>0);coords=sxy.reshape(-1,2)[ix];w=weight.ravel()[ix];iw=ink_weight.ravel()[ix];flat=c.reshape(-1,4);graybase=flat[ix,:3].mean(1);neutral=(graybase>130)&(graybase<210)&(np.ptp(flat[ix,:3].astype(int),axis=1)<7);level=float(np.median(graybase[(w>.8)&neutral]));values=flat[ix,:3].astype(float).copy();values[neutral]=level
 delta=ink_delta.ravel()[ix];values[neutral]=np.minimum(values[neutral],level+delta[neutral,None]*iw[neutral,None]);flat[ix,:3]=np.rint(flat[ix,:3]*(1-w[:,None])+values*w[:,None]).astype('uint8')
 np.savez_compressed(P/f'{short}_continuous_root_20261110.npz',target_pixels=ix.astype(np.int32),source_xy_times32_int32=np.rint(coords*32).astype(np.int32),weight_float32=w,ink_weight_float32=iw,neutral=neutral,coating_level=np.float32(level))
 # Keep SU in its original place and remove only the trailing -30.
 # Final small title trim uses the same original glyphs and substrate.
 x0,y0,x1,y1=[267,2408,373,2437];alpha=text_mask('SU-30',x1-x0,y1-y0,180,'condensed',False);mask=alpha>0;mask[:,54:]=False;original=read(args.original_reference_dir/f'{m}_c.png');clean=erase_reference(original,[x0,y0,x1,y1]);c[y0:y1,x0:x1,:3][mask]=clean[mask]
 for ext in ['png','dds']:Image.fromarray(c).save(P/'candidate'/f'{m}_c.{ext}')
 print(m,'continuous root pixels',len(ix),'paint',level,'changed',int(np.any(c!=base,axis=2).sum()),flush=True)
