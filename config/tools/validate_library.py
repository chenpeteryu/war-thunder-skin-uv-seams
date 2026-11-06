"""Validate relocated assets, missile coordinates, navigation and stored hashes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit
import argparse,csv,hashlib,json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        self.links += [v for k,v in attrs if k in ('href','src')]

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path);p.add_argument('--skip-hashes',action='store_true');args=p.parse_args()
    entries=json.loads((ROOT/'config/catalog.json').read_text(encoding='utf8'))['textures']
    assert len(entries)==136
    assert len({(a['model'],a['texture']) for a in entries})==len(entries)
    triangles=0;boundary_rows=0;missile_endpoints=0;errors=0.0
    for item in entries:
        folder=(ROOT/item['path']).resolve();assert folder.is_relative_to(ROOT)
        m=json.loads((folder/'metadata.json').read_text(encoding='utf8'))
        assert m['model']==item['model'] and m['texture']==item['texture']
        assert hashlib.sha256((folder/'geometry.npz').read_bytes()).hexdigest()==m['geometry_sha256']
        with np.load(folder/'geometry.npz') as d:
            uv=d['triangle_uv'];xyz=d['triangle_xyz'];edges=d['boundary_uv']
            assert uv.shape==xyz.shape[:2]+(2,) and uv.shape[1:]==(3,2)
            assert len(uv)==m['triangles'] and len(edges)==m['boundary_segments']
            assert np.isfinite(uv).all() and np.isfinite(xyz).all() and np.isfinite(edges).all()
            triangles+=len(uv)
            if item['category']=='missiles':
                dtype=np.dtype([('u','<i8'),('v','<i8')])
                # Promote before quantization: float32 multiplication can move a
                # half-step across rounding and disagree with saved float64 edges.
                vertices=np.unique(np.ascontiguousarray(np.rint(uv.reshape(-1,2).astype(np.float64)*1e6).astype('<i8')).view(dtype).ravel())
                endpoints=np.ascontiguousarray(np.rint(edges.reshape(-1,2)*1e6).astype('<i8')).view(dtype).ravel()
                where=np.searchsorted(vertices,endpoints)
                assert np.all(where<len(vertices)) and np.all(vertices[where]==endpoints)
                missile_endpoints+=len(endpoints)
        w,h=m['authoring_resolution'];assert [item['width'],item['height']]==[w,h]
        for name in ['outline.png','coverage_mask.png']:
            with Image.open(folder/name) as image:assert image.size==(w,h) and image.mode=='L'
        for name in ['outline.svg','island_ids.png','islands.csv','parts.csv']:assert (folder/name).is_file()
        if item['category']=='missiles':
            count=0
            with (folder/'boundary_coordinates.csv').open(encoding='utf-8-sig',newline='') as f:
                for row in csv.DictReader(f):
                    error=max(abs(float(row[f'x{k}_px'])-float(row[f'u{k}'])*w) for k in (0,1))
                    error=max(error,*(abs(float(row[f'y{k}_px'])-(1-float(row[f'v{k}']))*h) for k in (0,1)))
                    assert error<1e-5;errors=max(errors,error);count+=1
            assert count==m['boundary_segments'];boundary_rows+=count
            assert (ROOT/item['seam_database']).is_file()
        assert item['normal_layout_status']=='assumed_shared_with_c_pending_render_verification'
    parser=Links();parser.feed((ROOT/'index.html').read_text(encoding='utf8'))
    for link in parser.links:
        parsed=urlsplit(link)
        if not parsed.scheme and parsed.path:assert (ROOT/unquote(parsed.path)).is_file(),link
    source=json.loads((ROOT/'config/validation/migration_sources.json').read_text(encoding='utf8'))
    for path,expected in source['files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
    checked=0
    if not args.skip_hashes:
        hashes=json.loads((ROOT/'config/file_hashes.json').read_text(encoding='utf8'))
        for path,expected in hashes.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
        checked=len(hashes)
    report={'aircraft_models':len({x['model'] for x in entries if x['category']=='aircraft'}),'missile_models':len({x['model'] for x in entries if x['category']=='missiles'}),'texture_layouts':len(entries),'triangles':triangles,'original_asset_files_unchanged':len(source['files']),'missile_native_boundary_endpoints_checked':missile_endpoints,'missile_csv_boundary_rows_checked':boundary_rows,'max_missile_csv_formula_error_px':errors,'local_index_links_checked':len(parser.links),'manifest_files_checked':checked,'all_checks_passed':True,'runtime_verified':False,'normal_layout_verified':False}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
