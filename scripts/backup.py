import hashlib,json,subprocess,zipfile,tempfile,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'backup';B.mkdir(exist_ok=True)
files=[p for p in R.rglob('*') if p.is_file() and not any(x in p.relative_to(R).parts for x in ['.git','backup','__pycache__','.venv'])]
with zipfile.ZipFile(B/'project.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(R))
if (R/'.git').exists():subprocess.run(['git','bundle','create',str(B/'history.bundle'),'--all'],cwd=R,check=True)
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in B.iterdir() if p.name in ['project.zip','history.bundle']}
(B/'checksums.json').write_text(json.dumps(hashes,indent=2))
for name,h in hashes.items():assert hashlib.sha256((B/name).read_bytes()).hexdigest()==h
with tempfile.TemporaryDirectory() as t:
 T=Path(t)/'restored';T.mkdir()
 with zipfile.ZipFile(B/'project.zip') as z:
  assert z.testzip() is None
  for name in z.namelist():assert (T/name).resolve().is_relative_to(T.resolve())
  z.extractall(T)
 subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=T,check=True)
 subprocess.run([sys.executable,'scripts/analyze.py'],cwd=T,check=True)
 assert json.loads((T/'reports/summary.json').read_text())==json.loads((R/'reports/summary.json').read_text())
 if 'history.bundle' in hashes:
  subprocess.run(['git','clone',str((B/'history.bundle').resolve()),str(Path(t)/'git-copy')],check=True,capture_output=True)
  subprocess.run(['git','fsck','--full'],cwd=Path(t)/'git-copy',check=True,capture_output=True)
(B/'restore.json').write_text(json.dumps({'status':'PASS','hashes':hashes},indent=2));print('RESTORE PASS')
