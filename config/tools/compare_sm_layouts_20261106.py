from pathlib import Path
import numpy as np,json,hashlib,sys
R=Path.cwd();assets=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[2]/'aircraft';A=assets/'su30sm';B=assets/'su30sm2'
namesa={p.name for p in A.iterdir() if p.is_dir()};namesb={p.name for p in B.iterdir() if p.is_dir()};rows=[]
for name in sorted(namesa&namesb):
 a=np.load(A/name/'geometry.npz');b=np.load(B/name/'geometry.npz');ma=json.loads((A/name/'metadata.json').read_text());mb=json.loads((B/name/'metadata.json').read_text());rows.append({'texture':name,'triangles_sm':len(a['triangle_uv']),'triangles_sm2':len(b['triangle_uv']),'uv_array_equal':np.array_equal(a['triangle_uv'],b['triangle_uv']),'xyz_array_equal':np.array_equal(a['triangle_xyz'],b['triangle_xyz']),'boundary_uv_equal':np.array_equal(a['boundary_uv'],b['boundary_uv']),'dimensions_sm':ma['authoring_resolution'],'dimensions_sm2':mb['authoring_resolution']})
a=np.load(A/'su_30sm_c/geometry.npz');b=np.load(B/'su_30sm2_c/geometry.npz');ma=json.loads((A/'su_30sm_c/metadata.json').read_text());mb=json.loads((B/'su_30sm2_c/metadata.json').read_text())
def triangle_keys(g,m):
 u=np.rint(g['triangle_uv']*1e6).astype(np.int64);names=np.array(m['part_names'])[g['triangle_part']];result={}
 for name in np.unique(names):
  q=u[names==name];order=np.lexsort((q[:,:,1],q[:,:,0]),axis=1);q=np.take_along_axis(q,order[:,:,None],axis=1);result[str(name)]={tuple(x.ravel()) for x in q}
 return result
ka=triangle_keys(a,ma);kb=triangle_keys(b,mb);parts=[]
for row in rows:
 name=row['texture'];ga=np.load(A/name/'geometry.npz');gb=np.load(B/name/'geometry.npz');am=json.loads((A/name/'metadata.json').read_text());bm=json.loads((B/name/'metadata.json').read_text());ca=triangle_keys(ga,am);cb=triangle_keys(gb,bm);row['same_uv_triangle_sets_by_part']=ca==cb
for name in sorted(set(ka)|set(kb)):
 x=ka.get(name,set());y=kb.get(name,set());parts.append({'part':name,'unique_uv_triangles_sm':len(x),'unique_uv_triangles_sm2':len(y),'common_uv_triangles':len(x&y),'only_sm':len(x-y),'only_sm2':len(y-x),'same_uv_triangle_set':x==y})
report={'scope':'Current native LOD0 UV layouts; comparing UV triangle sets by part does not prove corresponding physical geometry or whole-skin interchangeability.','common_texture_files':rows,'textures_only_sm':sorted(namesa-namesb),'textures_only_sm2':sorted(namesb-namesa),'main_atlas':{'sm_texture':'su_30sm_c','sm2_texture':'su_30sm2_c','triangles_sm':len(a['triangle_uv']),'triangles_sm2':len(b['triangle_uv']),'parts':parts}}
(R/'sm_sm2_layout_comparison.json').write_text(json.dumps(report,indent=2));print('COMMON_TEXTURES',len(rows),'exact UV',sum(r['uv_array_equal'] for r in rows));print('COMMON_DIFFERENCES',[(r['texture'],r['uv_array_equal'],r['xyz_array_equal']) for r in rows if not r['uv_array_equal'] or not r['xyz_array_equal']]);print('ONLY_SM',report['textures_only_sm']);print('ONLY_SM2',report['textures_only_sm2']);print('MAIN',len(a['triangle_uv']),len(b['triangle_uv']),'parts',len(parts),'same',sum(p['same_uv_triangle_set'] for p in parts));print('DIFFERENT_PARTS',[(p['part'],p['only_sm'],p['only_sm2']) for p in parts if not p['same_uv_triangle_set']][:25])
