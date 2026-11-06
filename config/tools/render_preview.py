"""Blender orthographic emission preview. All user coordinates are native XYZ."""
import argparse, sys, json, hashlib
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument('--geometry', type=Path, required=True)
p.add_argument('--texture', type=Path)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--eye', nargs=3, type=float, required=True)
p.add_argument('--target', nargs=3, type=float, default=[0, 0, 0])
p.add_argument('--scale', type=float, required=True)
p.add_argument('--width', type=int, default=1600)
p.add_argument('--height', type=int, default=1000)
a = p.parse_args(args)
assert a.scale > 0 and a.width > 0 and a.height > 0
def native(v): return Vector((v[0], v[2], v[1]))
assert (native(a.eye)-native(a.target)).length > 1e-6
g = np.load(a.geometry)
xyz = g['triangle_xyz'][:, [0, 2, 1], :][:, :, [0, 2, 1]]
uv = g['triangle_uv'][:, [0, 2, 1], :]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
mesh = bpy.data.meshes.new('diagnostic_exterior')
mesh.from_pydata(xyz.reshape(-1, 3).tolist(), [], np.arange(xyz.size//3).reshape(-1, 3).tolist())
mesh.update()
layer = mesh.uv_layers.new(name='UVMap')
layer.data.foreach_set('uv', uv.reshape(-1).tolist())
obj = bpy.data.objects.new('diagnostic_exterior', mesh)
bpy.context.collection.objects.link(obj)
mat = bpy.data.materials.new('color_diagnostic')
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
em = nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (.45, .45, .45, 1)
mat.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
if a.texture:
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(a.texture.resolve()))
    tex.interpolation = 'Closest'
    tex.extension = 'REPEAT'
    mat.node_tree.links.new(tex.outputs['Color'], em.inputs['Color'])
obj.data.materials.append(mat)
cam_data = bpy.data.cameras.new('comparison_camera')
cam = bpy.data.objects.new('comparison_camera', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = native(a.eye)
cam.rotation_euler = (native(a.target)-cam.location).to_track_quat('-Z', 'Y').to_euler()
cam_data.type = 'ORTHO'
cam_data.ortho_scale = a.scale
cam_data.clip_start = .01
cam_data.clip_end = 1000
scene = bpy.context.scene
scene.camera = cam
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = a.width
scene.render.resolution_y = a.height
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.world.color = (.08, .08, .08)
a.output.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(a.output.resolve())
bpy.context.view_layer.update()
bpy.ops.render.render(write_still=True)
projection = cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(), x=a.width, y=a.height)
report = dict(blender=bpy.app.version_string, geometry_sha256=hashlib.sha256(a.geometry.read_bytes()).hexdigest(),
              texture_sha256=hashlib.sha256(a.texture.read_bytes()).hexdigest() if a.texture else None,
              native_eye=a.eye, native_target=a.target, ortho_scale=a.scale, resolution=[a.width,a.height],
              camera_world=[list(r) for r in cam.matrix_world], projection=[list(r) for r in projection],
              color_transform='Standard', diagnostic='emission only; no Dagor material simulation',
              line_overlays=False, runtime_verified=False)
a.output.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
