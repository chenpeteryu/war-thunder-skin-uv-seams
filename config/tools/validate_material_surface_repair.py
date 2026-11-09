"""Validate geometry-bound material repair masks without distributing source artwork."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2]
def main():
 rows=[]
 for short in ['su30sm','su30sm2']:
  d=json.loads((R/f'config/recipes/{short}_material_surface_20261109.json').read_text(encoding='utf-8'));g=R/d['geometry'];bundle=R/d['array_bundle'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(g)==d['geometry_sha256'] and sha(bundle)==d['array_bundle_sha256'];data=np.load(bundle);F=d['resolution'][0]
  for name,item in d['masks'].items():
   a=data[item['array']];assert a.dtype==np.uint8 and a.size*8==F*F;assert int(np.unpackbits(a,bitorder='little').sum())==item['pixels']
  assert data['lerx_native_detail_weight_u8'].shape==(F,F) and data['lerx_native_detail_weight_u8'].dtype==np.uint8
  assert d['reference_coating_RB']==[102,178]
  assert np.array_equal(data[d['masks']['pgo_art_preserve_pixels']['array']],data[d['masks']['pgo_material_pixels']['array']])
  if 'nose_reference_target_pixels' in data.files:
   ix=data['nose_reference_target_pixels'];xy=data['nose_reference_source_xy_float32'];a=data['nose_reference_blend_u8'];assert xy.shape==(len(ix),2) and a.shape==(len(ix),);assert np.isfinite(xy).all() and np.all((xy>=-.5)&(xy<=8191.5));assert np.all((ix>=0)&(ix<F*F));assert sha(R/d['nose_reference_geometry'])==d['nose_reference_geometry_sha256']
  ink=data['pgo_caption_ink_alpha_u8'];assert ink.shape==(F,F) and ink.dtype==np.uint8 and np.any(ink)
  review=json.loads((R/d['review']).read_text(encoding='utf-8'))['models'][d['model']];assert review['native_GA_preserved'] and review['outside_authorized_scope_changed']==0 and review['reusable_replay_difference_pixels']==0
  rows.append({'model':d['model'],'mask_groups':len(d['masks']),'geometry_sha256':d['geometry_sha256']})
 print(json.dumps({'scope':'Two SM/SM2 geometry-bound material/surface repair recipes only; source art not included.','checks_passed':True,'models':rows,'game_verified':False},indent=2))
if __name__=='__main__':main()
