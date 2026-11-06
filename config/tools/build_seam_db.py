"""Build a traversable registration tree; virtual 1px stubs are stored only in SQLite."""
from pathlib import Path
import argparse,json,sqlite3,hashlib,itertools,math
import numpy as np
from scipy.spatial import cKDTree
SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE models(id TEXT PRIMARY KEY,width INTEGER,height INTEGER,source_sha256 TEXT,filter_json TEXT);
CREATE TABLE charts(id INTEGER PRIMARY KEY,model TEXT REFERENCES models(id),part_id INTEGER,island_id INTEGER,part_name TEXT,triangles INTEGER,area_px REAL,paintable INTEGER,reason TEXT,root_id INTEGER,parent_id INTEGER);
CREATE TABLE connections(id INTEGER PRIMARY KEY,model TEXT REFERENCES models(id),chart_a INTEGER REFERENCES charts(id),chart_b INTEGER REFERENCES charts(id),relation TEXT,gap_m REAL,shared_edge_length_m REAL,needs_review INTEGER,notes TEXT,UNIQUE(model,chart_a,chart_b));
CREATE TABLE sides(connection_id INTEGER REFERENCES connections(id),side INTEGER CHECK(side IN (0,1)),chart_id INTEGER REFERENCES charts(id),source_triangle INTEGER,anchor_u REAL,anchor_v REAL,anchor_x_index REAL,anchor_y_index REAL,world_x REAL,world_y REAL,world_z REAL,anchor_error_px REAL,triangle_uv_json TEXT,triangle_xyz_json TEXT,PRIMARY KEY(connection_id,side));
CREATE TABLE pixels(connection_id INTEGER,side INTEGER,step INTEGER,x INTEGER,y INTEGER,unwrapped_x INTEGER,unwrapped_y INTEGER,tile_u INTEGER,tile_v INTEGER,world_x REAL,world_y REAL,world_z REAL,PRIMARY KEY(connection_id,side,step),FOREIGN KEY(connection_id,side) REFERENCES sides(connection_id,side));
CREATE TABLE transforms(connection_id INTEGER PRIMARY KEY REFERENCES connections(id),uv_a_to_b_json TEXT,uv_b_to_a_json TEXT,pixel_a_to_b_json TEXT,pixel_b_to_a_json TEXT,condition_number REAL,anchor_residual_px REAL,rule TEXT);
CREATE TABLE uv_aliases(model TEXT,alias_id INTEGER,chart_id INTEGER REFERENCES charts(id),PRIMARY KEY(model,alias_id,chart_id));
CREATE INDEX charts_by_model ON charts(model); CREATE INDEX connection_a ON connections(chart_a); CREATE INDEX connection_b ON connections(chart_b);
'''
class Union:
 def __init__(self,n):self.p=list(range(n));self.rank=[0]*n
 def find(self,x):
  while self.p[x]!=x:self.p[x]=self.p[self.p[x]];x=self.p[x]
  return x
 def join(self,a,b):
  a,b=self.find(a),self.find(b)
  if a==b:return False
  if self.rank[a]<self.rank[b]:a,b=b,a
  self.p[b]=a
  if self.rank[a]==self.rank[b]:self.rank[a]+=1
  return True

def bresenham(a,b):
 x,y=map(int,a);bx,by=map(int,b);dx=abs(bx-x);dy=-abs(by-y);sx=1 if x<bx else -1;sy=1 if y<by else -1;e=dx+dy;out=[]
 while True:
  out.append((x,y))
  if (x,y)==(bx,by):return out
  e2=e*2
  if e2>=dy:e+=dy;x+=sx
  if e2<=dx:e+=dx;y+=sy

def inside_candidates(t,anchor,r=5):
 c=np.rint(anchor).astype(int);yy,xx=np.mgrid[c[1]-r:c[1]+r+1,c[0]-r:c[0]+r+1];q=np.stack([xx.ravel(),yy.ravel(),np.ones(xx.size)],1);mat=np.vstack([t.T,np.ones(3)])
 if abs(np.linalg.det(mat))<1e-12:return None
 bc=q@np.linalg.inv(mat).T;valid=(bc>=-1e-7).all(1)
 if not valid.any():return None
 pts=q[valid,:2];b=bc[valid];j=np.argmin(((pts-anchor)**2).sum(1));return pts[j].astype(int),b[j]

def trace(uv,xyz,bary,w,h,length=6):
 t=uv*[w,-h]+[0,h]-.5;anchor=bary@t;start=inside_candidates(t,anchor)
 if start is None:return None
 a,_=start;center=t.mean(0);direction=center-anchor;norm=np.linalg.norm(direction)
 if norm>1e-9:destination=anchor+direction*min(length/norm,.75)
 else:destination=anchor
 end=inside_candidates(t,destination)
 if end is None:end=start
 points=bresenham(a,end[0])[:7];inv=np.linalg.inv(np.vstack([t.T,np.ones(3)]));valid=[]
 for x,y in points:
  bc=inv@np.array([x,y,1.]);
  if bc.min()<-1e-6:break
  valid.append((int(x),int(y),(bc@xyz).tolist()))
 if not valid:return None
 return {'uv':(bary@uv).tolist(),'xyz':(bary@xyz).tolist(),'index':anchor.tolist(),'error':float(np.linalg.norm(a-anchor)),'pixels':valid}

def registration(ua,pa,ub,pb,aa,ab,w,h):
 def unit(x):return x/max(np.linalg.norm(x),1e-15)
 na=unit(np.cross(pa[1]-pa[0],pa[2]-pa[0]));nb=unit(np.cross(pb[1]-pb[0],pb[2]-pb[0]));common=[]
 for q in pa:
  if np.linalg.norm(pb-q,axis=1).min()<2e-5:common.append(q)
 edge=common[1]-common[0] if len(common)>1 else np.cross(na,nb)
 if np.linalg.norm(edge)<1e-8:
  axes=np.eye(3);edge=max(axes,key=lambda v:min(np.linalg.norm(np.cross(v,na)),np.linalg.norm(np.cross(v,nb))))
 edge=unit(edge)
 def frame(u,p,anchor,normal):
  tangent=unit(edge-normal*(edge@normal));inward=unit(np.cross(normal,tangent))
  if inward@(p.mean(0)-anchor)<0:inward=-inward
  jac=np.linalg.solve(u[1:]-u[0],p[1:]-p[0]);return np.stack([jac@tangent,jac@inward])
 fa=frame(ua,pa,np.array(aa['xyz']),na);fb=frame(ub,pb,np.array(ab['xyz']),nb);fb[1]*=-1
 m=np.eye(3);m[:2,:2]=np.linalg.solve(fb,fa);m[:2,2]=np.array(ab['uv'])-m[:2,:2]@aa['uv'];mi=np.linalg.inv(m);pix=np.array([[w,0,-.5],[0,-h,h-.5],[0,0,1.]])
 pm=pix@m@np.linalg.inv(pix);pmi=np.linalg.inv(pm);a=np.r_[aa['index'],1.];b=np.r_[ab['index'],1.];residual=float(abs(pm@a-b).max());return m,mi,pm,pmi,max(np.linalg.cond(fa),np.linalg.cond(fb)),residual

def build_model(db,folder,model,offset,first_link):
 d=np.load(folder/(model+'.npz'));meta=json.loads((folder/(model+'.json')).read_text());p=d['triangle_xyz'].astype(float);uv=d['triangle_uv'].astype(float);parts=d['triangle_part'];isl=d['triangle_island'];original=d['source_triangle_id'];w,h=meta['reference_resolution'];db.execute('INSERT INTO models VALUES(?,?,?,?,?)',(model,w,h,meta['native_geometry_sha256'],json.dumps(meta['filter'])))
 keys,which=np.unique(np.column_stack([parts,isl]),axis=0,return_inverse=True);n=len(keys);area=abs(np.cross(uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]))*.5*w*h;total=np.bincount(which,weights=area,minlength=n);largest=np.full(n,-1,int)
 for tid in np.argsort(area):largest[which[tid]]=tid
 paintable=[];node_info=[]
 for node,(pid,iid) in enumerate(keys):
  tid=largest[node];supported=total[node]>=.5 and trace(uv[tid],p[tid],np.ones(3)/3,w,h) is not None;paintable.append(supported);node_info.append((offset+node,model,int(pid),int(iid),meta['part_names'][pid],int((which==node).sum()),float(total[node]),int(supported),'' if supported else 'no independently addressable pixel in representative UV triangle',None,None))
 db.executemany('INSERT INTO charts VALUES(?,?,?,?,?,?,?,?,?,?,?)',node_info);paintable=np.array(paintable);active=set(np.flatnonzero(paintable).tolist());uf=Union(n);selected=[];trace_cache={};fallbacks=0
 def add(na,nb,ta,tb,ba,bb,kind,length=0):
  nonlocal fallbacks
  if na==nb or na not in active or nb not in active or uf.find(na)==uf.find(nb):return False
  ra=trace(uv[ta],p[ta],ba,w,h);rb=trace(uv[tb],p[tb],bb,w,h);notes=[]
  if ra is None:
   ta=largest[na];ba=np.ones(3)/3;ra=trace(uv[ta],p[ta],ba,w,h);notes.append('A boundary has subpixel footprint; anchor uses an interior reference pixel')
  if rb is None:
   tb=largest[nb];bb=np.ones(3)/3;rb=trace(uv[tb],p[tb],bb,w,h);notes.append('B boundary has subpixel footprint; anchor uses an interior reference pixel')
  if ra is None or rb is None:return False
  if notes:kind='assembly_reference';fallbacks+=1
  gap=float(np.linalg.norm(np.array(ra['xyz'])-rb['xyz']));review=int(kind=='assembly_reference' or gap>.01 or max(ra['error'],rb['error'])>math.sqrt(2)+1e-5)
  if na>nb:na,nb,ta,tb,ra,rb=nb,na,tb,ta,rb,ra
  uf.join(na,nb);selected.append((na,nb,ta,tb,ra,rb,kind,gap,length,review,'; '.join(notes)));return True
 # Native edge registration, with UV coordinates retained independently on each face.
 _,vertex=np.unique(np.rint(p.reshape(-1,3)/1e-5).astype(np.int64),axis=0,return_inverse=True);vertex=vertex.reshape(-1,3);edges={}
 for tid,v in enumerate(vertex):
  node=int(which[tid])
  if node not in active:continue
  for a,b in [(0,1),(1,2),(2,0)]:edges.setdefault(tuple(sorted((int(v[a]),int(v[b])))),[]).append((node,tid,a,b))
 candidates={};boundary_refs={};vertex_refs={}
 for key,recs in edges.items():
  nodes={r[0] for r in recs}
  for rec in recs:
   node,tid,a,b=rec
   if sum(x[0]==node for x in recs)==1:
    for j in [a,b]:boundary_refs.setdefault((node,int(vertex[tid,j])),(tid,j))
   for j in [a,b]:vertex_refs.setdefault(int(vertex[tid,j]),{})[node]=(tid,j)
  if len(nodes)>1:
   for aa,bb in itertools.combinations(recs,2):
    if aa[0]==bb[0]:continue
    length=float(np.linalg.norm(p[aa[1],aa[2]]-p[aa[1],aa[3]]));pair=tuple(sorted((aa[0],bb[0])))
    if pair not in candidates or length>candidates[pair][0]:candidates[pair]=(length,aa,bb)
 for length,aa,bb in sorted(candidates.values(),key=lambda x:(-x[0],x[1][0],x[2][0])):
  na,ta,a0,a1=aa;nb,tb,b0,b1=bb;ba=np.zeros(3);bbary=np.zeros(3);ba[[a0,a1]]=.5;bbary[[b0,b1]]=.5;add(na,nb,ta,tb,ba,bbary,'shared_edge',length)
 exact_components=len({uf.find(i) for i in active})
 for refs in vertex_refs.values():
  items=list(refs.items())
  if len(items)>1:
   anchor=items[0]
   for other in items[1:]:
    na,(ta,ja)=anchor;nb,(tb,jb)=other;add(na,nb,ta,tb,np.eye(3)[ja],np.eye(3)[jb],'shared_vertex')
 contact_components=len({uf.find(i) for i in active})
 # Boruvka on measured boundary-point distances joins separated subassemblies without pretending they share a seam.
 boundary_nodes={k[0] for k in boundary_refs}
 for node in active:
  if node not in boundary_nodes:
   tid=largest[node]
   for j in range(3):boundary_refs[(node,int(vertex[tid,j]))]=(tid,j)
 refs=list(boundary_refs.items());owners=np.array([k[0] for k,_ in refs]);tids=np.array([v[0] for _,v in refs]);local=np.array([v[1] for _,v in refs]);points=p[tids,local];tree=cKDTree(points);rounds=0
 while len({uf.find(i) for i in active})>1:
  rounds+=1;roots=np.array([uf.find(i) for i in owners]);best={}
  for start in range(0,len(points),4096):
   stop=min(len(points),start+4096);dd,nn=tree.query(points[start:stop],k=min(32,len(points)));ok=roots[nn]!=roots[start:stop,None];available=ok.any(1);rows=np.flatnonzero(available);cols=np.argmax(ok[available],1)
   for rr,cc in zip(rows,cols):
    i=start+int(rr);j=int(nn[rr,cc]);root=int(roots[i]);dist=float(dd[rr,cc])
    if root not in best or dist<best[root][0]:best[root]=(dist,i,j)
  missing={uf.find(i) for i in active}-set(best)
  for root in missing:
   own=np.flatnonzero(roots==root);others=np.flatnonzero(roots!=root)
   if not len(others):continue
   alt=cKDTree(points[others]);dd,nn=alt.query(points[own]);k=int(np.argmin(dd));best[root]=(float(dd[k]),int(own[k]),int(others[nn[k]]))
  progress=0
  for dist,i,j in sorted(best.values()):
   na,nb=int(owners[i]),int(owners[j]);kind='near_gap' if dist<=.01 else 'assembly_reference';progress+=add(na,nb,int(tids[i]),int(tids[j]),np.eye(3)[local[i]],np.eye(3)[local[j]],kind)
  if not progress:raise RuntimeError('Cannot connect paintable exterior charts')
  if rounds>n:raise RuntimeError('Boruvka did not converge')
 # Surface reuse is an explicit constraint, not an inferred independent painting area.
 quant=np.rint(uv*1e6).astype(np.int64);order=np.lexsort((quant[:,:,1],quant[:,:,0]),axis=1);flat=np.take_along_axis(quant,order[:,:,None],axis=1).reshape(-1,6);_,uvid=np.unique(flat,axis=0,return_inverse=True);alias={}
 for tid,k in enumerate(uvid):alias.setdefault(int(k),set()).add(int(which[tid]))
 alias_rows=[];ag=0
 for nodes in alias.values():
  if len(nodes)>1:
   ag+=1
   for node in nodes:alias_rows.append((model,ag,offset+node))
 db.executemany('INSERT INTO uv_aliases VALUES(?,?,?)',alias_rows)
 link_id=first_link;relations={};errors=[];gaps=[]
 for na,nb,ta,tb,ra,rb,kind,gap,length,review,notes in selected:
  db.execute('INSERT INTO connections VALUES(?,?,?,?,?,?,?,?,?)',(link_id,model,offset+na,offset+nb,kind,gap,length,review,notes));relations[kind]=relations.get(kind,0)+1;gaps.append(gap)
  matrices=registration(uv[ta],p[ta],uv[tb],p[tb],ra,rb,w,h)
  db.execute('INSERT INTO transforms VALUES(?,?,?,?,?,?,?,?)',(link_id,*[json.dumps(x.tolist()) for x in matrices[:4]],float(matrices[4]),matrices[5],'local edge-frame unfolding; separate anchors on gaps; never a global nonrigid island warp'))
  for side,node,tid,r in [(0,na,ta,ra),(1,nb,tb,rb)]:
   db.execute('INSERT INTO sides VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(link_id,side,offset+node,int(original[tid]),*r['uv'],*r['index'],*r['xyz'],r['error'],json.dumps(uv[tid].tolist()),json.dumps(p[tid].tolist())));errors.append(r['error'])
   rows=[]
   for step,(x,y,world) in enumerate(r['pixels']):rows.append((link_id,side,step,x%w,y%h,x,y,x//w,y//h,*world))
   db.executemany('INSERT INTO pixels VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',rows)
  link_id+=1
 # Root/parent columns permit traversal without joining all geometric candidates.
 adj={i:[] for i in active}
 for na,nb,*_ in selected:adj[na].append(nb);adj[nb].append(na)
 if active:
  root=min(active);seen={root};todo=[root];db.execute('UPDATE charts SET root_id=?,parent_id=NULL WHERE id=?',(offset+root,offset+root))
  for cur in todo:
   for nxt in adj[cur]:
    if nxt not in seen:seen.add(nxt);todo.append(nxt);db.execute('UPDATE charts SET root_id=?,parent_id=? WHERE id=?',(offset+root,offset+cur,offset+nxt))
  assert len(seen)==len(active);assert len(selected)==len(active)-1
 report={'model':model,'external_triangles':len(p),'charts':n,'paintable_charts':len(active),'subpixel_charts_excluded_from_tree':n-len(active),'connections':len(selected),'tree_connected':True,'tree_acyclic':True,'edge_only_components':exact_components,'physical_contact_components':contact_components,'relations':relations,'uv_alias_groups':ag,'reference_anchor_fallbacks':fallbacks,'max_raster_anchor_error_px':max(errors,default=0),'max_measured_gap_m':max(gaps,default=0),'required_review_links':sum(x[9] for x in selected),'width_px':1,'stub_length_limit_px':6,'image_overlays_written':False,'runtime_verified':False}
 print(json.dumps(report),flush=True);return offset+n,link_id,report

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,default=Path(__file__).resolve().parents[1]/'data/geometry');ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data/seam_links.sqlite3');ap.add_argument('--models',nargs='+',default=['j_15t','j_16','j_10c']);args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True);tmp=args.output.with_suffix('.building.sqlite3')
 if tmp.exists():tmp.unlink()
 db=sqlite3.connect(tmp);db.executescript(SCHEMA);db.executemany('INSERT INTO meta VALUES(?,?)',[('schema_version','1'),('pixel_convention','x=u*W-.5, y=(1-v)*H-.5 are continuous sample indices; integer pixels have centers at these indices'),('stub_width_px','1'),('graph_policy','One spanning tree per model; short per-connection stubs do not need to meet other stubs on the same chart'),('not_a_claim','Assembly references carry separate measured XYZ anchors and are not shared physical seams; visibility is a static diagnostic only')]);offset=1;link=1;reports=[]
 for model in args.models:offset,link,r=build_model(db,args.inputs,model,offset,link);reports.append(r);db.commit()
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';assert not db.execute('PRAGMA foreign_key_check').fetchall();db.close();tmp.replace(args.output);report=args.output.parent/'reports/seam_graph_validation.json';report.parent.mkdir(exist_ok=True);report.write_text(json.dumps({'models':reports,'database_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
