import re,zlib,pathlib
b=pathlib.Path(r'C:\Users\akhila.y\Downloads\TYN_Assessment\TYN_AI_Engineering_Assessment.pdf').read_bytes()
objs={int(m[1]):m[2] for m in re.finditer(rb'(\d+) 0 obj\s*(.*?)\s*endobj',b,re.S)}
def stream(v):
 m=re.search(rb'stream\r?\n(.*?)\r?\nendstream',v,re.S)
 if not m:return b''
 return zlib.decompress(m[1]) if b'/FlateDecode' in v else m[1]
fonts={}
for n,v in objs.items():
 m=re.search(rb'/ToUnicode (\d+) 0 R',v)
 if m:
  s=stream(objs[int(m[1])]); fonts[n]={bytes.fromhex(a.decode()):bytes.fromhex(c.decode()).decode('utf-16-be') for a,c in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>',s) if len(c)>=4}
refs={a.decode():fonts[int(n)] for a,n in re.findall(rb'/(F\d+) (\d+) 0 R',b) if int(n) in fonts}
lines=[]
for n,v in objs.items():
 s=stream(v)
 if b'BT' not in s:continue
 for block in re.findall(rb'BT(.*?)ET',s,re.S):
  f=re.search(rb'/(F\d+) [\d.]+ Tf',block)
  if not f:continue
  cmap=refs[f[1].decode()]
  text=''.join(''.join(cmap.get(bytes([x]),'?') for x in bytes.fromhex(h.decode())) for h in re.findall(rb'<([0-9A-Fa-f]+)>',block))
  lines.append(text)
pathlib.Path('assessment.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines))
