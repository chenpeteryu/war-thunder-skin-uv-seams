from pathlib import Path
import json,numpy as np,sys
from PIL import Image
base=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else Path(__file__).resolve().parent
R=base/('texel_probes_alpha' if '--transparent' in sys.argv else 'texel_probes_interior')
m=json.loads((R/'manifest.json').read_text());rows=[]
for p in m['probes']:
 im=np.asarray(Image.open(R/p['image']).convert('RGBA'));x,y=p['sample_image_pixel'];actual=im[y,x,:3].astype(float);expected=np.asarray(p['expected_srgb']);err=float(abs(actual-expected).max());rows.append({**p,'actual_srgb':actual.tolist(),'alpha':int(im[y,x,3]),'max_code_error':err,'passed':err<=2})
report={'probes':rows,'passed':sum(x['passed'] for x in rows),'failed':sum(not x['passed'] for x in rows),'missing_groups':m['missing_groups'],'scope':'Readback of independently rendered texel colors at world-projected sample centres. Local samples only, not whole-library accuracy proof.'}
(R/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='probes'},indent=2));print('failures',[(x['model'],x['group'],x['side'],x['max_code_error'],x['actual_srgb'],x['expected_srgb']) for x in rows if not x['passed']])
