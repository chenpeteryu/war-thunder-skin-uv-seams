"""Clip native repeated UV triangles into 0..1 while preserving interpolated attributes."""
import numpy as np

def _clip(poly,axis,bound,keep_greater):
    if not len(poly):return poly
    out=[];last=poly[-1];last_inside=last[axis]>=bound if keep_greater else last[axis]<=bound
    for point in poly:
        inside=point[axis]>=bound if keep_greater else point[axis]<=bound
        if inside!=last_inside:
            t=(bound-last[axis])/(point[axis]-last[axis]);out.append(last+(point-last)*t)
        if inside:out.append(point)
        last,last_inside=point,inside
    return np.asarray(out,dtype=np.float64)

def repeat_triangles(uv,attributes=None):
    uv=np.asarray(uv)
    if attributes is None:attributes=np.empty((*uv.shape[:2],0),np.float64)
    inside=np.all((uv>=0)&(uv<=1),axis=(1,2))
    us=[uv[inside].astype(np.float64)];attrs=[np.asarray(attributes)[inside].astype(np.float64)]
    ids=[np.flatnonzero(inside)];tiles=[np.zeros((inside.sum(),2),np.int32)]
    for index in np.flatnonzero(~inside):
        t=uv[index].astype(np.float64);a=np.asarray(attributes[index],dtype=np.float64)
        lo=np.floor(t.min(0)).astype(int);hi=np.ceil(t.max(0)).astype(int)-1
        hi=np.maximum(lo,hi)
        if np.prod(hi-lo+1)>256:raise ValueError(f'UV triangle {index} spans more than 256 tiles; inspect its native data')
        poly=np.concatenate([t,a],axis=1)
        for x in range(lo[0],hi[0]+1):
            for y in range(lo[1],hi[1]+1):
                clipped=poly.copy()
                for axis,bound,greater in [(0,x,True),(0,x+1,False),(1,y,True),(1,y+1,False)]:
                    clipped=_clip(clipped,axis,bound,greater)
                    if len(clipped)<3:break
                if len(clipped)<3:continue
                for j in range(1,len(clipped)-1):
                    tri=clipped[[0,j,j+1]]
                    area=np.cross(tri[1,:2]-tri[0,:2],tri[2,:2]-tri[0,:2])
                    if abs(area)<1e-14:continue
                    us.append((tri[:,:2]-[x,y])[None]);attrs.append(tri[:,2:][None]);ids.append(np.array([index]));tiles.append(np.array([[x,y]],np.int32))
    return np.concatenate(us).astype(np.float32),np.concatenate(attrs).astype(np.float32),np.concatenate(ids),np.concatenate(tiles)
