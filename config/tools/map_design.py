"""Map an image into an extracted native UV layout without guessing part coordinates."""
from pathlib import Path
import argparse, json
import numpy as np
from PIL import Image
import cv2
from uv_repeat import repeat_triangles

KIT=Path(__file__).resolve().parents[1]
# Camera directions in native Dagor model space: +X nose, +Y up, +Z left.
VIEWS={
 'top':(2,-1,0,-1,(0,1,0)),
 'bottom':(2,1,0,-1,(0,-1,0)),
 'left':(0,1,1,-1,(0,0,1)),
 'right':(0,-1,1,-1,(0,0,-1)),
 'front':(2,-1,1,-1,(1,0,0)),
 'back':(2,1,1,-1,(-1,0,0)),
}

def rasterize(uv,attributes,shape,image,valid=None):
    """Interpolate source-image XY at native UV pixel centres. No island bbox warp."""
    w,h=shape
    out=np.zeros((h,w,4),np.uint8);coverage=np.zeros((h,w),np.uint8)
    p=uv.astype(np.float64).copy();p[:,:,0]*=w;p[:,:,1]=(1-p[:,:,1])*h
    if valid is None:valid=np.ones(len(p),bool)
    count=0
    for idx in np.flatnonzero(valid):
        t=p[idx];q=attributes[idx]
        xmin=max(0,int(np.ceil(t[:,0].min()-.5)));xmax=min(w-1,int(np.floor(t[:,0].max()-.5)))
        ymin=max(0,int(np.ceil(t[:,1].min()-.5)));ymax=min(h-1,int(np.floor(t[:,1].max()-.5)))
        if xmax<xmin or ymax<ymin:continue
        x0,y0=t[0];x1,y1=t[1];x2,y2=t[2]
        det=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(det)<1e-12:continue
        yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1].astype(np.float32);xx+=.5;yy+=.5
        a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/det
        b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/det
        c=1-a-b;inside=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)
        if not inside.any():continue
        mx=(a*q[0,0]+b*q[1,0]+c*q[2,0]).astype(np.float32)
        my=(a*q[0,1]+b*q[1,1]+c*q[2,1]).astype(np.float32)
        sampled=cv2.remap(image,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
        out[ymin:ymax+1,xmin:xmax+1][inside]=sampled[inside]
        coverage[ymin:ymax+1,xmin:xmax+1][inside]=255;count+=1
    return out,coverage,count

def project_coordinates(xyz,view,image_size,rect=None,bounds=None):
    ia,sa,ib,sb,direction=VIEWS[view]
    p=np.stack([xyz[:,:,ia]*sa,xyz[:,:,ib]*sb],axis=2).astype(np.float64)
    if bounds is None:
        lo=p.min((0,1));hi=p.max((0,1))
    else:lo=np.array(bounds[:2],float);hi=np.array(bounds[2:],float)
    iw,ih=image_size
    if rect is None:rect=[0,0,iw,ih]
    x0,y0,x1,y1=rect
    # Explicit rectangle is the orthographic world frame. It may be a hand-aligned
    # silhouette region inside the supplied image; it is never inferred from color.
    p=(p-lo)/np.maximum(hi-lo,1e-12)
    p[:,:,0]=x0+p[:,:,0]*(x1-x0)-.5;p[:,:,1]=y0+p[:,:,1]*(y1-y0)-.5
    return p.astype(np.float32),{'plane_bounds':[float(lo[0]),float(lo[1]),float(hi[0]),float(hi[1])],
      'image_rectangle':list(rect),'camera_direction':list(direction)}

def run(args):
    catalog=json.loads((KIT/'catalog.json').read_text(encoding='utf8'))
    entry=next(x for x in catalog['textures'] if args.model in [x['model'],x['id'],*x.get('unit_aliases',[])] and args.texture in [x['texture'],*x.get('texture_aliases',[])])
    folder=KIT.parent/entry['path']
    meta=json.loads((folder/'metadata.json').read_text(encoding='utf-8'))
    data=np.load(folder/'geometry.npz');uv=data['triangle_uv'];xyz=data['triangle_xyz']
    tri_part=data['triangle_part'];island=data['triangle_island']
    if not args.raw_uv:
        uv,xyz,origin,tiles=repeat_triangles(uv,xyz)
        tri_part=tri_part[origin];island=island[origin]
    design=np.array(Image.open(args.image).convert('RGBA'));ih,iw=design.shape[:2]
    w,h=meta['authoring_resolution']
    if args.size:w,h=args.size
    valid=np.ones(len(uv),bool)
    if args.parts:
        names=args.parts.split(',');missing=[name for name in names if name not in meta['part_names']]
        if missing:raise ValueError(f'Unknown part names: {missing}')
        ids=[meta['part_names'].index(name) for name in names];valid &= np.isin(tri_part,ids)
    if args.islands:valid &= np.isin(island,[int(x) for x in args.islands.split(',')])
    if not valid.any():raise ValueError('The requested parts/islands contain no faces in this texture.')
    details={}
    if args.mode=='atlas':
        p=uv.astype(np.float64).copy();p[:,:,0]=p[:,:,0]*iw-.5;p[:,:,1]=(1-p[:,:,1])*ih-.5
    elif args.mode=='island':
        if args.islands is None:raise ValueError('island mode requires --islands')
        lo=uv[valid].min((0,1));hi=uv[valid].max((0,1))
        p=(uv-lo)/np.maximum(hi-lo,1e-12);p[:,:,0]=p[:,:,0]*iw-.5;p[:,:,1]=(1-p[:,:,1])*ih-.5
        details['island_uv_bounds']=[*lo.tolist(),*hi.tolist()]
    else:
        p,details=project_coordinates(xyz,args.view,(iw,ih),args.image_rect,args.world_bounds)
        if not args.both_sides:
            normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0]).astype(np.float64)
            center=xyz.mean((0,1));winding=np.sign(np.sum(normals*(xyz.mean(1)-center))) or 1
            if args.normal_sign is not None:winding=args.normal_sign
            valid &= (normals@np.array(VIEWS[args.view][4]))*winding>1e-10
            details['normal_sign_used']=float(winding)
        details['occlusion']='No z-buffer; facing triangles only. Hidden facing surfaces may receive paint; use --parts/--islands to control them.'
    color,mask,count=rasterize(uv,p,(w,h),design,valid)
    if args.base:
        base=np.array(Image.open(args.base).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS))
        alpha=color[:,:,3:4].astype(np.float32)/255
        color=np.clip(color.astype(float)*alpha+base*(1-alpha),0,255).astype(np.uint8)
        color[:,:,3]=255
    args.out.parent.mkdir(parents=True,exist_ok=True)
    if args.out.suffix.lower()=='.dds':
        Image.fromarray(color).save(args.out)
        preview=args.out.with_suffix('.png');Image.fromarray(color).save(preview)
    else:Image.fromarray(color).save(args.out)
    Image.fromarray(mask).save(args.out.with_name(args.out.stem+'_coverage.png'))
    report={'model':args.model,'texture':args.texture,'mode':args.mode,'view':args.view if args.mode=='project' else None,
      'size':[w,h],'design_size':[iw,ih],'triangles_used':count,'painted_pixels':int(np.count_nonzero(mask)),
      'uncovered_pixels_are_transparent':not bool(args.base),'mapping_details':details,
      'limitations':['Orthographic image-to-mesh projection; an arbitrary perspective photo requires camera alignment first.',
       'Stacked UV islands can request conflicting colors; later faces win. Use island/part selection for deliberate control.',
       'This maps color only, and never fabricates packed normal/material channels. Existing suitable _n must be handled separately.']}
    args.out.with_suffix('.mapping.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model',required=True);p.add_argument('--texture',required=True)
    p.add_argument('--image',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--mode',choices=['atlas','island','project'],default='project')
    p.add_argument('--view',choices=list(VIEWS),default='top')
    p.add_argument('--size',nargs=2,type=int,metavar=('WIDTH','HEIGHT'))
    p.add_argument('--parts');p.add_argument('--islands')
    p.add_argument('--image-rect',nargs=4,type=float,metavar=('X0','Y0','X1','Y1'))
    p.add_argument('--world-bounds',nargs=4,type=float,metavar=('U0','V0','U1','V1'))
    p.add_argument('--both-sides',action='store_true');p.add_argument('--normal-sign',type=int,choices=[-1,1])
    p.add_argument('--base',type=Path)
    p.add_argument('--raw-uv',action='store_true',help='Disable repeat wrapping; keep native out-of-unit coordinates clipped to the image')
    return p

if __name__=='__main__':run(parser().parse_args())
