"""Check the actual source ZIP with a fresh standard-library-only consumer."""
import hashlib,pathlib,subprocess,sys,tempfile,zipfile
root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from ops_brief import VERSION
directory=root/'release-artifacts';name=f'lmstudio-local-ops-brief_{VERSION}_source.zip';archive=directory/name
assert (directory/(name+'.sha256')).read_text(encoding='utf-8')==hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+name+'\n'
with tempfile.TemporaryDirectory(prefix='ops brief consumer ') as temporary:
    destination=pathlib.Path(temporary).resolve();prefix=f'lmstudio-local-ops-brief_{VERSION}'
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        for entry in package.infolist():
            path=pathlib.PurePosixPath(entry.filename)
            assert not path.is_absolute() and '..' not in path.parts and path.parts[0]==prefix
            assert (entry.external_attr>>16)&0o170000!=0o120000
        package.extractall(destination)
    source=destination/prefix
    for arguments in [['-m','unittest','-v'],['ops_brief.py','--help'],['ops_brief.py','--version']]:
        result=subprocess.run([sys.executable,*arguments],cwd=source,capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        if arguments[-1]=='--version':assert result.stdout.strip()=='ops-brief '+VERSION
    saved=source/'previous.json';saved.write_text('previous saved brief',encoding='utf-8')
    result=subprocess.run([sys.executable,'ops_brief.py','--model','fixture','--incident',' ','--output',str(saved)],cwd=source,capture_output=True,text=True)
    assert result.returncode==2 and saved.read_text(encoding='utf-8')=='previous saved brief'
print('Fresh source ZIP: twelve tests, help/version and rejected-input preservation passed.')
