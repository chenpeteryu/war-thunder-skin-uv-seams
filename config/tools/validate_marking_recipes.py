"""Check the two scoped SM/SM2 marking recipes without requiring a full checkout."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    counts = []
    for short, model in [('su30sm', 'su_30sm'), ('su30sm2', 'su_30sm2')]:
        path = ROOT / f'config/recipes/{short}_endfield_high_markings.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data['model'] == model and data['texture'] == model + '_c'
        geometry = ROOT / data['geometry']
        assert geometry.resolve().is_relative_to(ROOT)
        assert hashlib.sha256(geometry.read_bytes()).hexdigest() == data['geometry_sha256']
        with np.load(geometry) as native:
            assert len(native['triangle_uv']) == data['native_triangle_count']
        assert data['authoring_resolution'] == [4096, 4096]
        assert data['guide_resolution'] == [1536, 1536]
        regions = data['regions']
        assert len(regions) == 15 and len({r['id'] for r in regions}) == 15
        assert sum(r['text'] == 'SUKHOI' for r in regions) == 1
        assert next(r for r in regions if r['id'] == 'nose_manufacturer')['style'] == 'diagonal_hatch'
        assert next(r for r in regions if r['id'] == 'fin_large_manufacturer')['text'] == 'SU-30'
        protected = next(r for r in regions if r['id'] == 'endfield_protected')
        assert protected['action'] == 'preserve_original' and protected['text'] == 'ENDFIELD'
        for region in regions:
            if 'guide_rectangle_xyxy' in region:
                source = np.array(region['guide_rectangle_xyxy'])
                pixels = np.rint(source * 4096 / 1536).astype(int)
                assert pixels.tolist() == region['authoring_rectangle_xyxy']
                x0, y0, x1, y1 = pixels
                assert 0 <= x0 < x1 <= 4096 and 0 <= y0 < y1 <= 4096
                assert np.allclose(region['uv_bounds'], [x0/4096, 1-y1/4096, x1/4096, 1-y0/4096], atol=1e-12)
            else:
                points = np.array(region['authoring_polygon_xy'])
                assert np.array_equal(points, np.rint(np.array(region['guide_polygon_xy']) * 4096 / 1536))
                assert np.all((points >= 0) & (points <= 4096))
                assert np.allclose(region['polygon_uv'], np.column_stack([points[:, 0]/4096, 1-points[:, 1]/4096]), atol=1e-12)
                assert region['clip_to_geometry']['parts'] == ['tail', 'rudder*']
            if 'hatch' in region:
                assert 0 < region['hatch']['ink_pixels_per_period'] < region['hatch']['period_authoring_pixels']
        review = json.loads((ROOT / data['review']).read_text(encoding='utf-8'))
        assert review['models'][model]['geometry_sha256'] == data['geometry_sha256']
        assert review['models'][model]['layout_validation']['normal_DDS_byte_identical']
        counts.append({'model': model, 'regions': len(regions), 'geometry_sha256': data['geometry_sha256']})
    report = {'scope': 'Two SM/SM2 marking recipes and referenced geometry only; not a full library validation.', 'models': counts, 'checks_passed': True, 'game_verified': False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
