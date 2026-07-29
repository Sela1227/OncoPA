#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OncoPA 資料清理（接母程式 PDF 匯入後執行、冪等）：
  A) 截斷條文補完：clause 尾端未閉合的日期串（如「（105/11/1、」）依官方 PDF 補完整。
  B) 詞內空格清理：移除兩個中文字之間的 PDF 換行殘留空格（如「治 療」→「治療」）。
用法：python3 tools/normalize_clauses.py index.html /path/to/chap9_new.txt
"""
import re,sys,json

def strip_ws(s): return re.sub(r'\s+','',s)

def load_pdf(path):
    raw=open(path,encoding='utf-8').read()
    raw=re.sub(r'第\s*9\s*節\s*[-－]\s*\d+','',raw)  # 清跨頁頁碼標記
    return strip_ws(raw)

def all_text_slots(d):
    """回傳 (取值函式, 設值函式) 清單，涵蓋 header/_title/subitems/單複用/notes"""
    slots=[]
    def add(container,key):
        slots.append((lambda:container[key], lambda v:container.__setitem__(key,v)))
    for c in (d.get('items') or []):
        if not isinstance(c,dict): continue
        for k in ('header','_title'):
            if c.get(k) is not None: add(c,k)
        for si in (c.get('subitems') or []):
            if isinstance(si,dict) and si.get('text') is not None: add(si,'text')
    pc=d.get('per_cancer')
    if isinstance(pc,dict):
        for sl in pc.values():
            if not isinstance(sl,dict): continue
            for c in (sl.get('clauses') or []):
                if not isinstance(c,dict): continue
                for k in ('header','_title'):
                    if c.get(k) is not None: add(c,k)
                for si in (c.get('subitems') or []):
                    if isinstance(si,dict) and si.get('text') is not None: add(si,'text')
            for u in ('single_use','combo_use','notes'):
                arr=sl.get(u)
                if isinstance(arr,list):
                    for i in range(len(arr)):
                        if isinstance(arr[i],str):
                            add_list=(lambda a,idx:(lambda:a[idx],lambda v:a.__setitem__(idx,v)))(arr,i)
                            slots.append(add_list)
    return slots

def complete_truncation(t,pdf):
    """若 t 尾端為未閉合日期串，回傳補完後字串，否則原樣。
    以「錨點＋起始日期」定位；即使 PDF 多處出現，只要補完結果唯一即採用。"""
    m=re.search(r'[（(]([0-9/、\s]*?)$',t)
    if not m: return t,False
    partial=strip_ws(m.group(1))
    if not re.search(r'\d',partial): return t,False
    prefix=strip_ws(t[:m.start()])
    pk=partial.rstrip('、')
    def collect(anchor):
        comps=set();start=0
        while True:
            pos=pdf.find(anchor,start)
            if pos<0: break
            start=pos+1
            fm=re.match(r'[（(]([0-9/、]+)[）)]',pdf[pos+len(anchor):])
            if fm and fm.group(1).startswith(pk): comps.add(fm.group(1))
        return comps
    # 完整前綴優先（最精確），再逐步退回較短錨點
    for alen in (len(prefix),40,24):
        anchor=prefix[-alen:]
        if len(anchor)<8: continue
        comps=collect(anchor)
        if len(comps)==1:
            return t[:m.start()]+'（'+comps.pop()+'）',True
    return t,False

def clean_spaces(t):
    """移除中文字之間的空格。"""
    prev=None
    while prev!=t:
        prev=t
        t=re.sub(r'([\u4e00-\u9fff])[ \t]+([\u4e00-\u9fff])',r'\1\2',t)
    return t

def rebuild_st(d):
    parts=[d.get('name','').lower(),(d.get('brand') or '').lower()]
    def cl(c):
        if c.get('header'): parts.append(c['header'])
        for si in (c.get('subitems') or []):
            parts.append(si if isinstance(si,str) else (si.get('text') or ''))
    for c in (d.get('items') or []):
        if isinstance(c,dict): cl(c)
    pc=d.get('per_cancer')
    if isinstance(pc,dict):
        for sl in pc.values():
            if not isinstance(sl,dict): continue
            for c in (sl.get('clauses') or []):
                if isinstance(c,dict): cl(c)
            for u in ('single_use','combo_use','notes'):
                parts += [x for x in (sl.get(u) or []) if isinstance(x,str)]
            parts += sl.get('subtitles') or []
    d['st']=re.sub(r'\s+',' ',' '.join(parts)).lower()

def main(html_path,pdf_txt):
    h=open(html_path,encoding='utf-8').read()
    m=re.search(r'const DRUGS = (\[.*?\]);',h,re.S)
    DRUGS=json.loads(m.group(1))
    pdf=load_pdf(pdf_txt)
    n_trunc=0;n_space=0
    for d in DRUGS:
        for get,setv in all_text_slots(d):
            t=get()
            if not isinstance(t,str): continue
            t2,fixed=complete_truncation(t,pdf)
            if fixed: n_trunc+=1
            t3=clean_spaces(t2)
            if t3!=t2: n_space+=1
            if t3!=t: setv(t3)
        rebuild_st(d)
    newjson='const DRUGS = '+json.dumps(DRUGS,ensure_ascii=False,separators=(',',':'))+';'
    open(html_path,'w',encoding='utf-8').write(h[:m.start()]+newjson+h[m.end():])
    print(f'截斷條文補完 {n_trunc} 處；詞內空格清理 {n_space} 個欄位')

if __name__=='__main__':
    main(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else '/tmp/新版.txt')
