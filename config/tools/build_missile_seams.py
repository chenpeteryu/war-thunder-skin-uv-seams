"""Build separate texture-scoped 1px reference trees from preserved missile UVs.

All native LOD0 surfaces are retained. This is not an exterior visibility filter.
No stubs are painted into textures, outline images, or diagnostic renders.
"""
from pathlib import Path
import argparse, hashlib, json, sqlite3, tempfile
from contextlib import closing
import numpy as np
from build_seam_db import SCHEMA, build_model

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', help='Optional short or native model ID')
    args = parser.parse_args()
    catalog = json.loads((ROOT/'config/catalog.json').read_text(encoding='utf8'))
    for item in catalog['textures']:
        if item['category'] != 'missiles':
            continue
        if args.model and args.model not in (item['id'], item['model']):
            continue
        folder = ROOT/item['path']
        source = folder/'geometry.npz'
        metadata = json.loads((folder/'metadata.json').read_text(encoding='utf8'))
        output = ROOT/item['seam_database']
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.building.sqlite3')
        if temporary.exists():
            temporary.unlink()
        with tempfile.TemporaryDirectory(prefix='missile_seam_') as directory:
            inputs = Path(directory)
            with np.load(source) as data:
                arrays = {k: data[k] for k in ('triangle_xyz','triangle_uv','triangle_part','triangle_island')}
            arrays['source_triangle_id'] = np.arange(len(arrays['triangle_uv']), dtype=np.int32)
            np.savez_compressed(inputs/(item['model']+'.npz'), **arrays)
            model_info = {
                'part_names': metadata['part_names'],
                'reference_resolution': metadata['authoring_resolution'],
                'native_geometry_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'filter': {'scope':'all native LOD0 geometry in this texture; no visibility filtering',
                           'texture':item['texture'], 'runtime_verified':False},
            }
            (inputs/(item['model']+'.json')).write_text(json.dumps(model_info), encoding='utf8')
            with closing(sqlite3.connect(temporary)) as database:
                database.executescript(SCHEMA)
                database.executemany('INSERT INTO meta VALUES(?,?)', [
                    ('schema_version','1'), ('stub_width_px','1'),
                    ('pixel_convention','x=u*W-.5, y=(1-v)*H-.5; integer indices identify texel centers'),
                    ('graph_policy','One tree per missile and texture; no cross-atlas references'),
                    ('not_a_claim','Full native geometry, no visibility filter or runtime verification; assembly_reference is not a physical shared seam'),
                ])
                _, _, report = build_model(database, inputs, item['model'], 1, 1)
                assert database.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                assert not database.execute('PRAGMA foreign_key_check').fetchall()
                database.commit()
            temporary.replace(output)
            report['geometry_scope'] = model_info['filter']
            report['database_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
            (output.parent/'build_report.json').write_text(json.dumps(report, indent=2), encoding='utf8')

if __name__ == '__main__':
    main()
