"""Headless Blender BVH visibility filter. Writes no preview or skin image."""
from pathlib import Path
import argparse,json,hashlib,sys,time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
ap=argparse.ArgumentParser();ap.add_argument('--kit',required=True);ap.add_argument('--out',required=True);ap.add_argument('--models',nargs='+',default=['j_15t','j_16','j_10c']);opt=ap.parse_args(args);out=Path(opt.out);out.mkdir(parents=True,exist_ok=True)
directions=[Vector((x,y,z)).normalized() for x in [-1,0,1] for y in [-1,0,1] for z in [-1,0,1] if x or y or z]
for model in opt.models:
 started=time.time();folder=Path(opt.kit)/'assets'/model/(model+'_c');raw=np.load(folder/'geometry.npz');meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'));p=raw['triangle_xyz'];uv=raw['triangle_uv'];part=raw['triangle_part'];isl=raw['triangle_island'];normal=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);area=np.abs(np.cross(uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]));good=(area>1e-12)&(area<.04)&(np.linalg.norm(normal,axis=1)>1e-12)
 ids=np.flatnonzero(good);q=np.rint(p[ids]*100000).astype(np.int64);order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1);key=np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9);_,inv=np.unique(key,axis=0,return_inverse=True);rank=np.lexsort((-area[ids],inv));_,first=np.unique(inv[rank],return_index=True);ids=np.sort(ids[rank[first]])
 xyz=p[ids];bvh=BVHTree.FromPolygons([Vector(v) for v in xyz.reshape(-1,3)],np.arange(len(ids)*3).reshape(-1,3).tolist(),all_triangles=True,epsilon=0.)
 pn=np.array(meta['part_names'])[part[ids]];cent=xyz.mean(1);excluded=np.array([any(k in str(n).lower() for k in ['cockpit','seat','pilot','interior','instrument','dashboard']) for n in pn]);boxes={'j_15t':(6.2,8.6,.44),'j_16':(4.5,8.6,.48)}
 if model in boxes:
  xlo,xhi,z=boxes[model];excluded|=(cent[:,0]>xlo)&(cent[:,0]<xhi)&(abs(cent[:,2])<z)&(cent[:,1]>.05)
 visible=np.zeros(len(ids),bool);attempts=0
 for i,tid in enumerate(ids):
  if excluded[i]:continue
  v=Vector(cent[i]);n=Vector(normal[tid]).normalized()
  for direction in [n,-n,*directions]:
   hit,_,_,_=bvh.ray_cast(v+direction*60.,-direction,60.001);attempts+=1
   if hit is not None and (hit-v).length<.0002:visible[i]=True;break
  if i%50000==0:print(model,'visibility',i,'/',len(ids),flush=True)
 chosen=ids[visible];payload={k:raw[k][chosen] for k in ['triangle_xyz','triangle_uv','triangle_part','triangle_island']};payload['source_triangle_id']=chosen.astype(np.int32);np.savez_compressed(out/(model+'.npz'),**payload)
 clean={'model':model,'texture':meta['texture'],'reference_resolution':[8192,8192],'native_resolution':meta['authoring_resolution'],'part_names':meta['part_names'],'native_axes':'+X nose, +Y up, +Z left','native_geometry_sha256':hashlib.sha256((folder/'geometry.npz').read_bytes()).hexdigest(),'filter':{'UV_area_range':[1e-12,.04],'XYZ_duplicate_quantum_m':1e-5,'visibility':'centroid ray from +/- normal then 26 global directions, both face windings accepted','ray_hit_tolerance_m':.0002,'interior_exclusions':'part names cockpit/seat/pilot/interior/instrument/dashboard; audited cockpit-opening box on J15T/J16','cockpit_box':boxes.get(model),'original_triangles':len(p),'canonical_triangles':len(ids),'excluded_cockpit_triangles':int(excluded.sum()),'exterior_triangles':len(chosen),'ray_queries':attempts,'runtime_verified':False},'elapsed_seconds':round(time.time()-started,2)};(out/(model+'.json')).write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8');print(model,'DONE',len(chosen),'seconds',clean['elapsed_seconds'],flush=True)
