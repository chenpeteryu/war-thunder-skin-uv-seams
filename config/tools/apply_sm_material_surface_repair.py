"""Replay geometry-bound SM HIGH material/surface corrections using user-owned input art."""
from pathlib import Path
import argparse,hashlib,json,re,struct
import numpy as np,cv2
from PIL import Image

def read(p):
 p=Path(p)
 if p.suffix.lower()=='.dds':
  with p.open('rb') as f:
   h=f.read(128);height,width=struct.unpack_from('<II',h,12);fourcc=h[84:88];bpp=struct.unpack_from('<I',h,88)[0]
   if fourcc==b'\0'*4 and bpp==32:
    v=np.frombuffer(f.read(width*height*4),dtype='<u4').reshape(height,width);return np.stack([((v&m)>>((m&-m).bit_length()-1)).astype(np.uint8) if m else np.full((height,width),255,np.uint8) for m in struct.unpack_from('<IIII',h,92)],2)
 return np.array(Image.open(p).convert('RGBA'))

def apply(recipe,root,color,normal,native_color,canard_color=None,nose_color=None):
 d=json.loads(Path(recipe).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(Path(root)/d['geometry'])==d['geometry_sha256'];assert sha(Path(root)/d['array_bundle'])==d['array_bundle_sha256'];assert sha(native_color)==d['native_color_sha256'];data=np.load(Path(root)/d['array_bundle']);c=read(color);n=read(normal);base=c.copy();ga=n[:,:,[1,3]].copy();F=d['resolution'][0];cc=c.reshape(-1,4);nn=n.reshape(-1,4)
 for p,key in [(color,'input_color_sha256'),(normal,'input_normal_sha256')]:assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==d[key],('Wrong pre-repair input',p)
 masks={key:np.unpackbits(data[v['array']],bitorder='little').astype(bool) for key,v in d['masks'].items()}
 material=np.zeros(F*F,bool)
 for key,mask in masks.items():
  if key in ['airframe_coating_pixels','lerx_material_pixels','fin_both_faces_material_pixels','pgo_material_pixels'] or re.fullmatch(r'gear_\w+_face-?1_pixels',key):material|=mask
 for key in data.files:
  if key.endswith('_reference_target_pixels'):material[data[key]]=True
 nn[material,0]=102;nn[material,2]=178
 gray=cv2.cvtColor(c[:,:,:3],cv2.COLOR_RGB2GRAY);closed=cv2.morphologyEx(gray,cv2.MORPH_CLOSE,np.ones((19,19),np.uint8));mask=masks['lerx_substrate_pixels'];values=np.clip(186+.55*(gray.ravel()[mask].astype(float)-closed.ravel()[mask]),150,186).round().astype(np.uint8);cc[mask,:3]=values[:,None]
 mask=masks['fin_root_tone_pixels'];cc[mask,:3]=np.clip(cc[mask,:3].astype(int)+9,0,179).astype(np.uint8)
 native=cv2.resize(read(native_color),(F,F),interpolation=cv2.INTER_CUBIC);gray=cv2.cvtColor(native[:,:,:3],cv2.COLOR_RGB2GRAY).astype(float);detail=gray-cv2.GaussianBlur(gray,(0,0),3)
 weight=data['lerx_native_detail_weight_u8'].astype(float)/255;edge=np.zeros((F,F),float)
 for ch in [1,3]:
  a=n[:,:,ch].astype(float);edge+=abs(a-cv2.GaussianBlur(a,(0,0),1.3))
 coat=np.clip(186+np.clip(detail*np.clip((edge-1.5)/6,0,1)*.7,-26,3),0,255)
 c[:,:,:3]=np.rint(c[:,:,:3].astype(float)*(1-weight[:,:,None])+coat[:,:,None]*weight[:,:,None]).astype(np.uint8)
 for key,mask in masks.items():
  match=re.fullmatch(r'(gear_\w+)_face(-?1)_pixels',key)
  if not match:continue
  name,face=match.groups();value=d['door_base_values'][name][face];values=np.clip(value+.25*detail.ravel()[mask],max(0,value-18),min(255,value+12)).round().astype(np.uint8);cc[mask,:3]=values[:,None]
 preserve=masks['pgo_art_preserve_pixels'];cc[preserve]=base.reshape(-1,4)[preserve]
 erase=masks['pgo_caption_erase_pixels'];cc[erase,:3]=187
 alpha=data['pgo_caption_ink_alpha_u8'].reshape(-1).astype(float)/255;ink=alpha>0;cc[ink,:3]=np.rint(cc[ink,:3]*(1-alpha[ink,None])+105*alpha[ink,None]).astype(np.uint8)
 if 'nose_reference_target_pixels' in data.files:
  from sm_nose_surface_mapping import sample
  assert nose_color is not None,'Provide the original reference C with --nose-reference-color'
  assert sha(nose_color)==d['nose_reference_color_sha256']
  source=read(nose_color);ix=data['nose_reference_target_pixels'];xy=data['nose_reference_source_xy_float32'];weight=data['nose_reference_blend_u8'].astype(float)/255
  cc[ix,:3]=np.rint(cc[ix,:3]*(1-weight[:,None])+sample(source,xy)*weight[:,None]).astype(np.uint8)
  mask=masks['nose_foreign_hardware_cleanup_pixels'];coat=np.clip(188+np.clip(detail*np.clip((edge-1.5)/6,0,1)*.7,-20,3),0,255).round().astype(np.uint8);cc[mask,:3]=coat.reshape(-1)[mask,None]
  mask=masks['nose_native_detail_restore_pixels'];cc[mask,:3]=native.reshape(-1,4)[mask,:3]
 assert np.array_equal(n[:,:,[1,3]],ga) and np.array_equal(c[:,:,3],base[:,:,3])
 return c,n

def main():
 p=argparse.ArgumentParser();p.add_argument('--recipe',type=Path,required=True);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--color',type=Path,required=True);p.add_argument('--normal',type=Path,required=True);p.add_argument('--native-color',type=Path,required=True);p.add_argument('--canard-color',type=Path);p.add_argument('--nose-reference-color',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();c,n=apply(a.recipe,a.root,a.color,a.normal,a.native_color,a.canard_color,a.nose_reference_color);a.output.mkdir(parents=True,exist_ok=True);d=json.loads(a.recipe.read_text(encoding='utf-8'))
 for ch,v in [('c',c),('n',n)]:
  for ext in ['png','dds']:Image.fromarray(v).save(a.output/(d['model']+'_'+ch+'.'+ext))
if __name__=='__main__':main()
