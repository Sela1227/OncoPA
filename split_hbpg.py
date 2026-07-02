#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OncoPA 專用：把母程式的合併癌別「肝膽胰胃癌」拆成 肝癌/膽道癌/胰臟癌/胃癌。
母程式（Cancer Drug）沿用肝膽胰胃合併類（對齊 MDT 第7團隊）；OncoPA 需求是選癌別時分開，
故每次從母程式重生 index.html 後，重跑本腳本即可。冪等：若已無「肝膽胰胃癌」則不動作。"""
import re,sys,json
HBPG='肝膽胰胃癌'
ORG_ORDER=['肝癌','膽道癌','胰臟癌','胃癌']

def organs_of(t):
    o=[]
    if re.search(r'膽道癌|膽管|肝內膽管|biliary',t,re.I): o.append('膽道癌')
    if re.search(r'肝細胞癌|HCC|hepatocellular',t,re.I): o.append('肝癌')
    if re.search(r'胰臟癌|胰腺癌|pancrea',t,re.I): o.append('胰臟癌')
    if re.search(r'胃癌|胃腺癌|胃食道|gastric',t,re.I): o.append('胃癌')  # 不配 GIST
    return o
def clause_text(c):
    p=[c.get('header','') or '',c.get('_title','') or '']
    for si in (c.get('subitems') or []): p.append(si if isinstance(si,str) else (si.get('text') or si.get('header') or ''))
    return ' '.join(p)
def items_text(d): return ' '.join(clause_text(c) for c in (d.get('items') or []) if isinstance(c,dict))
def subCore(s): return re.sub(r'[（(][^）)]*[）)]','',s).strip()
def item_organs(t,subs):
    clean=t.replace('**','');m=re.search(r'\*\*(.+?)\*\*',t);label=(m.group(1) if m else '');hay=label+' '+clean[:40]
    for s in subs:
        core=subCore(s)
        if s and (s in hay or (core and core in hay)): return organs_of(s)
    return organs_of(subs[0]) if subs else []

def split_drug(d):
    cancers=d.get('cancers') or []
    if HBPG not in cancers: return
    pc=d.get('per_cancer')
    slice=pc.get(HBPG) if isinstance(pc,dict) else None
    found=[]  # 這支藥實際涉及的器官（保序）
    new_pc={}
    if slice and slice.get('clauses'):
        buckets={}
        for c in slice['clauses']:
            for og in (organs_of(clause_text(c)) or []):
                buckets.setdefault(og,[]).append(c)
        for og in ORG_ORDER:
            if og in buckets:
                new_pc[og]={'clauses':buckets[og]}; found.append(og)
    elif slice and (slice.get('single_use') or slice.get('combo_use')):
        subs=slice.get('subtitles') or ['']
        pdl1_lines=(slice.get('pdl1') or '').split('\n')
        notes=slice.get('notes') or []
        buckets={}
        for u in ('single_use','combo_use'):
            for t in (slice.get(u) or []):
                if not t: continue
                for og in (item_organs(t,subs) or []):
                    buckets.setdefault(og,{'subtitles':[],'single_use':[],'combo_use':[],'pdl1':[],'notes':[]})[u].append(t)
        # subtitles / pdl1 / notes 依器官關鍵字過濾分到各器官
        kw={'肝癌':r'肝細胞癌','膽道癌':r'膽道癌|膽管','胰臟癌':r'胰臟癌|胰腺癌','胃癌':r'胃腺癌|胃癌'}
        for og in ORG_ORDER:
            if og not in buckets: continue
            b=buckets[og]
            b['subtitles']=[s for s in subs if re.search(kw[og],s)]
            b['pdl1']='\n'.join(l for l in pdl1_lines if re.search(kw[og],l)).strip()
            b['notes']=[n for n in notes if re.search(kw[og],n)]
            new_pc[og]=b; found.append(og)
    else:
        # per_cancer 無 HBPG（單器官藥，用 items 判定）
        found=[og for og in ORG_ORDER if og in (organs_of(items_text(d)) or [])] or ['胃癌']
    # 重建 cancers：把 HBPG 換成 found（保其他癌別原位）
    nc=[]
    for c in cancers:
        if c==HBPG: nc.extend(found)
        else: nc.append(c)
    d['cancers']=nc
    # 重建 per_cancer
    if isinstance(pc,dict):
        pc.pop(HBPG,None)
        pc.update(new_pc)

def main(path):
    html=open(path,encoding='utf-8').read()
    m=re.search(r'const DRUGS = (\[.*?\]);',html,re.S)
    DRUGS=json.loads(m.group(1))
    n=sum(1 for d in DRUGS if HBPG in (d.get('cancers') or []))
    if n==0:
        print('已無「肝膽胰胃癌」，跳過（冪等）。'); return
    for d in DRUGS: split_drug(d)
    newjson='const DRUGS = '+json.dumps(DRUGS,ensure_ascii=False,separators=(',',':'))+';'
    html2=html[:m.start()]+newjson+html[m.end():]
    # 更新 CANCERS 清單：肝膽胰胃癌 → 肝癌,膽道癌,胰臟癌,胃癌
    html2=html2.replace('"大腸直腸癌","肝膽胰胃癌","泌尿癌"','"大腸直腸癌","肝癌","膽道癌","胰臟癌","胃癌","泌尿癌"')
    open(path,'w',encoding='utf-8').write(html2)
    print(f'已拆分 {n} 支藥；DRUGS 總數 {len(DRUGS)}')

if __name__=='__main__':
    main(sys.argv[1] if len(sys.argv)>1 else 'index.html')
