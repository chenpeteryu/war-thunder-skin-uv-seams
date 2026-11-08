"""Compare UV sets and paired UV/XYZ by native part; no artwork comparison."""
from pathlib import Path
import argparse,json,hashlib,itertools
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--library',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
installed=(a.library/'config/catalog.json').is_file()
entries=json.loads((a.library/('config/catalog.json' if installed else 'catalog.json')).read_text(encoding='utf8'))['textures']
if installed:entries=[x for x in entries if x.get('review_batch')=='2026-11-07-rafale-typhoon']
models={x['model'] for x in entries};records={}
def digest_rows(rows):
 unique=np.unique(rows,axis=0)
 return {'unique_triangles':len(unique),'sha256':hashlib.sha256(unique.tobytes()).hexdigest()}
for entry in entries:
 folder=a.library/entry['path'];meta=json.loads((folder/'metadata.json').read_text());g=np.load(folder/'geometry.npz');uv=np.rint(g['triangle_uv'].astype(float)*1e6).astype('<i8');xyz=np.rint(g['triangle_xyz'].astype(float)*1e6).astype('<i8');parts={}
 for pid in np.unique(g['triangle_part']):
  choose=g['triangle_part']==pid;u=uv[choose];x=xyz[choose];order=np.lexsort((u[:,:,1],u[:,:,0]),axis=1);uk=np.take_along_axis(u,order[:,:,None],axis=1).reshape(-1,6)
  joint=np.concatenate([u,x],axis=2);order=np.lexsort(tuple(joint[:,:,i] for i in range(4,-1,-1)),axis=1);jk=np.take_along_axis(joint,order[:,:,None],axis=1).reshape(-1,15)
  parts[meta['part_names'][int(pid)]]={'uv':digest_rows(uk),'uv_xyz':digest_rows(jk),'raw_triangles':int(choose.sum())}
 records.setdefault(entry['model'],{})[entry['texture']]={'triangles':len(uv),'parts':parts,'resolution':meta['authoring_resolution'],'native_resolution':meta.get('native_texture_header_resolution'),'geometry_sha256':meta['geometry_sha256']}
 print('SIGNATURE',entry['model'],entry['texture'],flush=True)
comparisons=[]
for family,names in [('rafale',sorted(x for x in models if x.startswith('rafale'))),('eurofighter',sorted(x for x in models if not x.startswith('rafale')))]:
 for left,right in itertools.combinations(names,2):
  la=records[left][left+'_c'];ra=records[right][right+'_c'];lp=la['parts'];rp=ra['parts'];different_uv=[n for n in sorted(set(lp)|set(rp)) if lp.get(n,{}).get('uv')!=rp.get(n,{}).get('uv')];different_xyz=[n for n in sorted(set(lp)|set(rp)) if lp.get(n,{}).get('uv_xyz')!=rp.get(n,{}).get('uv_xyz')];different_count=[n for n in sorted(set(lp)|set(rp)) if lp.get(n,{}).get('raw_triangles')!=rp.get(n,{}).get('raw_triangles')]
  common=set(records[left])&set(records[right]);aux=[]
  for texture in sorted(common):
   x=records[left][texture];y=records[right][texture];aux.append({'texture':texture,'same_uv_by_part':{k:v['uv'] for k,v in x['parts'].items()}=={k:v['uv'] for k,v in y['parts'].items()},'same_uv_xyz_by_part':x['parts']==y['parts'],'same_resolution':x['resolution']==y['resolution']})
  row={'family':family,'left':left,'right':right,'main_triangles':[la['triangles'],ra['triangles']],'main_part_count':len(set(lp)|set(rp)),'same_uv_parts':len(set(lp)|set(rp))-len(different_uv),'different_uv_parts':different_uv,'different_uv_xyz_parts':different_xyz,'different_triangle_count_parts':different_count,'same_main_resolution':la['resolution']==ra['resolution'],'common_auxiliary_textures':aux,'left_only_textures':sorted(set(records[left])-set(records[right])),'right_only_textures':sorted(set(records[right])-set(records[left])),'main_geometry_merge_eligible':not different_uv and not different_xyz and not different_count and la['resolution']==ra['resolution']}
  comparisons.append(row);print('COMPARISON',left,right,'UV differences',different_uv,'XYZ differences',different_xyz,'merge',row['main_geometry_merge_eligible'],flush=True)
report={'quantization_uv':1e-6,'quantization_xyz_m':1e-6,'method':'Canonical triangle vertex order, unique UV and paired UV/XYZ sets per exact native part name; raw triangle multiplicity compared separately. Equal UV alone does not merge distinct physical geometry or texture bindings.','textures':records,'comparisons':comparisons}
a.output.write_text(json.dumps(report,indent=2),encoding='utf8')
