"""Check the variant merge boundary and recorded local render evidence."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'config/reviews/2026-11-07-rafale-typhoon'

def main():
    inventory=json.loads((REVIEW/'source_inventory.json').read_text(encoding='utf8'))
    entries=[a for a in json.loads((ROOT/'config/catalog.json').read_text(encoding='utf8'))['textures'] if a.get('review_batch')==inventory['review_batch']]
    assert len(entries)==inventory['layout_count']==79
    assert {a['model'] for a in entries}==set(inventory['native_models'])
    for name,digest in inventory['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    bindings=json.loads((ROOT/'config/aircraft_variants.json').read_text(encoding='utf8'))['units']
    assert len(bindings)==9 and len({a['model'] for a in bindings})==8
    greek=next(a for a in bindings if a['unit']=='rafale_eg_greece')
    assert greek['model']=='rafale_c_f3'
    assert {'from':'rafale_c_f3_c*','to':'rafale_eg_greece_c*'} in greek['replacements']
    header=json.loads((REVIEW/'greek_texture_headers.json').read_text(encoding='utf8'))
    assert max(tuple(a['resolution']) for a in header if a['texture']=='rafale_c_f3_c')==(4096,4096)
    assert max(tuple(a['resolution']) for a in header if a['texture']=='rafale_eg_greece_c')==(4096,4096)
    main_entry=next(a for a in entries if a['texture']=='rafale_c_f3_c')
    assert 'rafale_eg_greece' in main_entry['unit_aliases'] and 'rafale_eg_greece_c' in main_entry['texture_aliases']
    comparison=json.loads((REVIEW/'variant_comparison.json').read_text(encoding='utf8'))
    assert len(comparison['comparisons'])==16
    assert not any(a['main_geometry_merge_eligible'] for a in comparison['comparisons'])
    for model in inventory['native_models']:
        metadata=json.loads((REVIEW/'renders'/f'{model}.json').read_text(encoding='utf8'))
        assert len(metadata['views'])==14 and all((REVIEW/'renders'/f'{model}_{view["view"]}.png').is_file() for view in metadata['views'])
        body=next(a for a in entries if a['model']==model and a['texture']==model+'_c')
        assert metadata['body_geometry_sha256']==hashlib.sha256((ROOT/body['path']/'geometry.npz').read_bytes()).hexdigest()
        probe=json.loads((REVIEW/'model_probe.json').read_text(encoding='utf8'))[model]
        assert not any(part['skinned'] for part in probe['parts'])
    controls=json.loads((REVIEW/'texel_probes_alpha/validation.json').read_text(encoding='utf8'))
    assert controls['passed']==64 and controls['failed']==0 and not controls['missing_groups']
    for row in controls['probes']:
        image=np.array(Image.open(REVIEW/'texel_probes_alpha'/row['image']).convert('RGBA'))
        x,y=row['sample_image_pixel'];assert image[y,x,3]==255
        assert np.max(abs(image[y,x,:3].astype(float)-row['expected_srgb']))<=2
    seams=json.loads((REVIEW/'independent_seam_validation.json').read_text(encoding='utf8'))
    assert seams['all_checks_passed'] and seams['checked_stub_pixels']==76623
    print('RAFALE_TYPHOON_PASS: 9 unit bindings, 8 native models, 79 layouts, 112 views, 64 local texel controls')

if __name__=='__main__':main()
