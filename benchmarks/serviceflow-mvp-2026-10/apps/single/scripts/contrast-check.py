"""Focused mathematical confirmation of the changed small-text palette."""
import json,re
from pathlib import Path
css=Path('src/client/styles.css').read_text()
def luminance(hex):
 values=[int(hex[i:i+2],16)/255 for i in (0,2,4)]
 linear=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in values]
 return sum(a*b for a,b in zip(linear,[0.2126,0.7152,0.0722]))
def ratio(a,b):
 dark,light=sorted([luminance(a),luminance(b)])
 return (light+0.05)/(dark+0.05)
results={}
for name in ['new','quoted','booked']:
 block=re.search(r'\.status-'+name+r'\s*\{([^}]+)\}',css).group(1)
 fg=re.search(r'color:\s*#([0-9a-f]+)',block).group(1)
 bg=re.search(r'background:\s*#([0-9a-f]+)',block).group(1)
 results[name]=round(ratio(fg,bg),2)
placeholder=re.search(r'input::placeholder,\s*textarea::placeholder\s*\{[^}]*color:\s*#([0-9a-f]+)',css).group(1)
results['placeholder']=round(ratio(placeholder,'fffefa'),2)
print(json.dumps(results));assert all(value>=4.5 for value in results.values())
Path('evidence/contrast.json').write_text(json.dumps(results,indent=2)+'\n')
