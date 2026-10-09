"""Package/read audit records only. Does not change frozen model evidence."""
import io,json,hashlib,gzip,tarfile,sys
from pathlib import Path
P=Path(__file__).resolve().parent
MARK='UFC_EDGE_GROUND_PATHWAY_POC_MEASUREMENT_AND_HAZARD_AUDIT_V1_COMPLETE'
def sha(b):return hashlib.sha256(b).hexdigest()
def package():
 import pandas as pd
 for part in P.glob("DIAGNOSTIC_RECORDS.tar.xz.part*"):part.unlink()
 records={};buffer=io.BytesIO()
 with tarfile.open(fileobj=buffer,mode='w:xz',preset=6) as tar:
  for f in sorted(P.glob('*.csv.gz')):
   b=gzip.decompress(f.read_bytes());name=f.name[:-3]
   if name=='fight_hazard_accounting.csv':
    d=pd.read_csv(io.BytesIO(b),float_precision='round_trip');cols=['fight_id','event_id','event_date','outer_year','division','scheduled_rounds','method','support','F']+[c for c in d if c.startswith(('B3_','B5_','A1_','A2_','A4_'))]+['ever_entry','entries','ground_minutes','standing_minutes','alive_minutes','returns','sub_attempts','ground_actions','sub_finishes','ground_ko','standing_ko','raw_dec','K','ground_share','conversion_weighted'];b=d[cols].to_csv(index=False,float_format='%.17g').encode()
   info=tarfile.TarInfo(name);info.size=len(b);info.mtime=0;tar.addfile(info,io.BytesIO(b));records[name]={'sha256':sha(b),'bytes':len(b)}
 data=buffer.getvalue();parts=[]
 for i,start in enumerate(range(0,len(data),100000)):
  name=f'DIAGNOSTIC_RECORDS.tar.xz.part{i:03d}';b=data[start:start+100000];(P/name).write_bytes(b);parts.append({'name':name,'sha256':sha(b),'bytes':len(b)})
 (P/'RECORDS_MANIFEST.json').write_text(json.dumps({'archive_sha256':sha(data),'archive_bytes':len(data),'parts':parts,'records':records,'format':'Concatenate numbered parts, verify archive hash, extract plain CSV records. Primary archive table retains identifiers, unchanged cell membership, F and every reward; duplicate frozen reference columns are omitted. Oracle records retain all reward columns. Full original merged table regenerates with audit.py.'},indent=2,sort_keys=True))
def seal():
 paths=[f for f in sorted(P.iterdir()) if f.is_file() and f.name not in ['EVIDENCE_MANIFEST.json',MARK+'.json'] and not f.name.endswith('.csv.gz')]
 m={'starting_main_sha':'54a0b647825295b09342fa02cca4f40210bf4f94','frozen_PR163_manifest':'839587507aa470f8d0cf8df7b66f13c04a665790ebde1b2802abfc0c99f07d8b','classification':'E','draft_PR':164,'artifacts':{f.name:{'sha256':sha(f.read_bytes()),'bytes':f.stat().st_size} for f in paths}}
 (P/'EVIDENCE_MANIFEST.json').write_text(json.dumps(m,indent=2,sort_keys=True)+'\n');digest=sha((P/'EVIDENCE_MANIFEST.json').read_bytes())
 (P/(MARK+'.json')).write_text(json.dumps({'status':MARK,'evidence_manifest_sha256':digest,'classification':'E','no_model_trained':True,'no_selected_constants':True,'no_promotion':True},indent=2)+'\n');print(digest)
def verify():
 m=json.loads((P/'EVIDENCE_MANIFEST.json').read_text());assert all(sha((P/f).read_bytes())==v['sha256'] for f,v in m['artifacts'].items())
 r=json.loads((P/'RECORDS_MANIFEST.json').read_text());data=b''.join((P/x['name']).read_bytes() for x in r['parts']);assert sha(data)==r['archive_sha256'];assert all(sha((P/x['name']).read_bytes())==x['sha256'] for x in r['parts'])
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as tar:
  assert set(tar.getnames())==set(r['records'])
  for f,v in r['records'].items():assert sha(tar.extractfile(f).read())==v['sha256']
 w=json.loads((P/'WORKFLOW_HASH.json').read_text());assert sha((P.parents[2]/w['path']).read_bytes())==w['sha256']
 c=json.loads((P/(MARK+'.json')).read_text());assert c['evidence_manifest_sha256']==sha((P/'EVIDENCE_MANIFEST.json').read_bytes());print('Audit manifest/archive PASS',c['evidence_manifest_sha256'])
if __name__=='__main__':
 if '--package' in sys.argv:package()
 if '--seal' in sys.argv:seal()
 if '--verify' in sys.argv:verify()
