"""Read-only graph inspection and local UV/pixel transform composition."""
from pathlib import Path
import argparse,json,sqlite3,collections
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--db',type=Path,default=Path(__file__).resolve().parents[1]/'data/seam_links.sqlite3');ap.add_argument('--model',default='j_15t');ap.add_argument('--chart',type=int);ap.add_argument('--to',type=int);ap.add_argument('--connection',type=int);ap.add_argument('--pixel',nargs=2,type=float);ap.add_argument('--contacts-only',action='store_true');a=ap.parse_args();db=sqlite3.connect('file:'+a.db.resolve().as_posix()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
if a.connection:
 out={'connection':dict(db.execute('SELECT * FROM connections WHERE id=?',(a.connection,)).fetchone()),'sides':[dict(x) for x in db.execute('SELECT * FROM sides WHERE connection_id=? ORDER BY side',(a.connection,))],'pixels':[dict(x) for x in db.execute('SELECT * FROM pixels WHERE connection_id=? ORDER BY side,step',(a.connection,))],'transforms':dict(db.execute('SELECT * FROM transforms WHERE connection_id=?',(a.connection,)).fetchone())};print(json.dumps(out,ensure_ascii=False,indent=2))
elif a.chart and a.to:
 adj=collections.defaultdict(list)
 for r in db.execute('SELECT * FROM connections WHERE model=?',(a.model,)):
  if a.contacts_only and r['relation']=='assembly_reference':continue
  adj[r['chart_a']].append((r['chart_b'],r['id'],False,r['needs_review']));adj[r['chart_b']].append((r['chart_a'],r['id'],True,r['needs_review']))
 parent={a.chart:None};todo=[a.chart]
 for cur in todo:
  if cur==a.to:break
  for nxt,cid,reverse,review in adj[cur]:
   if nxt not in parent:parent[nxt]=(cur,cid,reverse,review);todo.append(nxt)
 if a.to not in parent:raise SystemExit('No path in this graph layer; gap/reference bridges may have been excluded.')
 path=[];cur=a.to
 while cur!=a.chart:
  old,cid,reverse,review=parent[cur];path.append((old,cur,cid,reverse,review));cur=old
 path.reverse();matrix=np.eye(3)
 for _,_,cid,reverse,_ in path:
  row=db.execute('SELECT * FROM transforms WHERE connection_id=?',(cid,)).fetchone();key='pixel_b_to_a_json' if reverse else 'pixel_a_to_b_json';matrix=np.array(json.loads(row[key]))@matrix
 out={'path':path,'composed_local_pixel_transform':matrix.tolist(),'needs_review':any(x[4] for x in path),'limit':'Composition follows local chart frames. It is not a global curved-surface warp; reference bridges are not physical seams.'}
 if a.pixel:out['mapped_unwrapped_pixel_index']=(matrix@[*a.pixel,1.]).tolist()[:2]
 print(json.dumps(out,ensure_ascii=False,indent=2))
else:
 rows=db.execute('SELECT * FROM charts WHERE model=?'+(' AND id=?' if a.chart else ''),(a.model,a.chart) if a.chart else (a.model,)).fetchall();print(json.dumps([dict(x) for x in rows],ensure_ascii=False,indent=2))
