"""Geometry-bound Su-30 fin joint coverage; no game artwork is included."""
import numpy as np
import cv2

def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def generate(native, part_names, ink_alpha, protected_boxes, size=4096):
    xyz=native['triangle_xyz'];part=np.array(part_names)[native['triangle_part']];center=xyz.mean(1)
    face=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]);face/=np.maximum(np.linalg.norm(face,axis=1)[:,None],1e-12)
    g=native
    selected=((part=='tail')|np.char.startswith(part,'rudder'))&(xyz[:,:,0].max(1)>-7.1)&(xyz[:,:,0].min(1)<-.8)&(xyz[:,:,1].max(1)>-.65)&(xyz[:,:,1].min(1)<1.25)&(abs(center[:,2])>1.6)&(abs(face[:,2])>.16)
    weight=np.zeros((size,size),np.float32)
    for uv,positions in zip(g['triangle_uv'][selected],xyz[selected]):
        q=uv.copy();q[:,0]=q[:,0]*size-.5;q[:,1]=(1-q[:,1])*size-.5
        x0,y0=np.maximum(np.floor(q.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(q.max(0)).astype(int),4095)
        if x0>x1 or y0>y1:continue
        yy,xx=np.mgrid[y0:y1+1,x0:x1+1];a,b,c=q;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den)<1e-10:continue
        w0=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den;w1=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w2=1-w0-w1;inside=(w0>=-1e-5)&(w1>=-1e-5)&(w2>=-1e-5)
        p=w0[:,:,None]*positions[0]+w1[:,:,None]*positions[1]+w2[:,:,None]*positions[2]
        w=smooth(-.65,-.35,p[:,:,1])*(1-smooth(.65,1.20,p[:,:,1]))*smooth(-7.05,-6.65,p[:,:,0])*(1-smooth(-1.1,-.8,p[:,:,0]))*smooth(1.65,1.9,abs(p[:,:,2]));w[~inside]=0
        view=weight[y0:y1+1,x0:x1+1];np.maximum(view,w,out=view)
    weight*=1-ink_alpha.astype(np.float32)/255
    mask=np.zeros((size,size),np.uint8)
    for box in protected_boxes:
        x0,y0,x1,y1=np.rint(np.array(box)*size/1536).astype(int);mask[y0:y1,x0:x1]=255
    weight*=smooth(0,24*size/4096,cv2.distanceTransform(255-mask,cv2.DIST_L2,5))
    return weight, np.where(selected)[0]
