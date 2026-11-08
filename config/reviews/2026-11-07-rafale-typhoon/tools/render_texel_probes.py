"""Render isolated source triangles with uniquely colored texels, never seam-line overlays."""
from pathlib import Path
import json,sqlite3,bpy,numpy as np
import sys
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else Path(__file__).resolve().parent;OUT=R/'texel_probes';OUT.mkdir(exist_ok=True)
interior='--interior' in sys.argv
if interior:OUT=R/'texel_probes_interior';OUT.mkdir(exist_ok=True)
transparent='--transparent' in sys.argv
if transparent:OUT=R/'texel_probes_alpha';OUT.mkdir(exist_ok=True)
body_only='--j10-body' in sys.argv
if body_only:OUT=R/'texel_probes_j10_body';OUT.mkdir(exist_ok=True)
nozzle_only='--j10-nozzle' in sys.argv
if nozzle_only:OUT=R/'texel_probes_j10_nozzle';OUT.mkdir(exist_ok=True)
BASE=R/'seam_links.sqlite3'
def native(a):return np.asarray(a)[:,[0,2,1]]
def code(x,y):return np.array([((x*17+y*3)%211+20)/255,((y*23+x*5)%211+20)/255,((x*7+y*13)%211+20)/255])
records=[];missing=[]
for model in ['rafale_c_f3','rafale_m_f3_r','ef_2000_block_10','ef_2000_aesa','f_2000a','f_2000a_aesa','typhoon_fgr4','typhoon_aesa']:
 if body_only and model!='j_10c':continue
 if nozzle_only and model!='j_10c':continue
 dbpath=BASE
 if nozzle_only:dbpath=R/'auxiliary_seams/j_10c__j_10c_nozzle_c/seam_links.sqlite3'
 db=sqlite3.connect('file:'+dbpath.as_posix()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
 m=db.execute('select * from models where id=?',(model,)).fetchone();w,h=m['width'],m['height'];used=set()
 for group,tokens in [('wing',['wing']),('control',['rudder','elevator']),('body',['fuselage','body','tail']),('nozzle',['nozzle'])]:
  if body_only and group!='body':continue
  if nozzle_only and group!='nozzle':continue
  if group=='body':tokens.append('fuse')
  choices=db.execute("select c.*,a.part_name as pa,b.part_name as pb from connections c join charts a on a.id=c.chart_a join charts b on b.id=c.chart_b where c.model=? and c.relation='shared_edge' and c.needs_review=0 order by c.shared_edge_length_m desc",(model,)).fetchall()
  connection=next((c for c in choices if c['id'] not in used and any(k in c['pa'] or k in c['pb'] for k in tokens)),None)
  if connection is None:missing.append({'model':model,'group':group,'reason':'no qualifying shared-edge connection in this primary-texture tree'});continue
  used.add(connection['id'])
  for s in db.execute('select * from sides where connection_id=? order by side',(connection['id'],)):
   uv=np.array(json.loads(s['triangle_uv_json']));xyz=native(json.loads(s['triangle_xyz_json']));pixels=db.execute('select * from pixels where connection_id=? and side=? order by step desc',(connection['id'],s['side'])).fetchall();pix=pixels[0];x,y=pix['unwrapped_x'],pix['unwrapped_y'];target=Vector((pix['world_x'],pix['world_z'],pix['world_y']))
   sample_rule='stored short-stub pixel';bary_margin=None
   if interior:
    t=uv*[w,-h]+[0,h]-.5;cent=np.rint(t.mean(0)).astype(int);dy,dx=np.mgrid[-5:6,-5:6];q=np.stack([cent[0]+dx.ravel(),cent[1]+dy.ravel(),np.ones(dx.size)],1);bc=np.linalg.solve(np.vstack([t.T,np.ones(3)]),q.T).T;best=int(np.argmax(bc.min(1)));bary_margin=float(bc[best].min())
    if bary_margin<=1e-4:missing.append({'model':model,'group':group,'side':s['side'],'reason':'source triangle has no strictly interior integer pixel near centroid'});continue
    x,y=map(int,q[best,:2]);target=Vector(bc[best]@xyz);sample_rule='independent integer texel centre strictly inside source triangle; does not replace short stub'
   jac=np.linalg.solve((uv[1:]-uv[0])*[w,-h],xyz[1:]-xyz[0]);length=np.linalg.svd(jac,compute_uv=False);scale=max(float(length.min())*50,1e-6)
   bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.outliner.orphans_purge(do_recursive=True)
   mesh=bpy.data.meshes.new('source triangle');mesh.from_pydata(xyz.tolist(),[],[(0,1,2)]);mesh.update();layer=mesh.uv_layers.new();layer.data.foreach_set('uv',uv.astype(np.float32).ravel().tolist());obj=bpy.data.objects.new('isolated triangle',mesh);bpy.context.collection.objects.link(obj)
   size=64;xorigin=x-32;yorigin=y-32;iy,ix=np.mgrid[:size,:size];xx=xorigin+ix;yy=yorigin+size-1-iy;rgb=np.stack([((xx*17+yy*3)%211+20)/255,((yy*23+xx*5)%211+20)/255,((xx*7+yy*13)%211+20)/255],-1);rgba=np.concatenate([rgb,np.ones((size,size,1))],-1).astype(np.float32)
   image=bpy.data.images.new('unique texels',width=size,height=size);image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel())
   mat=bpy.data.materials.new('texel encoding');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();tc=n.new('ShaderNodeTexCoord');mult=n.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=(w/size,h/size,1);add=n.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(-xorigin/size,-(h-yorigin-size)/size,0);tex=n.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Closest';tex.extension='EXTEND';em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');links=mat.node_tree.links
   for a,b in [(tc.outputs['UV'],mult.inputs[0]),(mult.outputs[0],add.inputs[0]),(add.outputs[0],tex.inputs['Vector']),(tex.outputs['Color'],em.inputs['Color']),(em.outputs[0],out.inputs[0])]:links.new(a,b)
   mesh.materials.append(mat);normal=Vector(np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]));normal.normalize();cd=bpy.data.cameras.new('probe');camera=bpy.data.objects.new('probe',cd);bpy.context.collection.objects.link(camera);camera.location=target+normal*max(scale*10,.01);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=scale;cd.clip_start=1e-7;cd.clip_end=1000
   scene=bpy.context.scene;scene.camera=camera;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=513;scene.render.resolution_y=513;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1;bpy.context.view_layer.update()
   scene.render.film_transparent=transparent;scene.render.image_settings.color_mode='RGBA'
   filename=f'{model}_{group}_{connection["id"]}_{s["side"]}.png';scene.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True);projection=world_to_camera_view(scene,camera,target);linear=code(x,y);srgb=np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055)*255
   records.append({'model':model,'group':group,'connection':connection['id'],'side':s['side'],'source_triangle':s['source_triangle'],'integer_pixel':[x,y],'resolution':[w,h],'sample_image_pixel':[int(projection.x*513),int((1-projection.y)*513)],'expected_srgb':srgb.tolist(),'image':filename,'sample_rule':sample_rule,'barycentric_margin':bary_margin,'triangle_part':connection['pa'] if s['side']==0 else connection['pb'],'scope':'isolated triangle texture-coordinate probe; does not establish seam continuity, visibility or parser correctness by itself'})
  print('PROBED',model,group,flush=True)
 db.close()
(OUT/'manifest.json').write_text(json.dumps({'probes':records,'missing_groups':missing,'line_overlays':False},indent=2),encoding='utf-8')
