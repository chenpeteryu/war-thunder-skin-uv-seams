"""Run the independent checker on every current primary/auxiliary database."""
from pathlib import Path
import argparse,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]

def main():
    p=argparse.ArgumentParser();p.add_argument('--report',type=Path);args=p.parse_args()
    reports=[]
    for database in sorted((ROOT/'config').rglob('seam_links.sqlite3')):
        command=[sys.executable,str(ROOT/'config/tools/validate_seam_db.py'),'--db',str(database)]
        completed=subprocess.run(command,capture_output=True,encoding='utf8')
        if completed.returncode:
            raise RuntimeError(f'{database.relative_to(ROOT)}\n{completed.stdout}\n{completed.stderr}')
        result=json.loads(completed.stdout)
        assert result['all_checks_passed']
        result['database']=database.relative_to(ROOT).as_posix()
        reports.append(result)
        print(f'PASS {result["database"]} ({result["checked_stub_pixels"]} pixels)',flush=True)
    expected=json.loads((ROOT/'config/catalog.json').read_text(encoding='utf8'))['textures']
    assert sum('/missile_seams/' in x['database'] for x in reports)==sum(x['category']=='missiles' for x in expected)
    report={'databases':len(reports),'checked_stub_pixels':sum(x['checked_stub_pixels'] for x in reports),'all_checks_passed':True,'runtime_verified':False,'results':reports}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))

if __name__=='__main__':main()
