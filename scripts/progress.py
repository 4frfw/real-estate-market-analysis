import os,json,csv,subprocess,datetime
from pathlib import Path
import plotly.graph_objects as go
R=Path(__file__).resolve().parents[1]
x=subprocess.run(['gh','issue','list','--repo',os.environ['GITHUB_REPOSITORY'],'--state','all','--limit','1000','--json','number,state'],check=True,capture_output=True,text=True)
items=json.loads(x.stdout)
if not items:raise RuntimeError('Create actual Issues first')
f=R/'data/project/progress.csv';f.parent.mkdir(parents=True,exist_ok=True);new=not f.exists()
with f.open('a',newline='') as h:
 w=csv.writer(h)
 if new:w.writerow(['utc','total','open'])
 w.writerow([datetime.datetime.now(datetime.timezone.utc).isoformat(),len(items),sum(x['state']=='OPEN' for x in items)])
with f.open() as h:rows=list(csv.DictReader(h))
fig=go.Figure(go.Scatter(x=[x['utc'] for x in rows],y=[int(x['open']) for x in rows],mode='lines+markers'))
fig.update_layout(title='Observed issue burndown',template='plotly_white')
fig.write_html(R/'site/burndown.html',include_plotlyjs='directory')
