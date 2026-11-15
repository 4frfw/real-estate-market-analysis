import json,math
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill
R=Path(__file__).resolve().parents[1]
def calculate(h,m):
 if set(h)!=set('year primary secondary primary_index secondary_index'.split()) or set(m)!=set('year inflation key_rate'.split()):raise ValueError('schema')
 for t in [h,m]:
  if t.isna().any().any() or t.year.duplicated().any() or not t.map(lambda x:isinstance(x,(int,float)) and math.isfinite(x)).all().all():raise ValueError('missing, duplicate or invalid number')
  if not (t.year%1==0).all():raise ValueError('fractional year')
 if set(h.year)!=set(m.year):raise ValueError('period mismatch')
 d=h.merge(m,on='year',validate='one_to_one').sort_values('year').reset_index(drop=True)
 if len(d)<3 or not (d.year.diff().dropna()==1).all():raise ValueError('year gaps')
 if (d[['primary','secondary','primary_index','secondary_index']]<=0).any().any() or (d.inflation<=-100).any() or (d.key_rate<0).any():raise ValueError('range')
 d['deflator']=(1+d.inflation/100).where(d.index!=0,1).cumprod()
 for s in ['primary','secondary']:
  d[s+'_mean_change']=d[s].pct_change()*100
  d[s+'_index_growth']=d[s+'_index']-100
  d[s+'_real_growth']=(d[s+'_index']/(100+d.inflation)-1)*100
 d['premium']=(d.primary/d.secondary-1)*100
 return d

def payment(rate):
 if rate<0:raise ValueError('negative rate')
 r=rate/1200
 return 25000 if r==0 else 6000000*r/(1-(1+r)**-240)

def build():
 for p in ['data/processed','reports','site']:(R/p).mkdir(parents=True,exist_ok=True)
 d=calculate(pd.read_csv(R/'data/raw/housing.csv'),pd.read_csv(R/'data/raw/macro.csv'))
 d.to_csv(R/'data/processed/market.csv',index=False)
 c=[]
 for s in ['primary','secondary']:
  for f in ['inflation','key_rate']:
   x=d[s+'_index_growth'];v=[x.drop(i).corr(d[f].drop(i)) for i in d.index]
   c.append([s,f,6,float(x.corr(d[f])),float(min(v)),float(max(v))])
 corr=pd.DataFrame(c,columns=['market','factor','n','r','loo_min','loo_max']);corr.to_csv(R/'data/processed/correlations.csv',index=False)
 scen=pd.DataFrame([[r,6000000,240,round(payment(r),2)] for r in [8,12,16,20]],columns=['rate','loan','months','payment']);scen.to_csv(R/'data/processed/scenarios.csv',index=False)
 stats=d[['primary','secondary','inflation','key_rate']].describe();stats.to_csv(R/'data/processed/statistics.csv')
 summary={'rows':len(d),'primary_growth':float((d.primary.iloc[-1]/d.primary.iloc[0]-1)*100),'secondary_growth':float((d.secondary.iloc[-1]/d.secondary.iloc[0]-1)*100),'premium':float(d.premium.iloc[-1]),'real_primary':float(d.primary_real_growth.iloc[-1]),'real_secondary':float(d.secondary_real_growth.iloc[-1])}
 (R/'reports/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 wb=Workbook();wb.remove(wb.active)
 for name,t in [('Data',d),('Correlations',corr),('Scenarios',scen),('Statistics',stats.reset_index())]:
  w=wb.create_sheet(name);w.append(list(t.columns))
  for row in t.itertuples(index=False,name=None):w.append([None if pd.isna(v) else v for v in row])
  w.freeze_panes='A2';w.auto_filter.ref=w.dimensions
  for cell in w[1]:cell.fill=PatternFill('solid',fgColor='17324D');cell.font=Font(color='FFFFFF',bold=True)
  for col in w.columns:w.column_dimensions[col[0].column_letter].width=22
 w=wb.create_sheet('Formulas');w.append(['year','mean change primary, %','premium, %','real primary, %','real secondary, %'])
 for i in range(2,len(d)+2):w.append([f'=Data!A{i}',None if i==2 else f'=(Data!B{i}/Data!B{i-1}-1)*100',f'=(Data!B{i}/Data!C{i}-1)*100',f'=(Data!D{i}/(100+Data!F{i})-1)*100',f'=(Data!E{i}/(100+Data!F{i})-1)*100'])
 import runpy
 runpy.run_path(str(R/'scripts/excel_presentation.py'))['enhance'](wb,d,summary)
 wb.save(R/'reports/market.xlsx')
 html='<html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Рынок жилья России</title><script src="plotly.min.js"></script><style>body{font:17px Arial;max-width:1100px;margin:auto;padding:20px;color:#17324d}table{width:100%}td,th{padding:8px}</style><h1>Рынок жилья России, 2019–2024</h1><p>Чичилов Кирилл · ЧЛБ25-ИУП-БИ01</p><p>Индекс не равен отношению средних цен. Ставка — декабрьская. Корреляции по шести годам не доказывают причинность.</p>'
 for title,columns in [('Средние цены, тыс. руб./м²',['primary','secondary']),('Прирост индексов и инфляция, %',['primary_index_growth','secondary_index_growth','inflation']),('Реальные приросты, %',['primary_real_growth','secondary_real_growth']),('Макрофакторы, %',['inflation','key_rate'])]:
  fig=go.Figure()
  for col in columns:fig.add_trace(go.Scatter(x=d.year.tolist(),y=d[col].tolist(),name=col,mode='lines+markers'))
  fig.update_layout(title=dict(text=title.replace(', ', '<br>'),x=0.02,y=0.98,font=dict(size=18)),template='plotly_white',height=700,margin=dict(t=110,b=240,l=70,r=30),xaxis=dict(rangeslider=dict(visible=True,thickness=0.12)),legend=dict(orientation='v',yanchor='top',y=-0.45,xanchor='left',x=0))
  html+=fig.to_html(full_html=False,include_plotlyjs=False)
 html+='<h2>Корреляции</h2>'+corr.to_html(index=False)+'<h2>Сценарии, не предложения банков</h2>'+scen.to_html(index=False)+'<h2>Источники</h2><p>Полные URL и происхождение: data/sources.md. Это исторический срез, не рынок 2026 года.</p></html>'
 (R/'site/index.html').write_text(html,encoding='utf-8');(R/'site/plotly.min.js').write_text(get_plotlyjs(),encoding='utf-8');(R/'site/.nojekyll').touch()
 return d,summary
if __name__=='__main__':print(build()[1])
