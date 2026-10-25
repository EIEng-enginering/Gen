#!/usr/bin/env python3
"""Read-only nine-volume cold-backup SHA/tar verification.

Never extracts, deletes, starts Docker or reads production databases. Emits only
counts and expected archive hashes; no living-person metadata or media names.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

EXPECTED=['gramps_users','gramps_index','gramps_thumb_cache','gramps_cache',
          'gramps_secret','gramps_db','gramps_media','gramps_tmp','research_postgres']

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()

def verify(root, require_media=False, max_uncompressed=60*1024**3):
    root=Path(root).resolve()
    if 'onedrive' in str(root).lower(): raise ValueError('Raw backup path inside OneDrive is forbidden')
    if (root/'INCOMPLETE.txt').exists():raise ValueError('Backup marked INCOMPLETE')
    names=['gen24_'+k+'.tgz' for k in EXPECTED]
    actual=sorted(x.name for x in root.glob('*.tgz'))
    if actual!=sorted(names):raise ValueError('Expected exactly nine archive names')
    checksum=root/'SHA256SUMS.txt'
    if not checksum.is_file():raise ValueError('No SHA256SUMS.txt')
    recorded={}
    for line in checksum.read_text(encoding='ascii').splitlines():
        match=re.fullmatch(r'([A-Fa-f0-9]{64})\s+([A-Za-z0-9_.-]+\.tgz)',line.strip())
        if not match or match.group(2) in recorded:raise ValueError('Invalid checksum manifest')
        recorded[match.group(2)]=match.group(1).lower()
    if sorted(recorded)!=sorted(names):raise ValueError('Manifest has unexpected/missing archives')
    count=0;media=0;bytes_total=0
    for name in names:
        tarpath=root/name
        if sha256(tarpath)!=recorded[name]:raise ValueError('Archive hash mismatch: '+name)
        with tarfile.open(tarpath,'r:gz') as tf:
            for member in tf:
                # reject links/devices, not merely path traversal; archive must be safe if later restored
                parts=Path(member.name.replace('\\','/')).parts
                if member.isdir() and member.name in ('.','./'):
                    continue
                if member.name.startswith('/') or '..' in parts or not parts or not(member.isfile() or member.isdir()):
                    raise ValueError('Nonregular or unsafe archive member in '+name)
                if member.isfile():
                    bytes_total+=member.size;count+=1
                    if bytes_total>max_uncompressed:raise ValueError('Excessive uncompressed size')
                    if name=='gen24_gramps_media.tgz':media+=1
    if require_media and media<1:raise ValueError('No nonempty media files: recovery gate not met')
    return {'archives':len(names),'hashes_verified':True,'regular_file_count':count,
            'media_file_count':media,'media_restore_requirement_met':media>0,
            'backup_source_path': 'restricted_local_only',
            'restored':False,'accepted_release':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('backup_dir')
    ap.add_argument('--require-media',action='store_true')
    args=ap.parse_args()
    try:print(json.dumps(verify(args.backup_dir,args.require_media),indent=2))
    except (ValueError,OSError,tarfile.TarError) as err:ap.exit(2,'INVALID BACKUP: '+str(err)+'\n')
if __name__=='__main__':main()
