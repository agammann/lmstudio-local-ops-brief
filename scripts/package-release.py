"""Package the clean committed source without dependencies or model weights."""
import hashlib,json,pathlib,subprocess,sys,zipfile
root=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from ops_brief import VERSION
def git(*args):return subprocess.check_output(['git',*args],cwd=root).decode().strip()
assert not git('status','--porcelain','--untracked-files=normal'),'Commit the source before packaging.'
commit=git('rev-parse','HEAD');assert len(commit)==40
paths=git('ls-files').splitlines()
assert all('.git' not in pathlib.PurePosixPath(p).parts and not any(part.startswith('.env') for part in pathlib.PurePosixPath(p).parts) for p in paths)
directory=root/'release-artifacts';directory.mkdir(exist_ok=True)
name=f'lmstudio-local-ops-brief_{VERSION}_source.zip';archive=directory/name;prefix=f'lmstudio-local-ops-brief_{VERSION}/'
subprocess.run(['git','archive','--format=zip',f'--prefix={prefix}',f'--output={archive}',commit],cwd=root,check=True)
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None and package.comment.decode()==commit
    files={e.filename[len(prefix):]:package.read(e) for e in package.infolist() if not e.is_dir()}
    assert set(files)==set(paths)
    for path,data in files.items():assert data==subprocess.check_output(['git','show',commit+':'+path],cwd=root),path
checksum=hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+name+'\n'
(directory/(name+'.sha256')).write_text(checksum,encoding='utf-8',newline='\n')
(directory/'SHA256SUMS').write_text(checksum,encoding='utf-8',newline='\n')
print(json.dumps({'version':VERSION,'commit':commit,'files':len(paths),'archive':name,'sha256':checksum.split()[0]}))
