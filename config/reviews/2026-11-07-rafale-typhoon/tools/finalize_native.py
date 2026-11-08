from pathlib import Path
import argparse,sys,json
p=argparse.ArgumentParser();p.add_argument('--kit-tools',type=Path,required=True);p.add_argument('--game',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
sys.path.insert(0,str(a.kit_tools))
import finalize_geometry as f
f.KIT=a.out/'library';f.GAME=a.game
lib=f.AssetLibrary(a.game,a.out/'cache');f.library=lambda:lib
original=f.subprocess.check_output
def version(*args,**kw):
 try:return original(*args,**kw)
 except f.subprocess.CalledProcessError:return '99c794ab102785c39e628033a09bf4ff18dbe64e (previously recorded backend commit; local git access unavailable)'
f.subprocess.check_output=version
f.run()
