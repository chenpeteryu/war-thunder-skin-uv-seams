"""Validate geometry-bound SM surface adaptation data, without artwork inputs."""
from pathlib import Path
import json, hashlib
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def main():
    rows = []
    for short in ['su30sm', 'su30sm2']:
        recipe = json.loads((ROOT / f'config/recipes/{short}_surface_adaptation.json').read_text(encoding='utf-8'))
        geometry = ROOT / recipe['geometry']
        bundle = ROOT / recipe['array_bundle']
        assert hashlib.sha256(geometry.read_bytes()).hexdigest() == recipe['geometry_sha256']
        assert hashlib.sha256(bundle.read_bytes()).hexdigest() == recipe['array_bundle_sha256']
        assert recipe['native_geometry_and_uv_changed'] is False
        with np.load(geometry) as native, np.load(bundle) as data:
            total = len(native['triangle_uv'])
            assert total == recipe['native_triangle_count']
            for name in data.files:
                if name.endswith('_triangle_ids'):
                    ids = data[name]
                    assert len(ids) == len(np.unique(ids))
                    assert np.all((ids >= 0) & (ids < total))
            assert len(recipe['continuity_groups']) == 6
            for group in recipe['continuity_groups']:
                assert len(data[group['triangle_ids_array']]) == group['count']
                assert np.array(group['source_calibration']['raw_corners']).shape == (4, 2)
            count = len(data['detail_triangle_ids'])
            assert count == recipe['detail_transfer']['selected_triangles']
            assert data['detail_source_uv'].shape == (count, 3, 2)
            assert np.isfinite(data['detail_source_uv']).all()
            pixels = 4096 * 4096
            for name in ['continuity_mask_packbits', 'review_coating_mask_packbits']:
                assert data[name].dtype == np.uint8 and data[name].size * 8 == pixels
            coating = np.unpackbits(data['review_coating_mask_packbits'], bitorder='little')
            assert int(coating.sum()) == recipe['review_coating']['actual_mask_pixels']
        from sm_fin_joint_weights import generate
        with np.load(geometry) as native, np.load(bundle) as data:
            meta=json.loads(geometry.with_name('metadata.json').read_text(encoding='utf-8'))
            joint=recipe['fin_joint_repair']
            weight, ids=generate(native,meta['part_names'],data['marking_ink_alpha_u8'],joint['protected_guide_boxes'])
            expected=np.rint(weight*255).astype(np.uint8)
            assert np.array_equal(expected,data['fin_joint_weight_u8'])
            assert len(ids)==joint['selected_triangles']
            assert joint['native_GA'].startswith('byte exact')
            assert data['marking_restore_scope_packbits'].size*8==4096*4096
            assert data['final_repair_scope_packbits'].size*8==4096*4096
        rows.append({'model': recipe['model'], 'continuity_groups': 6, 'selected_detail_triangles': count, 'coating_mask_pixels': int(coating.sum())})
    print(json.dumps({'scope': 'SM/SM2 artwork adaptation recipes only', 'checks_passed': True, 'models': rows, 'game_verified': False}, indent=2))


if __name__ == '__main__':
    main()
