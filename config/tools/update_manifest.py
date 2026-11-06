"""Explicitly refresh hashes after intentional changes; validation never rewrites them."""
from pathlib import Path
import subprocess,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def main():
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode('utf8').split('\0')
    excluded={'config/file_hashes.json','config/validation/library_validation.json'}
    hashes={}
    for name in sorted(set(names)-excluded-{''}):
        path=ROOT/name
        if path.is_file():hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT/'config/file_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('HASH_MANIFEST',len(hashes))
if __name__=='__main__':main()
