"""Personal News contracts. Static validation is independent of source availability."""
from __future__ import annotations
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
import copy, json, re
from jsonschema import Draft202012Validator, FormatChecker
ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,159}$')
DAY = re.compile(r'^\d{4}-\d{2}-\d{2}$')
CATEGORIES = {'ai','agents','work','gamedev','gaming','devices'}
class Invalid(ValueError): pass
def require(ok, message):
    if not ok: raise Invalid(message)
def load(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    require(isinstance(data,dict),f'{path}: expected object')
    return data
def day(value):
    require(isinstance(value,str) and DAY.fullmatch(value),'invalid date')
    return date.fromisoformat(value)
def timestamp(value):
    require(isinstance(value,str),'timestamp required')
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None and result.utcoffset() is not None,'timestamp offset required')
    return result
def text(value,maximum): return isinstance(value,str) and 0<len(value.strip())<=maximum
def url(value):
    if not isinstance(value,str): return False
    try:
        u=urlsplit(value)
        return u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and not any(c.isspace() for c in value)
    except ValueError: return False
def section(item): return item.get('section','main')
def counts(items):
    return {'main':sum(section(i)=='main' for i in items),'radar':sum(section(i)=='radar' for i in items),'new':sum(i['status']=='NEW' for i in items),'update':sum(i['status']=='UPDATE' for i in items),'featured':sum(i['featured'] for i in items)}
def settings(root=ROOT): return load(root/'config/pipeline.json')
def make_schema(cfg, legacy):
    """The immutable v1 contract stays valid; v2 limits derive from pipeline.json."""
    new=copy.deepcopy(legacy);new.pop('$schema',None)
    new['title']='Personal News edition v2'
    new['properties']['version']={'const':2}
    new['properties']['kind']={'const':'daily'}
    new['properties'].pop('edition_id',None)
    new['properties']['items']['maxItems']=cfg['main_target_max']+cfg['radar_max']
    item=new['properties']['items']['items']
    item['required'] += ['section','included_at']
    item['properties']['section']={'enum':['main','radar']}
    item['properties']['included_at']={'type':'string','format':'date-time'}
    item['properties']['published_timezone']={'type':'string','minLength':1,'maxLength':80}
    item['allOf'].append({'if':{'properties':{'section':{'const':'radar'}}},'then':{'properties':{'featured':{'const':False}}}})
    new['properties']['items']['allOf']=[{'contains':{'properties':{'section':{'const':s}},'required':['section']},'minContains':0,'maxContains':maximum} for s,maximum in [('main',cfg['main_target_max']),('radar',cfg['radar_max'])]]
    new['properties']['items']['allOf'].append({'contains':{'properties':{'featured':{'const':True}}},'minContains':0,'maxContains':cfg['max_featured']})
    new['properties']['attention_today']={'type':['object','null'],'required':['text','item_ids','source_url','valid_from','expires_at'],'additionalProperties':False,'properties':{'text':{'type':'string','minLength':1,'maxLength':280},'item_ids':{'type':'array','minItems':1,'uniqueItems':True,'items':{'type':'string','pattern':ID.pattern}},'source_url':{'type':'string','pattern':'^https://'},'valid_from':{'type':'string','format':'date-time'},'expires_at':{'type':'string','format':'date-time'}}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Personal News editions v1 + v2','oneOf':[legacy,new]}
def validate_catalogue(root=ROOT):
    cfg=settings(root)
    for k in ['main_target_min','main_target_max','radar_max','max_featured','discovery_candidate_target_min','discovery_candidate_target_max','main_window_hours','main_exceptional_lookback_hours','radar_lookback_days','rotating_per_category','state_max_events','state_retention_days']:
        require(type(cfg.get(k)) is int and cfg[k]>=0,f'invalid pipeline setting {k}')
    require(0<cfg['main_target_min']<=cfg['main_target_max'],'invalid main target')
    require(0<cfg['discovery_candidate_target_min']<=cfg['discovery_candidate_target_max'],'invalid discovery target')
    require(cfg['max_featured']<=cfg['main_target_max'],'invalid featured cap')
    require(0<cfg['main_window_hours']<=cfg['main_exceptional_lookback_hours'],'invalid main windows')
    require(cfg['radar_lookback_days']>0,'invalid radar window')
    require(set(cfg.get('category_candidate_targets',{}))=={'p1','p2'} and all(isinstance(v,list) and len(v)==2 and all(type(n) is int for n in v) and 0<v[0]<=v[1] for v in cfg['category_candidate_targets'].values()),'invalid category candidate targets')
    require(cfg['timezone']=='Europe/Rome' and url(cfg['website_url']),'invalid timezone/site')
    cats=load(root/'docs/data/categories.json')['categories']
    require({c['id'] for c in cats}==CATEGORIES and len(cats)==len(CATEGORIES),'invalid UI category IDs')
    require(all(not ({'topics','discovery_sources'} & c.keys()) for c in cats),'UI must not duplicate discovery configuration')
    catalogue=load(root/'config/SOURCES.json')
    require(catalogue.get('version')==2,'invalid source catalogue version')
    matrix=catalogue.get('query_matrix',{})
    require(set(matrix)==CATEGORIES and all(isinstance(q,list) and q and all(text(x,300) for x in q) for q in matrix.values()),'incomplete query matrix')
    ids,urls=set(),set()
    sources=catalogue.get('sources',[])
    require(isinstance(sources,list) and sources,'empty source map')
    for s in sources:
        require(isinstance(s,dict) and isinstance(s.get('id'),str) and ID.fullmatch(s['id']),'invalid source id')
        require(s['id'] not in ids and s.get('url') not in urls,'duplicate source id/url')
        ids.add(s['id']);urls.add(s.get('url'))
        require(text(s.get('name'),150) and url(s.get('url')),'invalid source name/URL')
        require(s.get('category') in CATEGORIES and type(s.get('tier')) is int and s['tier'] in (1,2,3),'invalid source category/tier')
        require(s.get('role')=={1:'primary',2:'discovery',3:'scouting'}[s['tier']],'inconsistent source role')
        require(s.get('source_type') in ['blog','release_notes','aggregator','roadmap','community','publication','official_site','official_forum','rss'],'invalid source type')
        require(s.get('check_policy') in ['daily','rotating','on_gap','optional'],'invalid check policy')
        require(type(s.get('enabled')) is bool and type(s.get('requires_primary_verification')) is bool,'invalid source booleans')
        require(s['tier']==1 or s['requires_primary_verification'],'discovery/scouting requires primary verification')
        require(isinstance(s.get('topics'),list) and s['topics'] and all(text(t,150) for t in s['topics']),'invalid topics')
        day(s.get('verified_on'))
        require(text(s.get('verification_method'),80),'missing source verification provenance')
    require({s['category'] for s in sources if s['enabled']}==CATEGORIES,'enabled source coverage missing')
    return cfg,catalogue

def validate_edition(d,categories,root=ROOT):
    cfg=settings(root)
    schema=make_schema(cfg,load(root/'config/edition-v1.schema.json'))
    errors=list(Draft202012Validator(schema,format_checker=FormatChecker()).iter_errors(d))
    require(not errors,'edition does not satisfy v1/v2 JSON Schema: '+(errors[0].message[:320] if errors else ''))
    generated=timestamp(d['generated_at']);zone=ZoneInfo(cfg['timezone']);date_value=day(d['date'])
    require(generated.astimezone(zone).date()==date_value,'generation date must match local edition date')
    if d.get('edition_id'):require(d['kind']=='bootstrap' and d['edition_id']==d['date']+'-initial','invalid initial edition identity')
    events=set()
    for i in d['items']:
        require(ID.fullmatch(i['id']) and ID.fullmatch(i['event_id']),'invalid article/event id')
        require(i['id'].startswith(d['date']+'-'),'article id must start with edition date')
        require(i['event_id'] not in events,'duplicate event in same edition');events.add(i['event_id'])
        require(i['category'] in categories,'unknown category')
        require(text(i['title'],180) and text(i['summary'],1200) and text(i['why_you_care'],600),'blank/oversized text')
        verified=timestamp(i['verified_at']);require(verified<=generated,'verification after generation')
        for src in i['sources']:require(url(src['url']),'unsafe source URL')
        if i['image'] is not None:
            require(url(i['image']['url']) and url(i['image']['source_url']),'unsafe image URL')
            require(text(i['image']['alt'],250) and text(i['image']['credit'],150),'image alt/credit required')
        if i['status']=='UPDATE':
            require(text(i['delta'],800) and ID.fullmatch(i['previous']['id']),'material UPDATE delta/prior ID required')
            require(day(i['previous']['date'])<=date_value,'UPDATE prior date is in future')
        if i['published_date'] is not None:require(day(i['published_date'])<=date_value,'publication date in future')
        if d['kind']=='bootstrap':continue
        require(i['published_date'] is not None,'daily item needs a source publication date')
        if d['version']==1:
            age=(date_value-day(i['published_date'])).days
            if i.get('published_at'):
                pub=timestamp(i['published_at']);require(pub.date()==day(i['published_date']),'source timestamp/date mismatch')
                require(0<=(generated-pub).total_seconds()<=72*3600,'v1 outside 72h window')
            else:require(age<=2,'v1 date-only item too old')
            if age>1 or (i.get('published_at') and (generated-pub).total_seconds()>24*3600):require(text(i.get('recency_reason'),400),'recency reason required')
            continue
        included=timestamp(i['included_at'])
        require(verified<=included<=generated and included.astimezone(zone).date()==date_value,'invalid included_at (retain it on same-day reruns)')
        from legacy import admitted
        if admitted(i,d,root):continue  # Exact, same-edition v1 inclusion; no re-dating.
        if i.get('published_at'):
            pub=timestamp(i['published_at']);require(pub.date()==day(i['published_date']),'source timestamp/date mismatch')
        else:
            pub_zone=ZoneInfo(i['published_timezone']) if i.get('published_timezone') else timezone(timedelta(hours=14))
            pub=datetime.combine(day(i['published_date']),time.min,pub_zone)
        age_hours=(included-pub).total_seconds()/3600
        limit=cfg['radar_lookback_days']*24 if section(i)=='radar' else cfg['main_exceptional_lookback_hours']
        require(0<=age_hours<=limit,'item outside its section freshness window')
        if section(i)=='main' and age_hours>cfg['main_window_hours']:require(text(i.get('recency_reason'),400),'main recovery requires reason')
    a=d.get('attention_today')
    if a:
        require(url(a['source_url']) and text(a['text'],280),'invalid attention source/text')
        byid={i['id']:i for i in d['items']}
        require(all(k in byid for k in a['item_ids']),'attention links missing articles')
        require(any(a['source_url']==s['url'] for k in a['item_ids'] for s in byid[k]['sources']),'attention source not linked to referenced article')
        start,end=timestamp(a['valid_from']),timestamp(a['expires_at'])
        require(start<=generated<end and end-start<=timedelta(days=2),'attention must be current and bounded')
        require(start.astimezone(zone).date()<=date_value<=end.astimezone(zone).date(),'attention outside edition day')
