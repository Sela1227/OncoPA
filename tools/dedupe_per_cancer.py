#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OncoPA 單一來源化（接母程式匯入 / 資料更新後執行、冪等）：
把多癌別藥的 per_cancer[cancer].clauses（clause 物件）轉為「引用 items 索引」，
消除同一條文在 items 與 per_cancer 重複儲存造成的 drift（審稿架構#3）。

模型：per_cancer[cancer].clauses 之元素可為
  - 整數 n            → 用 items[n]（含其 _title）
  - {"ref":n}         → 同上
  - {"ref":n,"_title":"…"} → 用 items[n] 文字，但以癌別專屬 _title 覆寫顯示
  - （向下相容）完整 clause 物件 → 原樣使用（尚未轉引用者）

安全策略：只轉「per_cancer clause 文字能在 items 精確匹配」者；
文字與 items 有出入的藥（需內容裁定）一律**跳過並列報**，不自動猜。
immune 形狀（single_use/combo_use）非 items 重複，不動。

用法：python3 tools/dedupe_per_cancer.py index.html
"""
import re,sys,json

def norm(s): return re.sub(r'\s+','',str(s or ''))

def clause_key(c):
    return norm(c.get('header'))+ '\u0001' + norm(''.join(
        (si.get('text') or '') for si in (c.get('subitems') or []) if isinstance(si,dict)))

def main(path='index.html'):
    h=open(path,encoding='utf-8').read()
    m=re.search(r'const DRUGS = (\[.*?\]);',h,re.S)
    DRUGS=json.loads(m.group(1))
    conv=0; drugs_conv=0; skipped=[]
    for d in DRUGS:
        pc=d.get('per_cancer')
        if not isinstance(pc,dict): continue
        items=[c for c in (d.get('items') or []) if isinstance(c,dict)]
        ikey={clause_key(c):i for i,c in enumerate(items)}
        drug_touched=False
        for cancer,sl in pc.items():
            if not isinstance(sl,dict) or not sl.get('clauses'): continue
            # 先確認整條 slice 都能精確匹配，否則整支跳過（保守）
            newrefs=[]; ok=True
            for c in sl['clauses']:
                if isinstance(c,(int,float)) or (isinstance(c,dict) and 'ref' in c):
                    newrefs.append(c); continue   # 已是引用
                idx=ikey.get(clause_key(c))
                if idx is None: ok=False; break
                it=items[idx]
                if (c.get('_title') or '')!=(it.get('_title') or ''):
                    newrefs.append({'ref':idx,'_title':c.get('_title')})
                else:
                    newrefs.append({'ref':idx})
            if not ok:
                skipped.append((d['num'],cancer)); continue
            if newrefs and any(not(isinstance(x,dict) and 'ref' in x and len(x)<=2) for x in sl['clauses']):
                sl['clauses']=newrefs; conv+=len(newrefs); drug_touched=True
        if drug_touched: drugs_conv+=1
    newjson='const DRUGS = '+json.dumps(DRUGS,ensure_ascii=False,separators=(',',':'))+';'
    open(path,'w',encoding='utf-8').write(h[:m.start()]+newjson+h[m.end():])
    print(f'轉引用：{drugs_conv} 支藥、{conv} 條 clause')
    if skipped:
        print(f'跳過（per_cancer 與 items 文字有出入，需內容裁定）：{len(set(x[0] for x in skipped))} 支')
        for num,cancer in skipped: print(f'  ⏭ {num} [{cancer}]')

if __name__=='__main__':
    main(sys.argv[1] if len(sys.argv)>1 else 'index.html')
