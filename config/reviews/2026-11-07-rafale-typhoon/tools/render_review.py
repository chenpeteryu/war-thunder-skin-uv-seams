"""Blender: complete opaque color-block review and static body visibility inputs."""
from pathlib import Path
import sys,argparse,json,hashlib,time
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);R=a.root.resolve();OUT=R/'renders';OUT.mkdir(exist_ok=True);EX=R/'exterior';EX.mkdir(exist_ok=True)
def vec(v):return Vector((v[0],v[2],v[1]))
views=[('top',(0,32,0)),('bottom',(0,-32,0)),('left',(0,0,32)),('right',(0,0,-32)),('front',(32,0,0)),('back',(-32,0,0))]+[(f'oblique_{x}_{y}_{z}',(x*24,y*20,z*24)) for x in [-1,1] for y in [-1,1] for z in [-1,1]]
directions=[Vector((x,y,z)).normalized() for x in [-1,0,1] for y in [-1,0,1] for z in [-1,0,1] if x or y or z]
for path in sorted((R/'scenes').glob('*.npz')):
 model=path.stem;started=time.time();g=np.load(path);meta=json.loads(path.with_suffix('.json').read_text());bodyfolder=R/'library/assets'/model/(model+'_c');body=np.load(bodyfolder/'geometry.npz');bm=json.loads((bodyfolder/'metadata.json').read_text());opaque=[m['id'] for m in meta['materials'] if m['shader']=='dynamic_masked_chrome_bump']
 # Core blocking scene: retain all opaque body/interior materials, excluding
 # name-identified optional attachments. Not engine activation reconstruction.
 optional=[m['id'] for m in meta['materials'] if any(s in (m['slots'][0] or '').lower() for s in ['pylon','pod','launcher','adapter','drop_tank','fuel_tank','missile','bomb'])]
 optional_parts=[i for i,x in enumerate(meta['parts']) if x['name'].lower().startswith(('pylon','pod','chute','flare','jet_flame')) or '_pod' in x['name'].lower()]
 active=np.isin(g['triangle_material'],opaque)&~np.isin(g['triangle_material'],optional)&~np.isin(g['triangle_part'],optional_parts);block=g['triangle_xyz'][active]
 bvh=BVHTree.FromPolygons([Vector(v) for v in block.reshape(-1,3)],np.arange(len(block)*3).reshape(-1,3).tolist(),all_triangles=True)
 xyz=body['triangle_xyz'];uv=body['triangle_uv'];normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);area=abs(np.cross(uv[:,1]-uv[:,0],uv[:,2]-uv[:,0]));good=(area>1e-12)&(np.linalg.norm(normals,axis=1)>1e-12);names=np.array(bm['part_names'])[body['triangle_part']];exclude=np.array([any(s in str(n).lower() for s in ['cockpit','seat','pilot','instrument','dashboard']) for n in names]);good&=~exclude
 visible=np.zeros(len(xyz),bool)
 for tid in np.flatnonzero(good):
  center=Vector(xyz[tid].mean(0));normal=Vector(normals[tid]).normalized()
  for direction in [normal,-normal,*directions]:
   hit,_,_,_=bvh.ray_cast(center+direction*60,-direction,60.001)
   if hit is not None and (hit-center).length<.0002:visible[tid]=True;break
 ids=np.flatnonzero(visible);np.savez_compressed(EX/(model+'.npz'),**{k:body[k][ids] for k in ['triangle_xyz','triangle_uv','triangle_part','triangle_island']},source_triangle_id=ids.astype(np.int32))
 info={'model':model,'texture':model+'_c','part_names':bm['part_names'],'reference_resolution':bm['authoring_resolution'],'native_geometry_sha256':bm['geometry_sha256'],'filter':{'scope':'static core-body centroid visibility against all selected opaque materials','source_triangles':len(xyz),'blocker_triangles':len(block),'visible_triangles':len(ids),'degenerate_or_named_interior_exclusions':int((~good).sum()),'occluded_triangles':int((good&~visible).sum()),'ray_tolerance_m':.0002,'directions':'both face normals plus 26 global directions','optional_material_ids':optional,'optional_part_ids':optional_parts,'glass_null_effects_excluded':True,'per_texel_alpha_simulated':False,'runtime_verified':False}}
 (EX/(model+'.json')).write_text(json.dumps(info,indent=2),encoding='utf8');del bvh
 print('VISIBILITY_COMPLETE',model,len(ids),'/',len(xyz),'seconds',round(time.time()-started,1),flush=True)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.outliner.orphans_purge(do_recursive=True)
 size=2048;iy,ix=np.mgrid[:size,:size];cellx=ix*32//size;celly=iy*32//size;rgb=np.stack([(cellx%4)/3,(celly%4)/3,((cellx+celly)%2)*.7+.15],-1);rgba=np.concatenate([rgb,np.ones((size,size,1))],-1).astype(np.float32)
 image=bpy.data.images.new('independent UV blocks',width=size,height=size);image.pixels.foreach_set(rgba.ravel());image.filepath_raw=str(OUT/(model+'_grid.png'));image.file_format='PNG';image.save()
 shown=[];omitted=[]
 for material in meta['materials']:
  mid=material['id'];select=g['triangle_material']==mid
  if not select.any():continue
  if material['shader']!='dynamic_masked_chrome_bump':omitted.append({'id':mid,'shader':material['shader'],'triangles':int(select.sum())});continue
  tex=(material['slots'][0] or '').split('*')[0];q=g['triangle_xyz'][select][:,[0,2,1]][:,:,[0,2,1]];u=g['triangle_uv'][select][:,[0,2,1]]
  mesh=bpy.data.meshes.new(str(mid));mesh.from_pydata(q.reshape(-1,3).tolist(),[],np.arange(q.size//3).reshape(-1,3).tolist());mesh.update();layer=mesh.uv_layers.new();layer.data.foreach_set('uv',u.reshape(-1).tolist());obj=bpy.data.objects.new(str(mid),mesh);bpy.context.collection.objects.link(obj)
  mat=bpy.data.materials.new(tex);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();em=n.new('ShaderNodeEmission');output=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(em.outputs[0],output.inputs[0]);pattern=tex==model+'_c'
  if pattern:
   t=n.new('ShaderNodeTexImage');t.image=image;t.interpolation='Closest';t.extension='REPEAT';mat.node_tree.links.new(t.outputs['Color'],em.inputs['Color'])
  else:em.inputs['Color'].default_value=(.24,.27,.30,1)
  mesh.materials.append(mat);shown.append({'id':mid,'texture':tex,'triangles':int(select.sum()),'color_blocks':pattern})
 scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1100;scene.render.resolution_y=825;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1;scene.world.color=(.06,.06,.06)
 if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=16
 camd=bpy.data.cameras.new('fixed review');cam=bpy.data.objects.new('fixed review',camd);bpy.context.collection.objects.link(cam);scene.camera=cam;camd.type='ORTHO';camd.ortho_scale=24;camd.clip_end=1000
 record={'model':model,'scene_sha256':meta['geometry_sha256'],'body_geometry_sha256':bm['geometry_sha256'],'materials':shown,'excluded_materials':omitted,'static_visibility':info['filter'],'views':[],'limitations':'2K synthetic grid on main texture; attachments shown neutral. Static opaque model, glass/effects omitted, no per-texel alpha, animation, engine material or universal pixel-precision claim.'}
 for name,eye in views:
  cam.location=vec(eye);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();scene.render.filepath=str(OUT/(model+'_'+name+'.png'));bpy.ops.render.render(write_still=True);record['views'].append({'view':name,'native_eye':eye,'native_target':[0,0,0],'scale':24,'matrix_world':[list(row) for row in cam.matrix_world]})
 (OUT/(model+'.json')).write_text(json.dumps(record,indent=2),encoding='utf8');print('RENDER_COMPLETE',model,flush=True)
