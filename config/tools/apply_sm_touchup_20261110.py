"""Apply the user-approved label removals and native fin-root detail restoration.
Requires user-owned Nov9 C, archived original reference C, native target C and J16 C.
Normal/material textures are deliberately never written.
"""
from pathlib import Path
import json,hashlib
import numpy as np,cv2
from PIL import Image
from apply_sm_material_surface_repair import read
from sm_reference_text_mask import text_mask

def erase_reference(original,box):
 x0,y0,x1,y1=box;roi=original[y0:y1,x0:x1,:3].copy();gray=cv2.cvtColor(roi,cv2.COLOR_RGB2GRAY);bg=cv2.morphologyEx(gray,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8));mask=cv2.dilate(((bg.astype(int)-gray.astype(int)>9)*255).astype('uint8'),np.ones((3,3),np.uint8));return cv2.inpaint(roi,mask,4,cv2.INPAINT_TELEA)
