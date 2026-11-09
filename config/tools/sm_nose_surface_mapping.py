"""Native nose skin parameterization. Exclude narrow pitot islands; do not use whole-fuse max X. Geometry inputs must be eagerly loaded arrays. No source artwork included."""
import numpy as np

def skin(g,names):
 p=g['triangle_xyz'];sel=names=='fuse';exclude=[]
 for island in np.unique(g['triangle_island'][sel]):
  ix=sel&(g['triangle_island']==island);q=p[ix];span=np.ptp(q,axis=(0,1))
  if q[:,:,0].min()>12 and max(span[1:])<.2:exclude.append(int(island))
 sel&=~np.isin(g['triangle_island'],exclude)
 return sel,exclude,float(p[sel,:,0].max())

def profile(p,start,end):
 xx=np.linspace(start,end-.001,160);edges=np.concatenate([p[:,[0,1]],p[:,[1,2]],p[:,[2,0]]]);a=edges[:,0];b=edges[:,1];dx=b[:,0]-a[:,0];valid=abs(dx)>1e-8;a=a[valid];b=b[valid];dx=dx[valid];yc=[];ry=[];rz=[]
 for x in xx:
  t=(x-a[:,0])/dx;ok=(t>=-1e-7)&(t<=1+1e-7);q=a[ok]+t[ok,None]*(b[ok]-a[ok]);
  if not len(q):yc.append(np.nan);ry.append(np.nan);rz.append(np.nan);continue
  yc.append((q[:,1].max()+q[:,1].min())/2);ry.append(max((q[:,1].max()-q[:,1].min())/2,.002));rz.append(max(abs(q[:,2]).max(),.002))
 vals=[]
 for a in [yc,ry,rz]:
  a=np.array(a);good=np.isfinite(a);vals.append(np.interp(xx,xx[good],a[good]))
 return xx,np.array(vals)

def params(xyz,prof):
 xx,data=prof;x=xyz[...,0];cy=np.interp(x,xx,data[0]);ry=np.interp(x,xx,data[1]);rz=np.interp(x,xx,data[2]);yy=(xyz[...,1]-cy)/ry;zz=xyz[...,2]/rz;return np.arctan2(zz,yy),np.sqrt(yy*yy+zz*zz)

def sample(im,xy):
 xy=xy.astype(np.float32);x=np.clip(xy[:,0],0,im.shape[1]-1);y=np.clip(xy[:,1],0,im.shape[0]-1);x0=np.floor(x).astype(int);y0=np.floor(y).astype(int);x1=np.minimum(x0+1,im.shape[1]-1);y1=np.minimum(y0+1,im.shape[0]-1);dx=(x-x0)[:,None];dy=(y-y0)[:,None];return np.rint(im[y0,x0,:3]*(1-dx)*(1-dy)+im[y0,x1,:3]*dx*(1-dy)+im[y1,x0,:3]*(1-dx)*dy+im[y1,x1,:3]*dx*dy).clip(0,255).astype(np.uint8)

