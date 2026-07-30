# OncoPA 獨立更新流程（健保第九節改版 SOP）

> **定位**：OncoPA 已與母程式（Cancer Drug 速查系統）**脫離**——執行期零相依（DRUGS 內嵌於 index.html）、資料維護自足。
> 本文件把「一次健保第九節改版」的完整步驟固化，讓任何一次改版都能照著走，不需等母程式重生。
>
> **與母程式的關係**：不是建置相依，而是「定期對帳夥伴」。每次改版兩邊各自更新後，比對「需事審藥清單」與 `pre_review` 標記是否一致（互相獨立抽取＝防錯）。唯一向母程式借東西的場景：某藥**新變成需事審**時，去母程式撈它已驗證的完整條文當底稿，省一次乾淨抽取。

---

## 前置：環境與輸入

工作區重置後先還原（坑：環境會在回合間重置）：

```bash
cd /home/claude/oncopa 2>/dev/null && ls OncoPA/index.html >/dev/null 2>&1 \
  || { mkdir -p /home/claude/oncopa && cd /home/claude/oncopa && unzip -q "/mnt/user-data/outputs/OncoPA V<最新版>.zip"; }
```

需要的輸入：
- **新版官方 PDF**：`chap9_<新日期>.pdf`（健保署「最新版藥品給付規定內容(分章節)」第九節）
- **舊版官方 PDF**：即目前 OncoPA data-date 對應的版本（用來 diff）
- （選配）母程式的改版差異說明，用來**對帳**，不是唯一依據

---

## 步驟 1：抽取兩版 PDF 文字

PDF 有兩種型態，先偵測：

```bash
file <pdf>
# "PDF document" → 真 PDF，用 pdfplumber
# "Zip archive"  → zip 偽裝（母程式來源檔常見），用 unzip 取每頁 txt
```

**真 PDF**：

```python
import pdfplumber
with pdfplumber.open('新版.pdf') as pdf:
    open('/tmp/新版.txt','w').write(''.join((p.extract_text() or '')+'\n' for p in pdf.pages))
```

**zip 偽裝**：

```bash
mkdir -p /tmp/old && cd /tmp/old && unzip -o -q <舊版.pdf>   # 得到 1.txt 2.txt …（每頁）
```

```python
import glob, re
files = sorted(glob.glob('/tmp/old/*.txt'), key=lambda p:int(re.search(r'(\d+)\.txt',p).group(1)))
open('/tmp/old.txt','w').write(''.join(open(f,encoding='utf-8',errors='ignore').read()+'\n' for f in files))
```

⚠️ 抽取後清跨頁頁碼標記（會夾進日期串裡）：`re.sub(r'第\s*9\s*節\s*[-－]\s*\d+','',text)`。

---

## 步驟 2：兩層 diff（坑 #38 — 缺一不可）

**只比藥號會漏掉既有藥的內文修改。** 必須同時比：

1. **藥號層**：新增／刪除的 `9.xxx`
2. **內文層**：既有藥號的條文字數／內容變動

```python
import re
def drugmap(t):
    parts=re.split(r'(?=9\.\d+(?:\.\d+)?[ 　\.、]?\s*[A-Za-z（(])',t)
    d={}
    for p in parts:
        m=re.match(r'\s*(9\.\d+(?:\.\d+)?)',p)
        if m: d[m.group(1)]=d.get(m.group(1),'')+re.sub(r'\s+','',p)
    return d
o,n=drugmap(open('/tmp/old.txt').read()), drugmap(open('/tmp/新版.txt').read())
def sk(x):ps=x[2:].split('.');return(int(ps[0]),int(ps[1]) if len(ps)>1 else 0)
print('新增:',sorted(set(n)-set(o),key=sk))
print('刪除:',sorted(set(o)-set(n),key=sk))
for num in sorted(set(o)&set(n),key=sk):
    if o[num] and abs(len(n[num])-len(o[num]))>15 and abs(len(n[num])-len(o[num]))/len(o[num])>0.03:
        print(f'  內文變動 {num}: {len(o[num])}→{len(n[num])}')
```

---

## 步驟 3：篩出 OncoPA 要處理的藥

OncoPA 只收**需事審**藥。把 diff 結果對到目前 DRUGS：

```python
import json
h=open('index.html',encoding='utf-8').read()
onco={d['num'] for d in json.loads(re.search(r'const DRUGS = (\[.*?\]);',h,re.S).group(1))}
# 變動藥中，哪些在 onco 裡 → 要改；新增藥 → 判斷是否需事審再決定加不加
```

判準：條文含「須經事前審查核准後使用」即需事審。新增的需事審藥**務必設 `pre_review:True`**（母程式曾漏設，見 115.7.23 的 9.137/9.138）。

---

## 步驟 4：套用變更

- **新藥**：依 [DRUGS schema](#drugs-schema) 建物件，`cancers`／`types`／`pre_review`／`items`（header＋subitems，`_title` 為卡片短標）／`per_cancer`（單癌別設 null）／`common_data`／`st`。逐字對 PDF，勿改寫。
- **既有藥內文更新**：以最小改動精準改對應 subitem；結構性大改（如新增整段適應症）才重建 items。
- **品牌／品項清單**（坑 #40）：同藥不同情境常用**不同品項清單**——查官方各情境前文，勿一律套用。例：9.69 pemetrexed 術前輔助限 3 項、轉移性非鱗狀第一線限 4 項（含 Alimta Avos）。
- **新增癌別**：若某藥帶進新癌別，同步加進 `const CANCERS`（對齊醫院 NHOS3001 下拉順序）。

每次改完該藥都要重建它的 `st`（搜尋索引，全小寫、空白正規化）。

---

## 步驟 5：跑清理工具（可重跑、冪等）

```bash
python3 tools/normalize_clauses.py index.html /tmp/新版.txt
```

自動處理：**截斷條文補完**（尾端或句中未閉合日期串，以官方 PDF 定位）＋**詞內空格清理**（治 療→治療）＋重建 st。

接著跑單一來源化（把多癌別藥 per_cancer 的純切片 clause 轉為引用 items 索引，防 items/per_cancer drift）：

```bash
python3 tools/dedupe_per_cancer.py index.html
```

冪等；會**列報** per_cancer 與 items 文字有出入的藥（需內容裁定，勿自動猜）。這支也是 drift 守門員——若某次更新只改了 items 沒改 per_cancer 副本，它會抓出來。目前 9.27/9.37 結直腸癌為刻意保留的結構性精修視圖（items 以「治療部分」母標分組、per_cancer 攤平成獨立卡），非 drift。

---

## 步驟 6：驗證套件（每次必跑）

```python
import re, json
h=open('index.html',encoding='utf-8').read()
D=json.loads(re.search(r'const DRUGS = (\[.*?\]);',h,re.S).group(1))       # JSON 可解析
print('DRUGS', len(D), 'CANCERS', len(re.search(r'const CANCERS = (\[[^\]]*\]);',h).group(1).split(',')))
# 每個非 text/plain 的 <script> 都要過 node --check
for i,m in enumerate(re.finditer(r'<script(?![^>]*type="text/plain")[^>]*>(.*?)</script>',h,re.S)):
    open(f'/tmp/j{i}.js','w').write(m.group(1))
```

```bash
for f in /tmp/j*.js; do node --check "$f" || echo "✗ $f 語法錯"; done
```

發布前擋版檢查（審稿建議）：
- 全庫無殘留截斷：`[（(][0-9/、\s]*、\s*(?=[ⅠI]\.|$)` 命中數應為 0
- 全庫無詞內空格：`[\u4e00-\u9fff]\s+[\u4e00-\u9fff]` 命中數應為 0
- `pre_review` 標記齊全（需事審藥都有）
- 藥名拼字掃描（發現一處錯字順勢全表掃，坑 #36）

⚠️ **改 WIZARD 文字時**：Python 寫進 JS 單引號字串的換行要寫 `\\n`（寫成 `\n` 會變真換行破壞 JS，坑 #35）。由 `node --check` 攔截。

---

## 步驟 7：版本同步（四處，鐵律）

只有 `c` 逢十進位，`a`／`b` 無上限。`data-date` 只在藥品資料變動時改。

| # | 位置 | 內容 |
|---|---|---|
| 1 | index.html gate `<h1>` span | `v0.x.y` |
| 2 | index.html `.ver-badge` | `data-version=` ＋顯示字 |
| 3 | index.html `.brand-version` | `data-date=`（資料變動時）|
| 4 | CLAUDE.md 當前狀態＋版本歷程表 | 版本行＋新增一列 |
| 5 | SELA-handoff.md 完成版本 | 版本行 |

CLAUDE.md 版本歷程那列要寫清楚：**改了什麼、為什麼、踩到什麼坑**。

---

## 步驟 8：打包與交付

```bash
cd /home/claude/oncopa && rm -f "OncoPA V0.x.y.zip" && zip -rq "OncoPA V0.x.y.zip" OncoPA -x "*.DS_Store"
cp "OncoPA V0.x.y.zip" /mnt/user-data/outputs/ && cp OncoPA/index.html /mnt/user-data/outputs/
```

用 present_files 交付 zip（給 Git Pusher）＋ index.html（預覽）。zip 檔名格式：`OncoPA V<版本>.zip`（**有空格、版本含點**）。

---

## 步驟 9：與母程式對帳（防錯，非相依）

兩邊各自更新後比對：
- **需事審藥清單**是否一致
- **`pre_review` 標記**是否一致
- 有出入 → 回查官方條文，找出誰對

對得上 = 兩份獨立抽取互相佐證，信心提高。對不上 = 至少一邊有誤，及早抓到。

---

<a name="drugs-schema"></a>
## 附錄：DRUGS schema

```javascript
{
  num:"9.137", name:"Cabazitaxel", brand:"Cabazred",
  cancers:["攝護腺癌"],            // 對齊 CANCERS / NHOS3001 下拉
  types:["化療"], pre_review:true, form_no:"",
  items:[                          // 主條文（單癌別藥放這裡）
    { num:"1", header:"…", subitems:[{num:"(1)",text:"…"}], _title:"卡片短標" }
  ],
  per_cancer:null,                 // 多癌別藥才用；單癌別設 null（走 items）
  common_data:[],
  st:"…"                           // 搜尋索引（全小寫、空白正規化，改完必重建）
}
```

多癌別藥的 `per_cancer` 有兩種形狀：一般用 `.clauses[]`；免疫藥（如 9.69）用 `subtitles/single_use/combo_use/pdl1/notes`。

---

## 附錄：脫離後可自主的架構升級（原「待母程式」三項）

因 DRUGS 不再被母程式重生覆寫，以下三項現在可在 OncoPA 自己做：

1. **單一來源條文模型**：`clauses:{ "9.69-2-10":{...} }` ＋ `per_cancer:{ "子宮體癌":["9.69-2-10"] }`（各癌別存引用、不複製全文），消除 items／per_cancer／st 重複。
2. **per-clause metadata**：`sourceVersion`／`effectiveDate`／`sourceClauseId`，支援追溯與「版本落後官方」警示。
3. **isAdminClause 原子化**：把「適應症 vs 共通限制」拆成帶 `appliesTo` 的原子規則，根治「適應症限制被誤套為共通規定」。

三者同源（都需 clause 級 ID），建議依序做：先 1 建立 clause 物件與 ID，2、3 順勢完成。
