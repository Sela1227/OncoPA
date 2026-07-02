# CLAUDE.md — 癌藥事審送審準備工具

> **這份是給下次 Claude 看的工作上下文，不是文件。**
> 維護章法：`SELA-Starter-Kit/conventions/CLAUDE-MD-章法.md`，每次升版前複習。
> 每升一版至少更新三處：踩過的坑、版本歷程、下版候選工作。

---

## 〇、當前狀態

- **版本：** V0.23.2（資料日期 115.6.23；登入改明碼＋預留醫令代碼欄位）
- **英文名／識別：** **OncoPA**（Onco + Prior-Authorization）
- **命名（雙語）：** 資料夾／zip 檔名用英文 `OncoPA`（Kit 英文名鐵律）；**程式內顯示維持中文「癌藥事審・送審準備」**（SELA 指定）。下個 Claude 別「好心」把顯示改成英文。
- **三層目標歸屬：** 醫院發展（院內個管事審作業工具）為主；非對外分享、非純個人。
- **版本獨立：** 本工具版本自成一軌，**不對齊母程式（V4.x）**，亦不對齊 Kit 版本
- **app logo：** 走雙 logo 制（見第十節）；**正式 logo 已置入**（Gemini 依 `SELA-logo-prompt.md` 生成、Claude 走 §10.2 四步轉檔）。logo 文字為「CB Show」
- **狀態：** 獨立純靜態工具，功能完整、已對齊 SELA Kit
- **一句話定位：** 醫師已決定送審某抗癌藥時，協助個管師「找對給付條文 → 複製 → 備齊送審資料」的速查工具。
- **技術棧：** 純 HTML + CSS + 原生 JS（單檔、無框架、無 build step）
- **入口點：** `index.html`
- **部署目標：** GitHub Pages（推 main，Settings → Pages 啟用）
- **通行碼：** `Sela`（前端 gate，非機密等級保護）
- **資料來源：** 母程式「健保癌症藥物速查系統」`index.html` 的 `const drugs`（見第八節更新流程）

---

## 一、技術棧決策（為什麼這樣選）

| 選擇 | 替代品 | 理由 |
|------|--------|------|
| 純 HTML+CSS+JS 單檔 | React/Vue | 無 build、雙擊可跑、Pages 直接 host、個管環境無 npm |
| 資料內嵌成 `const DRUGS` | 外部 fetch JSON | 單檔好分享、無 CORS／file:// 限制；更新靠重生（第八節） |
| 北歐霧藍配色（#436f8a/#2c4f66） | SELA 橘 | 醫療長時間使用、低視覺疲勞（colors.md 醫療系統建議） |
| 四頁式精靈（畫面切換） | 單長頁滾動 | 個管反饋：一次一焦點、有上一步，比長頁直覺 |

---

## 二、業務對映表（資料結構 ↔ 程式實作的單一真相）

> 資料來自母程式，schema 有三種形態，務必都支援：

| 業務概念 | 資料欄位 | 程式處理 |
|---------|---------|---------|
| 是否需事審 | `pre_review`（bool） | 只收 `true` 的藥（建置時過濾） |
| 事審附表編號 | `form_no` | 顯示在備料頁；多數藥為空 |
| 一般藥條文 | `items[]` 或 `per_cancer[癌別].clauses[]` | 每條 = 一張可選卡 |
| **免疫藥（9.69）** | `per_cancer[癌別].{single_use[],combo_use[],pdl1,notes[]}` | 依 `subtitles` 分子分型；單用/併用各一卡；`pdl1` 全表自選；`notes` 拆「文件要件 vs 注意事項」 |
| 通用給付規定 | `common_data[]`（**可能是字串或物件**） | `normClause()` 正規化；抽成「共通規定」參考區，不混入可選卡 |
| 搜尋索引 | `search_text` → 精簡為 `st` | 讓併用成分名（如 pembrolizumab）也搜得到 |
| 要備齊資料 | 由條文文字 + pdl1 + notes 關鍵字推斷 | `DOC_RULES` 比對；**輔助提醒、非官方對照**（免責聲明須保留） |

---

## 三、關鍵檔案路徑

| 想改什麼 | 動哪裡 |
|---------|-------|
| 藥物資料 | 不要手改 `index.html` 內 `const DRUGS`，走第八節從母程式重生 |
| 配色 | `index.html` `<style>` 的 `:root` |
| 版本/資料日期 | `.brand-version` 的 `data-version`/`data-date` 屬性 + 顯示文字（同步改） |
| 文件要件偵測 | `DOC_RULES` 陣列 |
| 免疫藥拆解邏輯 | `mkScenario()`、`buildCards()` 的 immuno 分支 |
| favicon | `favicon/`（SELA 標準套組，正常不動） |
| 病摘 AI Prompt 庫 | 內建 prompt 全文在 `<script type="text/plain" id="pl-builtin-gene">`；UI/邏輯在末段 `pl` IIFE（全 `pl-` 命名空間）。**新增全院共用 prompt → 加進 `builtins()`**；個管自訂存 localStorage（本機） |

---

## 四、踩過的坑（編號累積，永不重排）

0.5. **通用規定/敘述不可列為可選適應症（路由至共通規定）**
   - 症狀：母程式 items/clauses 把「事前審查程序、每日劑量上限、通則十二引用、療程上限」與「劑型標記【9.x.y…】」與真適應症並列，原樣渲染會讓它們變成「選出要送的那一條」的卡片。
   - 做法：`isAdminClause()` 偵測通用規定→併入 `cur.common`/`cur.commonG`（可勾選共通規定區，文字原樣保留、僅改分類）；`_is_source_marker`→渲染為非點選分隔標題、真適應症重新編號。
   - 保守原則＋安全網：判別式要求「無適應症訊號(IND)」才歸為事前審查類；且**移走後該藥/癌別不得變 0 適應症**（改動後必驗）。劑量/通則/療程上限以行首樣式嚴格比對，避免誤抓含這些字的真適應症。

0. **萃取內容（標題）只進畫面，永不進入送審/複製內容（資料完整性鐵律）**
   - `clauseTitle()` 是顯示用的萃取摘要，可能不夠精準；它只用於收合卡標題與 prep 標題顯示。
   - `copyText` 複製到送審單的內容，只能是「藥名（編號）癌別 + 原始條文 `c.text`（=`clauseText` 逐字 header+子項）」，**禁止**夾帶 `clauseTitle` 等任何萃取/改寫文字。
   - 免疫情境卡可保留 `c.label`，因其來自母程式原文 `**標記**`（非萃取）、且 `c.text` 已去標籤。
   - `clauseTitle()` 必須為純函式：只讀 `c.header`/`c.subitems`，不得寫回 `c`。改動後以 417 卡跑「不動原物件 / 複製精確全等於 識別行+原文」驗證。

1. **Python 注入資料用 `re.sub` 毀損內容**
   - 症狀：注入後 `const DRUGS` 解析失敗、出現非法控制字元
   - 原因：`re.sub` 把替換字串裡的 `\u`、`\\` 當跳脫處理
   - 做法：一律用純字串 `str.replace()` 注入，禁用 `re.sub`

2. **免疫藥 9.69 的 `common_data` 是字串陣列，不是物件**
   - 症狀：通用條款卡 `c.header` 為 undefined、卡片爆掉
   - 原因：母程式對 9.69 的通用規定存成 `["...","..."]`
   - 做法：`normClause(c)` 統一吃字串/物件，回 `{header,subitems}`

3. **ER/PR 文件偵測誤判**
   - 症狀：interferon、proper、performance 等字被當成要附 ER/PR 報告
   - 原因：正規式用裸 `ER`/`PR` 比對
   - 做法：改用「雌激素/荷爾蒙受體/ER、PR/接受體陽性」等明確上下文

4. **免疫成分名搜不到**
   - 症狀：搜 pembrolizumab／Keytruda 無結果
   - 原因：成分名集中在 9.69 一筆，不在 name/brand；精簡時又把 search_text 拿掉了
   - 做法：保留精簡搜尋索引 `st`（含併用成分名），name/brand 命中優先排序

5. **限制/條件條文被 IND 正規式「救回」成假適應症（admin 漏抓）**
   - 症狀：「X 不得合併使用」「僅得擇一給付」「使用前須接受…」「總療程以…上限」等純限制句，被當成可選適應症卡顯示（V0.15.0 全癌別策展時，逐條審核揪出 25 條）。
   - 原因：`is_admin`/`isAdminClause` 的多數規則以 `not IND` 為前提；但 IND 含 `與[^。]{1,30}?(?:併用|合併使用)`，會把「與 Y 不得合併使用」也判為有適應症訊號，使 admin 守則失效。OCR 又在「僅 得擇一給付」插空格、條尾帶日期戳 `（98/6/1、`，讓精確比對落空。
   - 做法：在 `ADMIN_PATTERNS`（**不經 IND 守門**的 `ADMIN_RE` 迴圈）補錨定式精確樣式（`^不得與.{1,50}(?:合併使用|併用)`、`僅\s*得擇一給付`(容忍 OCR 空格)、`^總療程以\d`、`每日至多給付`…）。**鐵律：build.py 的 `ADMIN_PATTERNS` 必與 index.html 的 JS `isAdminClause` 內 `ADMIN_RE` 逐條同步**（用 build.py 自動產生 JS regex literal，避免兩端漂移）。補規則後必跑驗證：coverage 缺漏=0、無藥/癌別變 0 適應症（保守原則）。安全網案例見策展腳本註解（9.65 Pralatrexate「每人至多給付」歸 admin 但 PTCL 適應症須留、9.68 Radium intro 留適應症、9.38 Temsirolimus header 像 admin 但 subitems 含 IND 守住、9.56 Brentuximab「限用於成人患者:」歸 admin）。

6. **DOC_RULES 腎功能規則 `/i` 讓基因 EGFR 誤觸 eGFR（標靶藥假叫附腎功能）**
   - 症狀：bevacizumab/regorafenib/panitumumab/cabozantinib/osimertinib/larotrectinib/amivantamab/encorafenib/fruquitinib 等 9 支 EGFR 相關標靶藥，「要備齊的資料」冒出「腎功能檢驗值」，但原條文無任何腎功能要求（個管師反映）。
   - 原因：`DOC_RULES` 腎功能條 `/(eGFR|CCr|腎功能)/i` 帶 `/i`；癌基因 **EGFR**（大寫）與腎功能 **eGFR**（小寫 e）只差大小寫，不分大小寫即誤判。**與坑 #12 同源**（clauseTitle 已修區分大小寫，DOC_RULES 當時漏修）。
   - 做法：移除該條 `/i`，eGFR 只配小寫 e（不再中 EGFR）；同時把真腎功能變體用字元類補齊避免漏抓：`/(eGFR|[Cc][Cc]r|[Cc]r[Cc]l|腎功能|腎絲球|肌酸酐|[Cc]reatinine)/`。驗證：9 支 EGFR 假陽性消失；cetuximab（頭頸癌 Ccr<50）、carfilzomib(CrCl)、骨髓瘤群(eGFR/腎功能) 等真腎功能藥仍正確觸發。**基因/生物標記規則 `/(EGFR|ALK…)/i` 不動**，EGFR 藥仍正確要「基因／生物標記檢測報告」。
   - 通則：DOC_RULES 任何「短英文縮寫＋/i」都要查是否與基因/生物標記縮寫撞（eGFR↔EGFR、CR↔…），縮寫類規則優先用區分大小寫＋字元類涵蓋變體。

7. **基因／生物標記從「通用標籤」改為「具名萃取」——latin token 的子字串與前治療脈絡會誤判**
   - 背景：個管師反映「基因／生物標記檢測報告」太籠統，需指明哪個基因、哪個生物標記。改用 `geneDocs()／markerDocs()` 具名萃取。
   - 踩到的坑：
     a. **VEGFR 子字串**：`EGFR` 未加 `\b` 會吃到 `VEGFR`（cabozantinib 甲狀腺癌假陽性）→ 一律 `\bEGFR\b`，所有 latin gene token 都加 `\b`／區分大小寫（同坑 #6 eGFR 精神）。
     b. **anti-EGFR 前治療脈絡**：條文「曾接受 anti-EGFR 療法」是前線條件、非檢測需求（regorafenib）→ EGFR 須額外滿足突變/表現/原生型脈絡(`突變|Exon|L858R|T790M|表現型|活化|原生型|插入`)才列為需檢測。
     c. **BRAF V600E/V600 重複**：有 V600E 時不再另列 V600（特異優先）。
   - 標籤語意：用「要附哪個檢測」之**中性**字樣（不分需突變陽性或需原生型），如「ALK 基因檢測」「All-RAS 基因突變分析」「PD-L1 表現量檢測」——個管師備件只需知道附哪份報告。
   - **逐條(per-clause)萃取**：`buildDocList` 以選定條文 c.text 為主，基因/標記自動分流到該適應症（osimertinib 第一線只出 Exon19/L858R、第二線只出 T790M）；whole-drug 聯集僅用於 master 報表。
   - **單一真相源**：master 報表 `gene-marker-report.html` **內嵌 index.html 同一份 `geneDocs／markerDocs`**，client 端即時計算。⚠️ 日後改萃取規則，兩處函式必須一起改（或重新由 index.html 複製產生報表）——與 build.py↔isAdminClause 同類紀律。
   - **報表逐癌別精修**：master 報表初版用「整支聯集」，使 cetuximab 把大腸癌的 All-RAS／BRAF 掛到整列、頭頸癌讀者誤會。改為**逐(藥×癌別)**：
     • 取文用 `per_cancer[癌別]`，兩種形態都要吃——①多數藥 `.clauses`（header＋subitems）；②僅 9.69 免疫為 `single_use/combo_use/pdl1/notes/subtitles`。
     • per_cancer=null 者經稽核**全為單一癌別**，安全 fallback 到 items 全文。
     • **不納入 common_data**：9.48 eribulin 的 common_data 混入一段 olaparib(BRCA) 條文，納入會假掛 BRCA；逐癌別 clauses 才是正確範圍。（順帶記：eribulin common_data 有 olaparib 條文滲入，屬待清資料瑕疵。）
     • 結果：cetuximab 頭頸癌＝無需求；9.69 各癌別正確（肺癌 EGFR/ALK/ROS-1＋PD-L1、大腸癌 MSI、胃癌 PD-L1＋HER2、黑色素瘤 BRAF）。有需求品項 57（聯集時 58 含 eribulin 假陽性）。

8. **首次實走第八節重生（母程式 V4.2.0→115.6.23）的三個陷阱**
   - 背景：母程式改版 V4.2.0（資料日期 115.6.23）。兩層 diff：編號層 0 增刪（仍 103 事審）；條文層 5 真改（9.18 早期乳癌 pCR/non-pCR 重構〔115/7/1〕、9.36.1 與 tucidinostat 擇一、9.82 brigatinib 每日 180mg、9.104 zanubrutinib 限 20 月、9.120 glofitamab 12 療程上限）。
   - 陷阱① **`_title` 沿用比對**：母程式無 `_title`，需從現行 OncoPA 以「header 正規化」沿用。norm 須**先去空白再去日期括號**（OCR 老 header 日期間有空格，反序會讓 `[0-9/、.]+` 在空格斷掉、括號去不掉）。
   - 陷阱② **手動拆分藥要保留現行**：OncoPA build 把「Erbitux 型態」多適應症條文拆成多張帶題卡（9.18/9.20/9.27/9.37/9.43/9.80），母程式仍群組式。這些藥若 0623 未改→**保留現行已拆分條目**（勿用母程式群組版覆蓋）。只有 9.18 有改→用母程式新結構＋手補「早期乳癌 · 輔助」。
   - 陷阱③ **母程式可能回退 OncoPA 下游修正**：9.98 Pemigatinib 的 OCR 滲入（9.99 Gilteritinib 併入「血液淋巴癌」）在 OncoPA V0.15.0 修過，但**母程式 V4.2.0 仍有**→重生時 9.98 須保留現行修正版。⚠️ **建議上游母程式也修掉 9.98 此 bug**，否則每次重生都要再補。
   - 做法定案：97 支用母程式乾淨 0623 文字＋header 正規化沿用 `_title`；6 支（9.20/9.27/9.37/9.43/9.80/9.98）保留現行；9.18 用母程式＋手補題。驗證：漏題真適應症卡=0、兩層 diff 僅預期變動、V0.19.0 基因/標記修正全保留、報表同步重生。

---

## 五、煙霧測試（可貼上執行）

```bash
python -m http.server 8000   # 開 http://localhost:8000
```

**手動檢查：**
- [ ] 通行碼 `cbshow` 進入
- [ ] 選癌別頁直接搜「dasatinib」→ 顯示「非事審品項、僅條文提及」提示；搜「osimertinib」→ 命中→自動進肺癌條文
- [ ] 肺癌 → 免疫 → 免疫檢查點抑制劑 → 看到子分型分組（非小細胞/小細胞）、單用/併用卡
- [ ] 搜 pembrolizumab 找得到（灰底為條文提及）
- [ ] 選一條 → 複製條文、資料清單可勾、列印正常
- [ ] osimertinib（肺癌 EGFR 第一線）→ **不**出現「腎功能檢驗值」；基因項顯示「基因檢測：EGFR 基因突變檢測（Exon 19 Del／L858R）」；選 T790M 那條則顯示（T790M）
- [ ] cabozantinib（甲狀腺癌）→ 基因項**不**出現 EGFR（VEGFR 子字串不誤判）
- [ ] regorafenib（大腸癌）→ 基因項顯示「All-RAS 基因突變分析」、**不**出現 EGFR
- [ ] 點 topbar「🧬 病摘 AI Prompt」開窗、見內建基因 prompt、可一鍵複製；備齊送審頁有基因/標記項時顯示情境連結亦能開窗；「＋匯入」新增後重整仍在
- [ ] 資料日期顯示 115.6.23；9.18 乳癌「早期乳癌 · 輔助」卡內含術後 pCR/non-pCR 分流新內容；9.98 無「血液淋巴癌」誤掛
- [ ] zolbetuximab → 標記含「Claudin 18.2」；ponatinib → 基因含「BCR-ABL T315I」；capivasertib → 「PIK3CA／AKT1／PTEN」而 alpelisib → 僅「PIK3CA」；PARP 婦癌(卵巢) → 基因含「HRD 同源重組缺陷」
- [ ] 開 gene-marker-report.html → 共 103 品項、58 項有需求；逐(藥×癌別)；cetuximab 大腸癌列出 All-RAS／BRAF V600E、頭頸癌列為「—」；9.69 各癌別不同；可搜尋／篩選／列印
- [ ] favicon 為 SELA logo、手機縮放正常

---

## 六、版本歷程

| 版本 | 重點 |
|------|------|
| V0.1.0 | 初版骨架；由「資格判定」改向「送審資料準備」四頁式、條文卡、免疫子分型拆解、通用條款抽離 |
| V0.2.0 | 只收需事審藥（103 支）、類型篩選；對齊 SELA Kit；雙 logo 制結構；英文名 OncoPA；資料夾/zip 英文化；版本號重定基準 |
| V0.3.0 | 置入正式 app logo（Gemini 生成 + §10.2 轉檔）；程式名旁加版本徽章；SELA 主 logo 顯示於登入頁與頁尾 |
| V0.4.0 | 蘋果風 UI 重構：桌機優先 master-detail 工作台（左條文清單／右送審準備，sticky），<980px 收合為推進式導覽；霧藍中性畫布、segmented 類型篩選、stepper、精煉字階、reduced-motion；密碼改 cbshow |
| V0.5.0 | 蘋果品質地板補完：點擊式磚卡（癌別／藥／條文卡／stepper）可 Tab 聚焦、Enter/Space 觸發，加 focus-visible focus 環 |
| V0.6.0 | 顯示名稱改「彰濱秀傳癌症中心 癌藥事審輔助系統」；條文工作台改等寬雙欄（1fr 1fr）修正版面不對稱；流程改癌別優先——第一步只選癌別（移除全域藥名搜尋），藥名搜尋移至該癌別內 |
| V0.7.0 | 免疫藥（9.69）卡片改「型態→單用/併用」兩層分組；卡片標題去掉與型態標題重複的前綴與尾端單用/併用標記；修正未命中型態的孤兒卡（如肺腺癌第三線歸入非小細胞肺癌）；prep/複製仍用完整條文標題 |
| V0.8.0 | 條文卡改手風琴收合（點標題展開、開一關一、預設展開第一張，CTA 不觸發收合），大幅縮短長條文清單；移除送審準備面板「需事前審查」提醒框（本系統每藥皆需事審、為冗訊；表單編號仍見於藥名列與備齊資料清單） |
| V0.9.0 | 選癌別頁改垂直置中、頁尾下沉，消除大片空白；移除冗餘副標（標題＋步驟列已說明流程）；資料修正：Cetuximab 9.27 大腸直腸癌由「1 條文含 3 子項」拆為 3 個獨立適應症卡（第一線 FOLFIRI/FOLFOX、第二線 encorafenib BRAF、二線以上 irinotecan EGFR），病人對應其一 |
| V0.23.2 | **登入密碼改明碼＋預留醫令代碼欄位，兩項**：①登入通行碼輸入框 `type="password"`→`type="text"`（同仁反映暗碼不方便，改為明碼可見）。②藥名後預留院內 **key-in 醫令代碼**顯示：新增 OncoPA 端補充 map `ORDER_CODES={}`（藥號→代碼）＋ `ocOf/ocTag/ocText` 輔助，接上藥名清單、選定藥抬頭、列印頁首與搜尋比對；map 空白時完全不顯示（現狀），待院方提供代碼填入即自動出現。<b>醫令代碼屬彰濱秀傳 HIS 醫囑碼，非健保/母程式公開資料，無法代查</b>，故僅預留、由院方提供。資料未動。⚠️ 坑 #14：院內專屬代碼（醫令碼等）一律不臆測填寫，改預留 map 由院方提供，避免臨床誤植 |
| V0.23.1 | **預留「操作精靈（手把手院內程式操作＋流程注意事項）」骨架，尚未啟用**（依需求：先預留在背後、不上線，之後補院內實際流程）。內容：topbar 加隱藏啟動鈕 `#wzLaunch`（🧭 操作精靈）、modal 骨架 `#wzMask`（重用 pl- 樣式）、`wzOpen/wzClose/wzRender` 函式、資料骨架 `WIZARD_STEPS=[]`／`WIZARD_NOTES=[]`、旗標 `WIZARD_ENABLED=false`。旗標關閉時啟動鈕隱藏、modal 不開啟，**畫面與行為零變化**。<b>日後啟用步驟</b>：①`WIZARD_ENABLED=true`；②填 `WIZARD_STEPS`（每步 `{title,body,img?,cautions?[]}`）與 `WIZARD_NOTES`（整體流程注意事項）。啟動鈕/modal 均沿用 pl- class，故 @media print 已自動隱藏。資料未動。⚠️ 坑 #13：新增隱藏功能一律以旗標預設關閉＋啟動鈕 `display:none`，確保「預留但不上線」時對使用者零可見變化 |
| V0.23.0 | **列印準備單改版（省紙核對版）＋列印前病人資訊，兩項**：①按「列印準備單」先跳彈窗，可輸<b>病人姓名／病歷號（皆可留空）</b>——僅組進列印頁首方便紙本歸檔核對，**不進 localStorage、列印後即清空**（病人個資不留存）。留空則頁首印底線供手寫。②重寫 `@media print`：黑白緊排、去色塊/陰影/大留白，隱藏左側條文清單、所有按鈕、病摘 AI 提示、SELA 頁尾；列印頁首含系統名＋藥品/癌別/事審別/適應症＋病人/病歷號/日期；勾選方框改細黑框（已勾顯✓、未勾空框供手勾）；「要備齊的資料」清單排兩欄省紙；保留條文全文、PD-L1/事審碼、注意事項、共通規定與安全聲明。純前端、資料未動。⚠️ 坑 #12：列印頁首含病人個資，`doPrint()` 列印後務必清空 `#printHead` 與輸入框，勿寫入任何儲存 |
| V0.22.1 | **免疫卡（9.69）抬頭正名，兩項**（回報自截圖）：①「舊適應症」個管看不懂 → `mkScenario` 依條文（限 109/4/1 前經審核同意、後續續用）改抬頭為「限 109/4/1 前已核准續用」（肝癌單用、胃癌單用兩張）；②併用群組硬標題「併用化療」不精確——晚期肝細胞癌第一線（atezolizumab+bevacizumab／durvalumab+tremelimumab）、惡性肋膜間皮瘤（ipilimumab+nivolumab）皆非化療 → `renderCards` 群組標題改「併用」，一次涵蓋全癌別（各卡實際搭配見條文內文）。純渲染層改動、資料未動、重生後仍有效。⚠️ 坑 #11：UI 群組硬標題勿假設 combo＝化療；母程式 label 內「(併用化療)」僅部分為真，抬頭一律用中性「併用」 |
| V0.22.0 | **「肝膽胰胃癌」拆成 肝癌／膽道癌／胰臟癌／胃癌 四獨立癌別**（OncoPA 選癌別時分開，不沿用母程式的合併類）。母程式 Cancer Drug 仍用合併類（對齊 MDT 第7團隊「肝膽胰消化道癌」），故此拆分為 **OncoPA 端專屬轉換**：資料層改寫 12 支藥的 `cancers[]`／`per_cancer`（單器官藥直接改名；多器官藥 9.46 TS-1→膽/胰/胃、9.69 免疫→肝/膽/胃、9.95 Larotrectinib→膽/胰 依條文切分），`CANCERS` 清單同步（10→13 類）。程式邏輯零改動（篩選/getSlice/免疫分組全靠癌別字串）。器官偵測：膽道癌`膽道癌|膽管|肝內膽管`、肝癌`肝細胞癌|HCC`（肝內膽管歸膽不歸肝）、胰臟癌`胰臟癌|胰腺癌`、胃癌`胃癌|胃腺癌`（GIST 不誤配）。做成可重跑腳本 `split_hbpg.py`，冪等。驗證：DRUGS=103、無殘留合併類、肝6/膽4/胰3/胃4 支、9.69 免疫各器官 subtitle/single/combo/pdl1 獨立無汙染、JS 通過。⚠️ 坑 #10：母程式每次重生 index.html 後須重跑 `split_hbpg.py`（與 9.98 OCR 修正同屬 OncoPA 端 post-rebuild 補丁）|
| V0.21.1 | **修 9.69 免疫藥條文分組錯配**（回報：「肝的免疫藥給的適應症是胃的」）。根因：`mkScenario` 以 `label.includes(subtitle)` 分組，subtitle「胃癌**(不含胃腸基質瘤及神經內分泌)**」帶括號註解，而適應症標題只寫「轉移性胃癌／胃癌第一線」，比對不中 → fallback 到 `subs[0]`＝晚期肝細胞癌，導致兩張胃癌卡（轉移性胃癌舊適應症、胃癌第一線併化療）被掛到「晚期肝細胞癌」標題下。修法：比對前先以 `subCore()` 去除 subtitle 括號註解取核心詞（胃癌(不含…)→胃癌）再 `includes`，並比對 `label＋條文前 40 字`。驗證：9.69 全 9 癌別分組＝subtitles 數、無錯配、既有 fallback（肺腺癌第三線→非小細胞肺癌）不受影響。資料未動（115.6.23）。⚠️ 坑 #9：subtitle 帶括號限定詞時，關鍵字比對須取核心詞，否則掉進 fallback 靜默錯置 |
| V0.21.0 | 整合「**病摘 AI Prompt 庫**」進 OncoPA：topbar 常駐入口鈕＋備齊送審區（偵測到基因/標記清單時）情境連結，開彈窗式 Prompt 庫。內建首支 prompt（分子病理→院內「基因報告（新增）」表單萃取，含 LOINC/民國7碼/病理科 SOP 對照），一鍵複製整段貼入醫院病摘 AI；個管可自行匯入/編輯/刪除自訂 prompt（localStorage 本機保留）。全 class/JS 以 `pl-` 命名空間隔離、prompt 全文置 `<script type=text/plain>` 免跳脫。資料未動（115.6.23）。⚠️ localStorage 自訂 prompt 綁裝置/瀏覽器，不跨機；全院共用須改放 `builtins()` 由 SELA 維護部署 |
| V0.20.0 | **首次實走第八節：從母程式 V4.2.0 重生，資料日期 115.5.22→115.6.23**。兩層 diff：編號層 0 增刪；條文層 5 真改（9.18 早期乳癌 pCR/non-pCR 重構〔115/7/1〕、9.36.1 tucidinostat 擇一、9.82 180mg、9.104 限20月、9.120 12療程上限）。做法：97 支用母程式乾淨 0623 文字＋header 正規化沿用 `_title`；6 支手動拆分/已修者（9.20/9.27/9.37/9.43/9.80/9.98）保留現行；9.18 母程式新結構＋手補題。⚠️ 母程式 V4.2.0 仍含 9.98 OCR 滲入（9.99 併入血液淋巴癌），OncoPA 端再次保留修正，**建議上游母程式修正**。基因/標記 V0.19.0 修正全保留；報表同步重生。驗證：漏題=0、兩層 diff 僅預期、103 藥、JS 通過（詳坑 #8）|
| V0.19.0 | 依另一 AI 的「事審＋生物標記」整理交叉核對，補抓 5 項原文真有但先前漏抓者：CLDN18.2(zolbetuximab，原僅 HER2)、BCR-ABL T315I(ponatinib，先前完全未列)、PIK3CA／AKT1／PTEN(capivasertib，條件式；alpelisib 仍僅 PIK3CA)、HRD 同源重組缺陷(PARP 卵巢，BRCA 外之替代)、ANCA(rituximab 血管炎)。有需求品項 57→58。已查證：一代 EGFR-TKI(gefitinib/erlotinib/afatinib/dacomitinib)、Lonsurf 等**不在本版 chap9 資料**(對方多列，scope 不同，未納)。⚠️ 對方引用 chap9_**1150623**.pdf(115.6.23) 較本專案 115.5.22 新——待向健保署確認是否有新版，再決定是否重建資料 |
| V0.18.0 | 新增功能：基因／生物標記由通用標籤改「具名萃取」(`geneDocs`/`markerDocs`)——備件清單具名顯示需附哪個基因檢測（含 Exon19/L858R、T790M、Exon20 插入、V600E、All-RAS、ALK、ROS-1、NTRK、MET Exon14、BRCA、FLT3-ITD、PIK3CA、FGFR2、PDGFRA、RET…）與哪個生物標記（PD-L1、HER2、MSI/MMR、CD20/19/22/30/33、17p、IGHV）。逐條分流；修坑 #7（VEGFR 子字串、anti-EGFR 前治療、BRAF 重複）。另出獨立報表 `gene-marker-report.html`（內嵌同源函式＝單一真相源，可搜尋/篩選/列印） |
| V0.17.0 | 修坑 #6：`DOC_RULES` 腎功能條移除 `/i`，解決癌基因 **EGFR** 誤觸腎功能 **eGFR**——9 支 EGFR 標靶藥（bevacizumab/regorafenib/panitumumab/cabozantinib/osimertinib/larotrectinib/amivantamab/encorafenib/fruquitinib）不再假叫附腎功能；同步把真腎功能變體(Ccr/CrCl/creatinine/腎絲球/肌酸酐)補進規則避免漏抓（cetuximab 頭頸癌 Ccr、carfilzomib CrCl、骨髓瘤群 eGFR 仍正確觸發）。基因/生物標記規則不動 |
| V0.16.0 | 流程改回「混合式」：選癌別頁(`#scr-find`)重新接上**全域藥名搜尋**（直接搜成分/商品/編號，不必先知癌別；命中→`pickDrug(fromSearch)` 自動帶癌別，多癌別則於選藥頁內選），保留「或選癌別瀏覽」。修正 V0.6.0 只留癌別優先導致「不知道藥用在哪種癌就完全搜不到」的盲點（例：dasatinib——本身非事審品項、僅在 9.32/9.67 等條文中被提及）。全 mention-only 命中改顯眼提示「非事審品項、僅條文提及」。renderSearch/pickDrug 機制本就在 JS，V0.6.0 起未接 UI，本版只重接介面、未動資料 |
| V0.15.0 | 策展標題全癌別完成（接力肺癌，餘 8 大類共 242 條新增 `_title`，連同肺癌 19 條 = 全真適應症皆有北歐簡潔短標、用「·」分隔）。逐條審核揪出 25 條「限制/條件/程序」句被 IND 救回成假適應症，補 ~20 條錨定式 `ADMIN_PATTERNS`（含容忍 OCR 空格的 `僅\s*得擇一給付`、`^總療程以\d`、`每日至多給付`…）並**同步寫進 JS `isAdminClause`**（build.py 自動生成 JS regex，兩端不漂移）。資料修正：移除 9.98 Pemigatinib 誤掛之「血液淋巴癌」（OCR 把 9.99 Gilteritinib 內容併入，假陽性）。驗證：coverage 缺漏=0、無藥/癌別變 0 適應症、複製內容仍逐字＝識別行＋原文（`_title` 不入複製） |
| V0.14.0 | (1)手機 RWD：全域斷詞(overflow-wrap/word-break)修長英文字串橫向溢出＋body overflow-x:hidden＋560px 小螢幕斷點。(2)isAdminClause 擴充：藥物擇一/互換規定(去空白容忍 OCR「使 用」)、劑量(最多/處方)、「無效後不再給付」、「使用注意事項」皆歸共通規定→333 適應症/78 共通。(3)策展標題：新增 `_title` 顯示覆蓋欄(優先於 clauseTitle，不動條文/複製)，**肺癌**階段完成 19 條 |
| V0.13.0 | 重大修正：通用規定/敘述不再被當成可選適應症。新增 `isAdminClause()` 把「事前審查程序、純劑量、通則十二引用、純療程上限」共 66 條路由至「共通規定」可勾選區（文字原樣保留、僅改分類）；來源劑型標記（【9.36.1…】等 6 個）改為非點選分隔標題並重新編號。安全前提：移走後無任何藥變 0 適應症（已驗證）。345 真適應症／66 通用規定／6 標記 |
| V0.12.1 | 鐵律修正：萃取標題僅供畫面顯示，移出複製內容。`copyText` 改為只輸出「藥名（編號）癌別 + 原始條文 `c.text`」，AI 萃取的 `clauseTitle` 絕不進入送審剪貼簿（免疫情境卡保留母程式原文 `**標記**` 的 `c.label`）。全 417 卡驗證：標題萃取不動原物件、複製＝識別行+逐字原文（精確全等） |
| V0.12.0 | 條文卡收合標題由「適應症 N」改為自動萃取的有意義短標（`clauseTitle()`）：分節 header（○○部分：）取部位名、完整適應症句抽「治療線·關鍵組合（生物標記）」、事前審查段標為「事前審查共通規定」；剝除前治療描述（先前接受過…無效）與排除語境（不得與X／除…外）避免抓到非本藥組合的藥名；EGFR 區分大小寫避免誤判腎功能 eGFR。417 卡 0 錯誤/0 空標題 |
| V0.11.0 | 共通給付規定改為逐條件可打勾確認：prep 面板「別忘了共通規定」由純參考清單改為 checklist，每個子條件各一勾選框、保留分段標題；獨立 `cur.cchecks` 狀態（藥物層級，切換適應症卡不重置）；新增 `commonGroups()`、`toggleCommon()` |
| V0.10.0 | 全藥稽核「Erbitux 型態」（引言/分節 header 下塞多個互斥獨立適應症），確認並拆分 4 筆：Bevacizumab 9.37 大腸直腸癌（第一線/第二線）、Rituximab 9.20 CLL（兩適應症各帶共用療程上限）、Lenalidomide 9.43 多發性骨髓瘤（第一線/復發二線+，各帶 3 條共用條件）、Osimertinib 9.80（第一線 EGFR19/21、第二線 T790M，前綴「限單獨使用」）。含共用條件者，將條件複製為每張適應症卡的子項以保送審完整 |

> 先前對話迭代曾用 V1.x 內部編號，現重定基為 V0.2.0（雛型階段）。超過 10 版砍最舊的，搬到 README.md。

---

## 七、下版候選工作（按優先序）

1. **更新資料流程驗證** — 下次母程式改版時實走第八節流程（維護命脈）；屆時新增/異動條文需補對應 `_title`（策展短標），並同步維護 build.py 的 `TITLES` 對照表與 `ADMIN_PATTERNS`（兩端 JS/Python 同步，見坑 #5）
2. ~~策展標題全癌別~~（V0.15.0 完成：全真適應症皆有 `_title`）
3. 肺腺癌等子型字串未對到 `subtitles`，目前歸「其他」→ 建子型對應表歸入非小細胞肺癌
4. P 碼／PD-L1 由「全表自選」升級為情境↔P 碼可信配對（保留全表兜底）
5. `form_no` 待母程式補齊後自動帶入（無需改本工具）

---

## 八、升版必讀 — 資料更新流程（維護命脈）

> **本工具資料不自己手維護，一律從母程式重生。不做自動核對（那留在母程式）。**

NHI 條文更新時：

1. 照原流程把新條文更新進**母程式 `index.html`**（雙層 diff、自動核對都在母程式）。
2. 把更新後的母程式 `index.html`（或其中 `const drugs = [...]` 整段）交給 Claude。
3. 一併告知：**資料日期**（母程式 `CURRENT_DATA_DATE`）、**結構是否有變**（新癌別／新特殊排版／新 `form_no`）。
4. Claude：抽 `drugs` → 濾 `pre_review=true` → 精簡（保留 `st`）→ 純字串注入 `index.html` → 更新 `.brand-version` 的 `data-date` 與顯示、版號 +1 → 跑第五節煙霧測試。

> 採「AI 介入重生」而非一鍵腳本，是 SELA 的決定：每次更新都是優化機會（條文拆解、子分型歸類、P 碼配對），由 Claude 介入比機械注入更能維持品質。

---

## 九、一句話總結

V0.15.0（雛型）：功能完整的獨立事審送審準備工具。**策展標題全癌別完成**——所有真適應症收合卡皆有北歐簡潔短標（`_title` 顯示覆蓋、用「·」分隔、不入複製）；逐條審核同時把「限制/條件/程序」句（不得合併、僅得擇一、使用前須…、總療程上限…）補進 admin 路由（build.py 與 JS `isAdminClause` 兩端同步），並修正 9.98 OCR 假掛癌別。手機 RWD 完成（斷詞防溢出＋小螢幕斷點）；通用規定（含擇一/互換、劑量、無效後不給付、使用注意事項、事前審查/通則/療程上限）與劑型標記不列為可選適應症，改入共通規定區/分隔；收合標題萃取僅供顯示、不混入複製；共通規定可逐條件打勾，顯示名「彰濱秀傳癌症中心 癌藥事審輔助系統」。條文卡手風琴收合；選癌別頁垂直置中、精簡冗語；已全藥稽核並拆分「Erbitux 型態」多適應症條文，病人對應其一。流程癌別優先：選癌別→選藥→核對條文→備齊送審。蘋果風桌機優先等寬雙欄工作台、手機響應收合、鍵盤可及性齊備；密碼 cbshow。版本自成一軌、不對齊母程式。下版第一優先是「下次母程式改版時實走資料更新流程」。

---

## 十、雙 logo 制（SELA Kit §8-9、§17）

- **App logo（主視覺）：** `favicon/app-logo.png`（512²，正式 logo）＋ `app-logo-master.png`（滿版方形母圖）。由 Gemini 依 `SELA-logo-prompt.md` 生成，Claude 走 §10.2 四步轉檔（取底色 #446e86 → sentinel floodfill 去白底+鋸齒環 → 純底色合成白 glyph → 生 16/32/180/192/512 + ico）。**重生方式：** 換新圖重跑 favicon/ 內處理腳本即可。logo 為點陣（含文字「CB Show」），無 SVG 版。
- **logo prompt：** `SELA-logo-prompt.md`（根目錄，範本 B 醫療型、北歐霧藍 #436f8a、壁虎 not a natural fit）。
- **SELA logo（品牌歸屬）：** footer 角標 `.sela-credit`，引用**獨立**的 `favicon/sela.svg`（不重用 favicon 引用）。
- **出現位置：** 登入頁、topbar、favicon、手機捷徑皆為 app logo；**SELA 主 logo 顯示於登入頁底部 + 頁尾 footer**（30px + 標籤，明確但仍為輔助）。
- **配色不撞：** app 北歐霧藍 vs SELA 橘，不同色。manifest `theme_color`/`icons` 用 app 自己的（#2c4f66 + app logo）。
