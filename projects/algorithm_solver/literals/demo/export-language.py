from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent.parent;out=Path(__file__).resolve().parent
p=root/'pass2/working/packages/shared7';m=json.loads((p/'manifest.json').read_text());d=json.loads((p/'dictionary.json').read_text());cases=json.loads((root/'pass2/working/execution/report.json').read_text())
assert m['dictionary_sha256']=='62ab89348d4781187375f35663f81b6304a70b9f951d9bd3327fecae6d3b8c39'
assert hashlib.sha256((p/'dictionary.ltd').read_bytes()).hexdigest()==m['dictionary_sha256']
names=['Best stock profit','Single unpaired number','Strict majority','Anagram equality','First unique-character index','Attendance eligibility','Candy-type allocation','Harmonious subsequence length','Flower placement','Maximum fixed-window average','Robot returns to origin','Increasing contiguous run','Binary search','ASCII lowercase','Pivot index','Jewel membership count','N-times repeated value','Height-order mismatches','Defang IPv4','Remove vowels']
counts={r['problem']:r['total'] for r in cases['rows']}
data={'schema':'gamma.literal-demo-dictionary.v1','profile':'gamma.literal-shared7-interactive.v1','source_commit':'0951af88c332818133f132cce9d6cf8e277b90cb','dictionary_sha256':m['dictionary_sha256'],'dictionary_bytes':m['dictionary_bytes'],'literals':[r['text'] for r in d['literals']],'problems':[dict(id=k,title=title,sequence=row['sequence'],source_sha256=row['source_sha256'],reference_cases=counts[k]) for (k,row),title in zip(sorted(m['programs'].items()),names)],'evidence':{'reference_cases_passed':3834,'reference_cases_total':3834,'literal_count':79,'source_only_selections':154,'source_only_bits':1078,'interactive_controls_included':False,'source':'https://github.com/clocksmith/gamma/blob/0951af88c332818133f132cce9d6cf8e277b90cb/projects/algorithm_solver/literals/pass2/working/execution/report.json'}}
(out/'literal-language.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print({'dictionary_sha256':m['dictionary_sha256'],'problems':len(data['problems']),'literals':len(data['literals'])})
