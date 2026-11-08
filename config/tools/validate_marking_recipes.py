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
            native_islands = set(native['triangle_island'].tolist())
        assert data['authoring_resolution'] == [4096, 4096]
        assert data['guide_resolution'] == [1536, 1536]
        regions = data['regions']
        assert data['schema_version'] == 2
        assert len(regions) == 17 and len({r['id'] for r in regions}) == 17
        assert sum(r['text'] == 'SUKHOI' for r in regions) == 3
        assert next(r for r in regions if r['id'] == 'nose_manufacturer')['hatch']['direction'] == 'diagonal'
        assert next(r for r in regions if r['id'] == 'fin_large_manufacturer')['text'] == 'IRKUTSK'
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
                assert region['clip_to_geometry']['required_geometry_sha256'] == data['geometry_sha256']
                assert region['clip_to_geometry']['native_island'] in native_islands
            if isinstance(region.get('hatch'), dict):
                assert 0 < region['hatch']['ink_pixels_per_period'] < region['hatch']['period_authoring_pixels']
        review = json.loads((ROOT / data['review']).read_text(encoding='utf-8'))
        assert review['models'][model]['geometry_sha256'] == data['geometry_sha256']
        assert review['models'][model]['native_GA_preserved']
        assert review['models'][model]['outside_authorized_scope_changed'] == 0
        forbidden = ['015','016','AVIC','NORINCO','WS10','TAIHANG','CAICD','61249','PLAAF']
        assert not any(word in region['text'] for word in forbidden for region in regions)
        assert sum(region['text'] == ('30SM2' if model.endswith('2') else '30SM') for region in regions) == 5
        counts.append({'model': model, 'regions': len(regions), 'geometry_sha256': data['geometry_sha256']})
    report = {'scope': 'Two SM/SM2 marking recipes and referenced geometry only; not a full library validation.', 'models': counts, 'checks_passed': True, 'game_verified': False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
