"""Independent read-only checks for graph, digital stubs and numeric registration."""
from pathlib import Path
import argparse,json,sqlite3,collections,math
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--db',type=Path,default=Path(__file__).resolve().parents[1]/'data/seam_links.sqlite3');ap.add_argument('--report',type=Path);a=ap.parse_args();db=sqlite3.connect('file:'+a.db.resolve().as_posix()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row;assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert not db.execute('PRAGMA foreign_key_check').fetchall();models=[];max_roundtrip=0.;max_anchor=0.;checked_pixels=0
for m in db.execute('SELECT * FROM models'):
 ids={x[0] for x in db.execute('SELECT id FROM charts WHERE model=? AND paintable=1',(m['id'],))};links=db.execute('SELECT * FROM connections WHERE model=?',(m['id'],)).fetchall();assert len(links)==len(ids)-1;adj=collections.defaultdict(list)
 for r in links:adj[r['chart_a']].append(r['chart_b']);adj[r['chart_b']].append(r['chart_a'])
 visited=set();todo=[min(ids)]
 while todo:
  q=todo.pop()
  if q in visited:continue
  visited.add(q);todo.extend(adj[q])
 assert visited==ids
 for r in links:
  sides=db.execute('SELECT * FROM sides WHERE connection_id=? ORDER BY side',(r['id'],)).fetchall();assert len(sides)==2
  for side in sides:
   pixels=db.execute('SELECT * FROM pixels WHERE connection_id=? AND side=? ORDER BY step',(r['id'],side['side'])).fetchall();assert 1<=len(pixels)<=7;uv=np.array(json.loads(side['triangle_uv_json']));xyz=np.array(json.loads(side['triangle_xyz_json']));t=uv*[m['width'],-m['height']]+[0,m['height']]-.5;mat=np.vstack([t.T,np.ones(3)])
   anchor=np.array([side['anchor_u'],side['anchor_v']])*[m['width'],-m['height']]+[0,m['height']]-.5;assert np.max(abs(anchor-[side['anchor_x_index'],side['anchor_y_index']]))<1e-8
   for i,p in enumerate(pixels):
    assert p['x']==p['unwrapped_x']%m['width'];assert p['y']==p['unwrapped_y']%m['height'];bc=np.linalg.solve(mat,[p['unwrapped_x'],p['unwrapped_y'],1]);assert bc.min()>=-1e-5;assert np.max(abs(bc@xyz-[p['world_x'],p['world_y'],p['world_z']]))<1e-6
    if i:
     old=pixels[i-1];assert max(abs(p['unwrapped_x']-old['unwrapped_x']),abs(p['unwrapped_y']-old['unwrapped_y']))==1
    checked_pixels+=1
  tr=db.execute('SELECT * FROM transforms WHERE connection_id=?',(r['id'],)).fetchone();f=np.array(json.loads(tr['pixel_a_to_b_json']));b=np.array(json.loads(tr['pixel_b_to_a_json']));points=np.array([[0,0,1],[.5,.5,1],[4000,3000,1],[8191,8191,1]],float).T;err=float(abs(b@f@points-points).max());max_roundtrip=max(max_roundtrip,err);assert err<1e-4
  x=np.array([sides[0]['anchor_x_index'],sides[0]['anchor_y_index'],1]);y=np.array([sides[1]['anchor_x_index'],sides[1]['anchor_y_index'],1]);err=float(abs(f@x-y).max());max_anchor=max(max_anchor,err);assert err<1e-4
  gap=np.linalg.norm(np.array([sides[0]['world_x'],sides[0]['world_y'],sides[0]['world_z']])-np.array([sides[1]['world_x'],sides[1]['world_y'],sides[1]['world_z']]));assert abs(gap-r['gap_m'])<1e-9
  if r['relation']=='shared_edge':assert gap<2e-5
 models.append({'model':m['id'],'paintable_charts':len(ids),'links':len(links),'connected':True,'acyclic':True})
report={'models':models,'checked_stub_pixels':checked_pixels,'max_local_transform_roundtrip_error_px':max_roundtrip,'max_continuous_anchor_registration_error_px':max_anchor,'stub_width_px':1,'stub_max_grid_steps':6,'raster_topology':'8-connected, independently local to each connection','all_checks_passed':True,'images_modified':False,'runtime_verified':False};print(json.dumps(report,ensure_ascii=False,indent=2))
if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
