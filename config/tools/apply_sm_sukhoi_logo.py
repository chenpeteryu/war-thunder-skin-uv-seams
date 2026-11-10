"""Replace the existing fin manufacturer word with the sourced emblem and wordmark."""
from pathlib import Path
import json,hashlib
import numpy as np,cv2
from PIL import Image
from apply_sm_material_surface_repair import read
from sm_reference_text_mask import text_mask
def apply(profile,root,color):
 d=json.loads(Path(profile).read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
 assert sha(color)==d['input_C_sha256'];assert sha(Path(root)/d['geometry'])==d['geometry_sha256'];assert sha(Path(root)/d['alpha_mask'])==d['alpha_mask_sha256']
 c=read(color);x0,y0,x1,y1=d['box_authoring'];a=np.array(Image.open(Path(root)/d['alpha_mask'])).astype(float)/255;roi=c[y0:y1,x0:x1,:3];old=text_mask('SUKHOI',x1-x0,y1-y0,0,'condensed',False);mask=cv2.dilate((old>0).astype('uint8')*255,np.ones((3,3),np.uint8));clean=cv2.inpaint(roi.copy(),mask,3,cv2.INPAINT_TELEA);roi[:]=np.rint(clean*(1-a[:,:,None])+d['ink_value']*a[:,:,None]).astype('uint8');return c
