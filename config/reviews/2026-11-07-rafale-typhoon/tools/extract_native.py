"""Extract native LOD0 layouts through the existing UV kit, without editing it."""
from pathlib import Path
import argparse,sys,json,gc,hashlib,traceback
import numpy as np

p=argparse.ArgumentParser();p.add_argument('--kit-tools',type=Path,required=True);p.add_argument('--game',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.kit_tools))
import extract_uv as ex
ex.KIT=a.out/'library';ex.KIT.mkdir(parents=True,exist_ok=True);ex.GAME=a.game
lib=ex.AssetLibrary(a.game,a.out/'cache');lib.build_index(lambda s:None);ex.backend_log.setMuted(True)
models=['rafale_c_f3','rafale_m_f3_r','ef_2000_block_10','ef_2000_aesa','f_2000a','f_2000a_aesa','typhoon_fgr4','typhoon_aesa']
summary=[];failures=[];sources={};dims=ex.dimensions()
(a.out/'scenes').mkdir(exist_ok=True)
for model in models:
 try:
  ref=ex.AssetRef(*next(h for h in lib.name_index[model] if h[2] in ex.MODEL_CLASS_IDS));mdl=lib._open_model(ref,lambda s:None)
  groups,names=ex.parts_for_model(mdl)
  # Use float64 before the inherited 1e-6 quantization, matching stored
  # boundary endpoints and avoiding half-step changes in float32 arithmetic.
  for texture,chunks in sorted(groups.items()):
   chunks=[(pid,uv.astype(np.float64),xyz) for pid,uv,xyz in chunks]
   row=ex.export_texture(model,texture,chunks,names,dims.get(texture),ref);row['game_root']=str(a.game);summary.append(row)
  materials=[{'id':i,'shader':m.cls,'slots':m.getTextureSlots(),'params':m.getParams()} for i,m in enumerate(mdl.materials or [])]
  us=[];xs=[];ps=[];ms=[];parts=[];missing=[]
  for pid,obj in enumerate(mdl):
   parts.append({'name':obj.name,'skinned':obj.skinned});faces=obj.faces
   if not faces:continue
   starts=sorted(s for s in set(obj.materials)|set(obj.material_ids) if 0<=s<len(faces));node=mdl.skeleton.getNodeByName(obj.name) if mdl.skeleton and not obj.skinned else None
   for j,start in enumerate(starts):
    end=starts[j+1] if j+1<len(starts) else len(faces);mid=obj.material_ids.get(start)
    if mid is None:missing.append({'part':obj.name,'start':start,'end':end});continue
    f=np.asarray(faces[start:end],dtype=int).reshape(-1,3);ids,inv=np.unique(f,return_inverse=True)
    uv=np.asarray([mdl.getUV(int(i))[:2] for i in ids],np.float32)[inv.reshape(f.shape)]
    xyz=np.asarray([mdl.getVertex(int(i),parentBone=node)[:3] for i in ids],np.float32)[inv.reshape(f.shape)]
    us.append(uv);xs.append(xyz);ps.append(np.full(len(f),pid,np.int32));ms.append(np.full(len(f),mid,np.int32))
  scene=a.out/'scenes'/(model+'.npz');np.savez_compressed(scene,triangle_uv=np.concatenate(us),triangle_xyz=np.concatenate(xs),triangle_part=np.concatenate(ps),triangle_material=np.concatenate(ms))
  metadata={'model':model,'game_root':str(a.game),'parts':parts,'materials':materials,'triangles':sum(len(x) for x in xs),'missing_material_ranges':missing,'geometry_sha256':hashlib.sha256(scene.read_bytes()).hexdigest(),'source_asset':ref.name,'source_pack':ref.grp,'scope':'all LOD0 material draw ranges; no animation; opaque diagnostic will explicitly omit glass/null/effect shaders'}
  scene.with_suffix('.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
  entry=next(x for x in lib.grp_entries[ref.grp] if x['name']==model and x['class_id']==ref.class_id) if hasattr(ref,'class_id') else next(x for x in lib.grp_entries[ref.grp] if x['name']==model)
  with (a.game/ref.grp).open('rb') as stream:stream.seek(entry['offset']);blob=stream.read(entry['size'])
  sources[model]={'resource_pack':ref.grp,'entry':entry,'raw_entry_sha256':hashlib.sha256(blob).hexdigest(),'skinned_parts':[o.name for o in mdl if o.skinned]}
  print('EXTRACTED',model,len(groups),'textures',metadata['triangles'],'scene triangles',flush=True)
  del mdl,groups,us,xs,ps,ms;gc.collect()
 except Exception as error:
  failures.append({'model':model,'error':repr(error),'traceback':traceback.format_exc()});print('FAILED',model,repr(error),flush=True)
 (ex.KIT/'catalog.json').write_text(json.dumps({'textures':summary,'failures':failures},indent=2),encoding='utf8')
 (a.out/'native_source_evidence.json').write_text(json.dumps(sources,indent=2),encoding='utf8')
assert not failures,failures
