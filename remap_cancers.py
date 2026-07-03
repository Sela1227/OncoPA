#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OncoPA 專用：把癌別對應到院內事審系統下拉（20 項，確認完整）。
在 split_hbpg.py 之後執行、冪等。
系統清單無：腎細胞癌/胰臟癌/白血病/多發性骨髓瘤/黑色素瘤等 → 一律歸「其他癌症」；喉癌 → 下咽癌。
"""
import re,sys,json,copy
RENAME=[('大腸直腸癌','結直腸癌'),('膽道癌','肝內膽管癌'),('其他癌','其他癌症')]
LYMPH=r'淋巴瘤|淋巴癌|NHL|DLBCL|濾泡性|濾泡型|被套細胞|MCL|何杰金|霍奇金|ALCL|CTCL|PTCL|巨球蛋白|PCNSL|邊緣區|Burkitt|B細胞淋巴|T細胞淋巴'
NONLYMPH=r'多發性骨髓|骨髓瘤|白血病|CML|AML|ALL|CLL|MDS|RAEB|骨髓纖維化|骨髓增生|MPD|Ph\+|GvHD|移植物抗宿主'
ORDER=['肺癌','乳癌','結直腸癌','肝癌','肝內膽管癌','胃癌','胃腸道間質瘤','攝護腺癌','膀胱癌','鼻咽癌','口腔癌','口咽癌','下咽癌','子宮頸癌','卵巢、腹膜、輸卵管','子宮體癌','甲狀腺惡性腫瘤','食道癌','淋巴癌','其他癌症']

def clause_text(c):
    p=[c.get('header','') or '',c.get('_title','') or '']
    for si in (c.get('subitems') or []): p.append(si if isinstance(si,str) else (si.get('text') or si.get('header') or ''))
    return ' '.join(p)
def items_text(d): return ' '.join(clause_text(c) for c in (d.get('items') or []) if isinstance(c,dict))
def subCore(s): return re.sub(r'[（(][^）)]*[）)]','',s).strip()
def item_sub(t,subs):
    clean=t.replace('**','');m=re.search(r'\*\*(.+?)\*\*',t);label=(m.group(1) if m else '');hay=label+' '+clean[:40]
    for s in subs:
        core=subCore(s)
        if s and (s in hay or (core and core in hay)): return s
    return subs[0] if subs else ''
def is_immune(sl): return isinstance(sl,dict) and (sl.get('single_use') or sl.get('combo_use'))
def merge_slice(a,b):
    if not isinstance(a,dict): return copy.deepcopy(b)
    if not isinstance(b,dict): return a
    if not is_immune(a) and not is_immune(b):
        a['clauses']=(a.get('clauses') or [])+(b.get('clauses') or []); return a
    for k in ('subtitles','single_use','combo_use','notes'):
        a[k]=(a.get(k) or [])+(b.get(k) or [])
    pa=(a.get('pdl1') or '').strip();pb=(b.get('pdl1') or '').strip()
    a['pdl1']=pa+('\n' if pa and pb else '')+pb
    return a
def put(pc,tgt,ns): pc[tgt]=merge_slice(pc[tgt],ns) if tgt in pc else copy.deepcopy(ns)

def classify(text,rules,residual):
    for tgt,kw in rules:
        if re.search(kw,text,re.I): return tgt
    return residual

def split_by(d,src,rules,residual):
    """一 clause/item → 單一目標；per_cancer 空則用 items（可多命中）"""
    pc=d.get('per_cancer')
    if isinstance(pc,dict) and src in pc:
        sl=pc.pop(src); parts={}
        if is_immune(sl):
            subs=sl.get('subtitles') or ['']; pdl1=(sl.get('pdl1') or '').split('\n'); notes=sl.get('notes') or []
            for u in ('single_use','combo_use'):
                for t in (sl.get(u) or []):
                    if not t: continue
                    tgt=classify(item_sub(t,subs),rules,residual)
                    parts.setdefault(tgt,{}).setdefault(u,[]).append(t)
            for tgt in list(parts.keys()):
                parts[tgt]['subtitles']=[s for s in subs if classify(s,rules,residual)==tgt]
                parts[tgt]['pdl1']='\n'.join(l for l in pdl1 if l.strip() and classify(l,rules,residual)==tgt).strip()
                parts[tgt]['notes']=[n for n in notes if classify(n,rules,residual)==tgt]
        else:
            for c in (sl.get('clauses') or []):
                parts.setdefault(classify(clause_text(c),rules,residual),{'clauses':[]})['clauses'].append(c)
        for tgt,ns in parts.items(): put(pc,tgt,ns)
        found=list(parts.keys())
    else:
        found=[t for t,kw in rules if re.search(kw,items_text(d),re.I)] or [residual]
    nc=[]
    for c in (d.get('cancers') or []):
        if c==src:
            for x in [t for t in ORDER if t in found]:
                if x not in nc: nc.append(x)
        elif c not in nc: nc.append(c)
    d['cancers']=nc

def split_headneck(d):
    """頭頸→鼻咽/口腔/口咽/下咽（喉→下咽）；通用頭頸鱗癌→口腔+口咽+下咽（不含鼻咽）"""
    SUB=[('鼻咽癌',r'鼻咽'),('口腔癌',r'口腔'),('口咽癌',r'口咽'),('下咽癌',r'下咽|喉')]
    GEN=['口腔癌','口咽癌','下咽癌']
    def subsites(text):
        s=[]
        if re.search(r'鼻咽',text) and not re.search(r'不含[^）)]*鼻咽|除外[^）)]*鼻咽',text): s.append('鼻咽癌')
        if re.search(r'口腔',text): s.append('口腔癌')
        if re.search(r'口咽',text): s.append('口咽癌')
        if re.search(r'下咽|喉',text): s.append('下咽癌')
        if not s and re.search(r'頭頸|鱗',text): s=GEN[:]
        return s or GEN[:]
    pc=d.get('per_cancer'); src='頭頸癌'
    targets=set()
    if isinstance(pc,dict) and src in pc:
        sl=pc.pop(src)
        if is_immune(sl):
            subs=sl.get('subtitles') or ['']; pdl1=(sl.get('pdl1') or '').split('\n'); notes=sl.get('notes') or []
            buck={}
            for u in ('single_use','combo_use'):
                for t in (sl.get(u) or []):
                    if not t: continue
                    for tg in subsites(item_sub(t,subs)): buck.setdefault(tg,{}).setdefault(u,[]).append(t)
            for tg in buck:
                buck[tg]['subtitles']=[s for s in subs if tg in subsites(s)]
                buck[tg]['pdl1']='\n'.join(l for l in pdl1 if l.strip() and tg in subsites(l)).strip()
                buck[tg]['notes']=[n for n in notes if tg in subsites(n)]
            for tg,ns in buck.items(): put(pc,tg,ns); targets.add(tg)
        else:
            buck={}
            for c in (sl.get('clauses') or []):
                for tg in subsites(clause_text(c)): buck.setdefault(tg,{'clauses':[]})['clauses'].append(c)
            for tg,ns in buck.items(): put(pc,tg,ns); targets.add(tg)
    else:
        for tg in subsites(items_text(d)): targets.add(tg)
    nc=[]
    for c in (d.get('cancers') or []):
        if c==src:
            for x in [t for t in ORDER if t in targets]:
                if x not in nc: nc.append(x)
        elif c not in nc: nc.append(c)
    d['cancers']=nc

def split_blood(d):
    src='血液淋巴癌'; pc=d.get('per_cancer'); found=set()
    if isinstance(pc,dict) and src in pc:
        sl=pc.pop(src)
        if is_immune(sl):
            subs=sl.get('subtitles') or ['']; pdl1=(sl.get('pdl1') or '').split('\n'); notes=sl.get('notes') or []
            buck={}
            cl=lambda t:'淋巴癌' if re.search(LYMPH,t) else '其他癌症'
            for u in ('single_use','combo_use'):
                for t in (sl.get(u) or []):
                    if not t: continue
                    buck.setdefault(cl(item_sub(t,subs)),{}).setdefault(u,[]).append(t)
            for tg in buck:
                buck[tg]['subtitles']=[s for s in subs if cl(s)==tg]
                buck[tg]['pdl1']='\n'.join(l for l in pdl1 if l.strip() and cl(l)==tg).strip()
                buck[tg]['notes']=[n for n in notes if cl(n)==tg]
            for tg,ns in buck.items(): put(pc,tg,ns); found.add(tg)
        else:
            buck={}
            for c in (sl.get('clauses') or []):
                tg='淋巴癌' if re.search(LYMPH,clause_text(c)) else '其他癌症'
                buck.setdefault(tg,{'clauses':[]})['clauses'].append(c)
            for tg,ns in buck.items(): put(pc,tg,ns); found.add(tg)
    else:
        it=items_text(d)
        if re.search(LYMPH,it): found.add('淋巴癌')
        if re.search(NONLYMPH,it) or not found: found.add('其他癌症')
    nc=[]
    for c in (d.get('cancers') or []):
        if c==src:
            for x in [t for t in ORDER if t in found]:
                if x not in nc: nc.append(x)
        elif c not in nc: nc.append(c)
    d['cancers']=nc

def main(path):
    html=open(path,encoding='utf-8').read()
    m=re.search(r'const DRUGS = (\[.*?\]);',html,re.S); DRUGS=json.loads(m.group(1))
    # 1) 改名
    for d in DRUGS:
        d['cancers']=[dict(RENAME).get(c,c) for c in (d.get('cancers') or [])]
        pc=d.get('per_cancer')
        if isinstance(pc,dict):
            for old,new in RENAME:
                if old in pc: put(pc,new,pc.pop(old))
        if d.get('st'):
            for old,new in RENAME: d['st']=d['st'].replace(old,new)
    # 2) 其他癌症 碎出 GIST/甲狀腺（先做，趁尚未併入其他東西）
    for d in DRUGS:
        if '其他癌症' in (d.get('cancers') or []):
            split_by(d,'其他癌症',[('胃腸道間質瘤',r'胃腸道間質瘤|GIST'),('甲狀腺惡性腫瘤',r'甲狀腺')],'其他癌症')
    # 3) 婦癌 拆
    for d in DRUGS:
        if '婦癌' in (d.get('cancers') or []):
            split_by(d,'婦癌',[('子宮頸癌',r'子宮頸'),('子宮體癌',r'子宮體|子宮內膜'),('卵巢、腹膜、輸卵管',r'卵巢|輸卵管|腹膜')],'卵巢、腹膜、輸卵管')
    # 4) 泌尿癌 拆：攝護腺/膀胱；腎細胞→其他癌症
    for d in DRUGS:
        if '泌尿癌' in (d.get('cancers') or []):
            split_by(d,'泌尿癌',[('攝護腺癌',r'攝護腺|前列腺|CRPC|CSPC|去勢'),('膀胱癌',r'泌尿道上皮')],'其他癌症')
    # 5) 胰臟癌 → 其他癌症
    for d in DRUGS:
        if '胰臟癌' in (d.get('cancers') or []):
            split_by(d,'胰臟癌',[],'其他癌症')
    # 6) 血液淋巴癌 → 淋巴癌 / 其他癌症（clause 逐條、items 多目標）
    for d in DRUGS:
        if '血液淋巴癌' in (d.get('cancers') or []):
            split_blood(d)
    # 7) 頭頸癌 → 口腔/口咽/下咽（喉→下咽）
    for d in DRUGS:
        if '頭頸癌' in (d.get('cancers') or []):
            split_headneck(d)
    # 8) CANCERS
    present=set(c for d in DRUGS for c in (d.get('cancers') or []))
    newC=[c for c in ORDER if c in present]+[c for c in present if c not in ORDER]
    newjson='const DRUGS = '+json.dumps(DRUGS,ensure_ascii=False,separators=(',',':'))+';'
    html2=html[:m.start()]+newjson+html[m.end():]
    html2=re.sub(r'const CANCERS = \[[^\]]*\];','const CANCERS = '+json.dumps(newC,ensure_ascii=False)+';',html2)
    open(path,'w',encoding='utf-8').write(html2)
    print('完成；DRUGS',len(DRUGS));print('CANCERS =',newC)

if __name__=='__main__': main(sys.argv[1] if len(sys.argv)>1 else 'index.html')
