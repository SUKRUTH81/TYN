import json,collections
p=r'C:\Users\akhila.y\Downloads\TYN_Assessment\inputs\dataset.json'
d=json.load(open(p,encoding='utf-8')); print(d.keys());print(collections.Counter(r['kind'] for r in d['records']))
for r in d['records']:
 if r['kind'] in ['manifest','requirement','release_manifest']:print(json.dumps(r,ensure_ascii=True,indent=2))
print('ENV configured:', {k:bool(__import__('os').getenv(k)) for k in ['JIRA_BASE_URL','JIRA_EMAIL','JIRA_API_TOKEN','OPENAI_API_KEY']})
