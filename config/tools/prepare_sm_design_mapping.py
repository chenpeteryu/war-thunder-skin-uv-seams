from pathlib import Path
import json, hashlib
import numpy as np
from scipy.spatial import cKDTree

P=Path(__file__).resolve().parents[2]
LIB=P/'aircraft'
def load(model,tex):
 f=LIB/model/tex
 return dict(np.load(f/'geometry.npz')),json.loads((f/'metadata.json').read_text(encoding='utf-8'))
def normals(x):
 n=np.cross(x[:,1]-x[:,0],x[:,2]-x[:,0]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)

def match(sx,su,tx,k=24):
 sn=normals(sx);tn=normals(tx)
 tree=cKDTree(sx.mean(1));_,near=tree.query(tx.mean(1),k=min(k,len(sx)),workers=4)
 if near.ndim==1:near=near[:,None]
 best=np.full(len(tx),1e10);out=np.zeros((len(tx),3,2),np.float32);errors=best.copy();align=best.copy()
 for j in range(near.shape[1]):
  idx=near[:,j];q=sx[idx].astype(np.float64);a=q[:,1]-q[:,0];b=q[:,2]-q[:,0];v=tx-q[:,None,0]
  aa=(a*a).sum(1);ab=(a*b).sum(1);bb=(b*b).sum(1);den=aa*bb-ab*ab
  av=(v*a[:,None]).sum(2);bv=(v*b[:,None]).sum(2);safe=np.maximum(den,1e-20)
  w1=(bb[:,None]*av-ab[:,None]*bv)/safe[:,None];w2=(aa[:,None]*bv-ab[:,None]*av)/safe[:,None];w=np.stack([1-w1-w2,w1,w2],2)
  wc=np.clip(w,0,1);wc/=np.maximum(wc.sum(2,keepdims=True),1e-12)
  projected=(wc[:,:,:,None]*q[:,None]).sum(2)
  error=np.linalg.norm(projected-tx,axis=2).max(1)
  dot=(sn[idx]*tn).sum(1)
  score=error+np.maximum(0,1-dot)*.35+(den<1e-18)*100
  take=score<best;best[take]=score[take];errors[take]=error[take];align[take]=dot[take]
  # Keep extrapolation for modestly different tessellation; reject/repair large
  # displacements explicitly rather than claiming geometric correspondence.
  use_w=np.where((error>.025)[:,None,None],wc,w)
  vals=(use_w[:,:,:,None]*su[idx][:,None]).sum(2)
  out[take]=vals[take]
 return out,errors,align

def run():
 import argparse
 parser=argparse.ArgumentParser(description='Rebuild artwork sampling coordinates without modifying native geometry')
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();OUT=args.output.resolve()
 if OUT.is_relative_to((P/'aircraft').resolve()):raise ValueError('Output must be outside native aircraft assets')
 OUT.mkdir(parents=True,exist_ok=True)
 s,sm=load('j16','j_16_c');reports={}
 for model,tex in [('su30sm','su_30sm_c'),('su30sm2','su_30sm2_c')]:
  t,tm=load(model,tex);attr=np.zeros_like(t['triangle_uv']);err=np.full(len(attr),100,np.float32);dot=np.zeros(len(attr),np.float32);groups=[]
  for pid in np.unique(t['triangle_part']):
   name=tm['part_names'][pid];take=t['triangle_part']==pid
   if name.startswith(('nozzle1','nozzle2','optic','prop','pylon')):continue
   if name not in sm['part_names']:continue
   source=s['triangle_part']==sm['part_names'].index(name)
   if not source.any():continue
   tx=t['triangle_xyz'][take].copy();sx=s['triangle_xyz'][source]
   if name=='fuse':
    # Preserve the rear airframe, shorten only the longer SM radar nose.
    x=tx[:,:,0];q=x>9.0;x[q]=9+(x[q]-9)*(13.078754-9)/(13.797441-9)
   if name in ['rudder0','rudder1','rudder0_1','rudder1_1']:
    for axis in [0,1]:
     lo,hi=tx[:,:,axis].min(),tx[:,:,axis].max();a,b=sx[:,:,axis].min(),sx[:,:,axis].max()
     tx[:,:,axis]=a+(tx[:,:,axis]-lo)*(b-a)/max(hi-lo,1e-9)
   uv,e,d=match(sx,s['triangle_uv'][source],tx)
   attr[take]=uv;err[take]=e;dot[take]=d
   if not name.startswith(('gear','wheel','nozzle')):
    groups.append(dict(part=name,triangles=int(take.sum()),p50_m=float(np.median(e)),p95_m=float(np.quantile(e,.95)),within_2cm=int((e<.02).sum())))
   if name in ['fuse','tail','wing_l','rudder0']:print(model,name,groups[-1],flush=True)
  np.savez_compressed(OUT/f'{model}_mapping.npz',source_uv=attr,error=err,normal_dot=dot)
  reports[model]=groups
 (OUT/'mapping_quality.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
if __name__=='__main__':run()
