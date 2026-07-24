# CLAUDE.md — 癌藥事審送審準備工具

> **部署（GitHub Pages）**：採自訂 workflow `.github/workflows/deploy.yml`（`concurrency: cancel-in-progress: true`，避免密集 push 互相卡死）＋根目錄 `.nojekyll`；Source 設「GitHub Actions」。此為部署設定，非 app 變更（app 仍 V0.26.0）。密集 push 後若見 `Deployment failed, try again later.`：先 Settings→Environments→github-pages 取消卡住的 deployment、Actions 取消多餘排隊 run，再 re-run。

> **這份是給下次 Claude 看的工作上下文，不是文件。**
> 維護章法：`SELA-Starter-Kit/conventions/CLAUDE-MD-章法.md`，每次升版前複習。
> 每升一版至少更新三處：踩過的坑、版本歷程、下版候選工作。

---

## 〇、當前狀態

- **版本：** V0.31.0（資料日期 115.6.23；基因對照全面對齊病理科 SOP）
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
| V0.31.0 | **基因對照全面對齊病理科 SOP（使用者裁示「都先照病理科建議為主」）**。`GENE_LOINC` 重寫並加註來源：SOP 有明訂者一律以 SOP 為準，SOP 未涵蓋者才用查找視窗實查碼，並於表頭載明「修改須同步病摘 Prompt 之 SOP 表（Rule 14）」。**依 SOP 改動**：EGFR 21665-5→**21666-3**（SOP 基因層級碼；變異層級 55764-5/55766-0/55769-4/55770-2 列為二擇一）、**PD-L1 由「附病理報告」改為可填表 83052-1**（方法 LP6333-1 Immune stain，另列 83054-7/85147-7/99064-8/83057-0）、HER2 49683-6（另列院內 7 碼）、ALK 78205-2（方法 LP6333-1／LP6404-0，並警示 21787-7/21813-1/90305-4 屬 ALCL 淋巴瘤肺癌勿用）、ROS1 102038-7（方法 LA26404-6）、BRCA 改列 SOP 候選 21639-0/38531-0/59041-4/79207-7。新增 **`method` 欄**與 `.lc-mth` 樣式（螢幕藍底／列印細黑框），備件清單每行同時顯示代碼與建議檢測方法。精靈同步：步驟11 檢測方法補 **LP6333-1 Immune stain／LP6404-0 Molgen**、PD-L1 警語改為「依 SOP 仍可填基因資訊」；步驟13 新增★「融合類（ALK/ROS1/NTRK）突變類型選 **95123-6 Gene fusion transcript details**，融合對象寫分析結果欄」。驗證：34 標籤 100% 命中、JS 通過。⚠️ 坑 #35：Python 字串內 `\\n` 寫入 JS 單引號字串會變真換行破壞語法，插入 WIZARD 文字須寫 `\\\\n`（本次由 node --check 攔到）|
| V0.30.1 | **BRAF 定案 58483-9（使用者確認），三處同步**：①精靈對照表——移除待確認的 104278-7 列、58483-9 標「★院內確認採用」；②`GENE_LOINC` 註記同步；③**病摘 AI Prompt 內建區塊**——SOP 表 `| BRAF | 104278-7 ⚠️ |`→`58483-9`、刪除「104278-7 在 ODS 代碼表查無」註腳、BRAF 細表改為「基因層級 58483-9／V600E 58415-1(組織)·85101-4(骨髓)／V600K 89861-9／V600(組織) 97025-1」。全檔已無 104278-7 殘留。**⚠️重大發現**：內建 Prompt（`pl-builtin-gene`）中早已存在一份「病理科 SOP：基因→檢測代碼→檢測方法」及各基因變異層級細表，內容比 V0.29.0 新建之 `GENE_LOINC` 更完整，且揭露多項本專案先前不知之事實——檢測方法另有 **LP6333-1 Immune stain(IHC，PD-L1 用)／LP6404-0 Molgen**（故 IHC 亦可填基因資訊）、突變類型有 **95123-6 Gene fusion transcript details**、院內有**「452 筆代碼表」**為權威子集（104276-1／104290-2／81747-8 均查無）。二者存在衝突（EGFR：SOP 21666-3 vs GENE_LOINC 21665-5；PD-L1：SOP 走 Immune stain 填表 vs 使用者指示直接附病理報告），待使用者裁示後統一。⚠️ 坑 #34：新增功能前應先全檔搜尋既有同類資料（本次 GENE_LOINC 與內建 Prompt 之 SOP 表重複建置，違反 Rule 14 單一來源）|
| V0.30.0 | **操作精靈改為收合式介面**（回報：敘述太多，長表格如 LOINC 對照應可收合）。改用原生 `<details>/<summary>`（無需 JS 狀態管理）三層收合：①**步驟**——16 步預設全部收合，收合時僅顯示編號＋標題＝乾淨索引；②**巢狀收合**——表格（50 筆 LOINC／6 筆實例）與「其他注意事項」各自獨立收合，summary 顯示筆數；③**流程注意事項**整區收合。新增 `wzAll(open)` 全部展開／全部收合按鈕與 `.wz-bar` 工具列。**警語分層**：以 `★` 開頭者視為關鍵警語，恆常顯示於橘底 `.wz-caut-key` 區塊；其餘收進「其他注意事項（N）」。自訂 summary 箭頭（`::after` ▸／展開時旋轉 90°），移除瀏覽器預設 marker。草稿橫幅文字改為「內容仍在校對中（報告／檔案管理、送出兩步待補），發現有誤請回報」。渲染模擬驗證：details 開關各 29 平衡、16 步驟區塊、12 個巢狀收合、3 個★關鍵警語區塊。精靈 modal 沿用 `pl-mask` class，列印時本即隱藏，無需額外列印處理。⚠️ 坑 #33：長內容面板優先用原生 `<details>`，避免自建開合狀態；分層原則＝關鍵警語恆顯、細節收合、summary 帶數量讓使用者預期展開量 |
| V0.29.0 | **「要備齊的資料」自動帶出基因資訊填表代碼**。設計轉折：原規劃「逐藥或逐條人工標註基因需求」，查證後發現**現有 `geneDocs`／`markerDocs` 已是逐條呼叫且標籤已內含變異型態**（如「FGFR2 基因融合／重排檢測」「MET Exon 14 跳讀突變檢測」「All-RAS 基因突變分析」），故無需任何標註工程——掃描 534 段條文，兩函式合計只產出 **34 種標籤**，只需建 34 標籤→代碼之對照即可。實作：新增 **`GENE_LOINC`（26 筆前綴規則，涵蓋全部 34 標籤，命中率 100%）**，17 筆給 LOINC 代碼、9 筆標「附病理報告」；`loincOf()`／`loincHint()` 於 checklist 每行下方渲染提示，代碼可點擊複製（`copyLoinc`，含 execCommand fallback）；螢幕與 `@media print` 樣式各一套（列印用細黑框、8.5px）。依使用者決策：非分子項目（PD-L1／HER2 IHC／CLDN18.2／MSI·MMR／CD 系列／17p／IGHV／HRD／ANCA）一律走病理報告；BRAF 採 58483-9。**單一來源**：`GENE_LOINC` 為備件提示與精靈對照表之共同依據（勿另建第二份）。因 geneDocs 為程式邏輯非資料，母程式重生後標籤不變，**本功能無需 post-rebuild 腳本**。⚠️ 坑 #32：動手前先查既有邏輯——本次原擬 174 條文標註工程，實際只需 26 筆對照；另注意 ad-hoc 分析用 regex 須與產品同級（無字界的 `EGFR` 會誤中 VEGFR，導致誤判需求分歧） |
| V0.28.4 | **依 LOINC 官方論壇回覆修正「tested for」用法**。使用者提供 LOINC Community Forum 討論串（2024/11「What is the difference between LOINC 21666-3 and 21665-5?」），LOINC 團隊 **Pam Banning 官方回覆確認**：「Tested For」系列**不是病人結果**，僅為「檢驗套組查了哪些位點」之清單；「Mutations Found」系列才是病人結果。其設計目的是讓臨床能判讀「未發現突變」究竟涵蓋到哪些位點（例：結果碼寫 No Mutations Found、但 tested-for 只列 exon19 del 與 L858R，即可看出 T790M 根本沒驗）。故修正原「★不要選 tested for」之敘述為更精確的兩段：①不可拿來填**結果**（結果用 targeted mutation analysis 碼）②但**可另加一列**記錄涵蓋範圍——院內 cobas 報告的 Detection range 即此清單，**正可佐證條文所要求的「All-RAS」涵蓋**。步驟14 實例增列（選填）KRAS 21703-4／NRAS 21720-8 涵蓋範圍列；表中 21666-3 由「⚠️建議改用」改為「選填佐證用，不可取代 21665-5」。⚠️ 坑 #31：遇代碼語意爭議應查標準組織官方來源（LOINC Forum/官網）而非僅憑推論或他人轉述；本次官方回覆同時證實原判讀並揭露原未想到的互補用法 |
| V0.28.3 | **院內同仁實務反饋比對，對照表 47→50 筆；坑#21 解除**。比對結果：**相符 4 項**——KRAS+NRAS→81420-2（且院內慣用「RAS 合併一列」，步驟14 實例已改為此填法、原三列改列為替代填法）、ROS1→102038-7、檢測方法 cobas→LA26419-4 qPCR、FISH→LA26404-6。**新增 1 項**——ERBB2(HER2)→**49683-6**（FISH 時方法選 LA26404-6）。**存疑 2 項**：①院內回報 EGFR 用 **21666-3**，但該碼為 *mutations tested for*＝套組涵蓋範圍非檢驗結果，表中標⚠️並建議改用 **21665-5**（targeted mutation analysis）；②院內回報 BRAF 用 **104278-7**，該碼未出現在 BRAF 搜尋畫面中，標⚠️待確認 COMPONENT。**坑#21 解除**：PD-L1(TPS/CPS/TC/IC) 屬 IHC，**不填基因資訊，直接檢附病理報告**（院內實務確認），步驟11 警語改為確定敘述。另補：代碼的 METHOD_TYP 與「檢測方法」欄可不同（ROS1 僅 Molgen 碼，做 FISH 仍選 102038-7＋方法欄選 LA26404-6）。⚠️ 坑 #30：外部實務反饋須逐項比對而非照單全收——語意錯誤的代碼（tested for）即使已在使用也應標示存疑並提出正解 |
| V0.28.2 | **MET 三種變異型態齊備，對照表 44→47 筆**。使用者補齊 MET 搜尋結果，發現 MET 在清單中有三類代碼：**exon 14 跳讀突變→100026-4**（targeted mutation analysis·Nom）、**擴增→90926-7(FISH)／102039-5(Molgen)**、**copy number 定量→92906-7(copy/nucleus)／92907-5(MET/CEP7 比值)**。經全文查證 **9.101 Tepotinib 條文無「擴增/amplification」字樣**，僅要求 exon 14 跳讀突變 → 確認選 100026-4，擴增與 copy number 入表但標「※非 9.101 條文所需」。同框入鏡之 RET(101386-1)／ESR1(102116-1、104295-1)／PML-RARA(21551-7)／CBFB-MYH11(101377-0) 查證後**均無對應 §9 藥品**（selpercatinib、pralsetinib、elacestrant 皆未收載；RET/amplification 之條文命中為字串誤中），不入表。警告改寫為通則：「變異型態要對」涵蓋 融合/重排 vs 點突變（FGFR2、NTRK）與 MET 三型態。⚠️ 坑 #29：同一基因常有「點突變／融合重排／擴增／copy number」多種變異各有代碼，**必須回查條文採認哪一種**；本專案已三度由此攔截誤選（FGFR2、NTRK、MET） |
| V0.28.1 | **補 MET 代碼，LOINC 對照表 43→44 筆**。使用者搜「MET gene」回傳整份清單（搜尋不穩定：單一關鍵字與含空格片語可比對，「MET gene」則失效），但畫面中已可見 **100026-4 MET gene targeted mutation analysis**（Prid/Bld·Tiss/Nom/Molgen）。經確認清單**無「MET exon 14 skipping」專屬代碼**（前次搜「exon 14」僅回 JAK2 佐證），故採通則：**選上位的 100026-4，把「MET exon 14 skipping mutation」寫在突變類型欄**；9.101 Tepotinib 條文原文即「間質上皮轉化因子外顯子14 跳讀式突變(MET exon 14 skipping mutation)」。同框入鏡之 IDH1(100022-3)／IDH2(100023-1)／IDH1·IDH2 exon4(100305-2/100306-0)／SETBP1／SRSF2／TPMT／NUDT15 經全條文查證**均無任何 §9 條文提及**（含 ivosidenib/enasidenib），故不入表。⚠️ 坑 #28：找不到精確代碼時的通則＝「代碼選最貼近的上位項，精確資訊寫在突變類型/結果欄」，勿為求精確而選不相符的代碼，亦勿留空 |
| V0.28.0 | **新增精靈步驟14「真實分子報告填表實例」**（使用者提供院內大腸直腸癌 KRAS/NRAS/BRAF cobas real-time PCR 報告全文）。內容：報告→表單全欄位對照（檢測方法→**LA26419-4 qPCR**、檢體→組織FFPE、機構→本院不勾外院報告）＋**三列明細表**（KRAS 21702-6「Exon 2, G12X·偵測到」／NRAS 21719-0「未偵測到」／BRAF 58483-9「未偵測到」）。關鍵警示：①**「G12X」不可自行改寫成具體位點**（cobas 的 G12X 代表 G12A/C/D/R/S/V 之一而未指明，僅 G12C 在 FFPE 單獨報出）②**陰性列一定要填**（抗 EGFR 藥即在證明 RAS 原生型）③BRAF 選 58483-9 而非 97025-1（cobas 涵蓋 exon11 G466/G469 與 exon15，範圍大於 V600）④腫瘤含量需 ≥10%（本例 15%）。**條文查證結果**：本組涵蓋 KRAS/NRAS exon 2/3/4＝符合條文所需 All-RAS；KRAS 突變 → 不符 cetuximab(9.27)／panitumumab(9.53) 之 RAS wild-type，亦不符 encorafenib(9.134) 之 BRAF V600E；但 **regorafenib(9.51)／fruquintinib(9.136) 條文僅要求「K-ras 原生型者才需再加上用過 anti-EGFR」，故 KRAS 突變者反少一道前線門檻**。⚠️ 坑 #27：str_replace 以步驟 title 行為錨點插入新步驟會吃掉原步驟標題造成 JS 斷裂——插入 WIZARD_STEPS 後必跑 node --check（本次即由此攔到） |
| V0.27.2 | **LOINC 對照表 40→43 筆＋釐清搜尋機制**。使用者搜「exon 14」欲找 MET，實際全數撈到 **JAK2**——確認 UBrowList **搜尋為 COMPONENT 字串比對、非語意搜尋**，提示改用「基因名＋gene」（如「MET gene」）。順勢加入 JAK2 三筆：exon 14 突變分析 周邊血→**80187-8**／骨髓→80188-6／全定序→99963-1；**查證 9.55 Ruxolitinib 條文後標明「條文未強制」**——該條文要求為 IWG Consensus Criteria 中度風險-2/高風險＋脾腫大症狀，全文無 JAK2/V617F/CALR/MPL，故 JAK2 僅為 MPN 診斷佐證。另查得 **9.101 Tepotinib 條文明文要求「MET exon 14 skipping mutation（外顯子14 跳讀式突變）」**，其 LOINC 尚待以「MET gene」搜尋取得。⚠️ 坑 #26：加入任何基因代碼前先回查條文是否真有此要求，勿因清單有就寫成必填；本專案已兩次以條文查證修正（JAK2 非必填、FGFR2 須選 rearrangements） |
| V0.27.1 | **基因 LOINC 對照表擴至 40 筆（第二批：FLT3/PIK3CA/NTRK/FGFR2/BCR-ABL/PDGFRA）**。新增：FLT3-ITD 骨髓→**85100-6**／周邊血→79210-1／allelic ratio→92844-0、FLT3-TKD(D835+I836)→72520-0、D835→92843-2；PIK3CA→**60033-8**；NTRK1/2/3 重排→**93813-4**(唯一)；**FGFR2 融合/重排→95784-5**（Pemigatinib 條文所需）、點突變→21674-7；**BCR-ABL1 激酶區突變(含 T315I)→55135-8**（ponatinib 送審用）、b2a2→49490-6、b3a2→49491-4、e1a1(p190)→49496-3、t(9;22)→74041-5；**PDGFRA D842V→77170-9**（avapritinib）、exon18→71357-8、重排→55092-1。新增兩條關鍵警告：①**融合/重排 ≠ 點突變**（FGFR2 選 95784-5 非 21674-7；NTRK 選 rearrangements）②**FLT3 無通用 targeted mutation analysis**，須依 ITD/TKD 分選且檢體要對。不要選清單補 63419-6(PIK3CA tested for)、21675-4(FGFR2 tested for)、83062-0(PIK3CA VCF)。另補「搜尋結果過多改用更精確關鍵字」（MET 逾 30 筆）。⚠️ 坑 #25：條文寫「融合／重排」時務必選 rearrangements 類代碼，選成 targeted mutation analysis（點突變）等於未證明該條件 |
| V0.27.0 | **精靈支援表格 ＋ 基因→LOINC 對照表（23 筆，院內清單實查）**。①`wzRender` 新增 `table:{cap,head,rows}` 支援與 `.wz-tbl` 樣式（第二欄自動 mono 強調代碼、可橫捲）。②依使用者實查截圖（EGFR/ALK/BRAF/NRAS/ROS1/BRCA）建對照表填入步驟12：EGFR 一般→**21665-5**、exon19del→55764-5、L858R→**55766-0**(c.2573T>G)、T790M→**55769-4**(c.2369C>T)、exon20ins→55770-2、液態切片→85383-8(Plas.cfDNA)；ALK 重排FISH→**78205-2**、EML4-ALK組織→88744-8、一般→100019-9、ALCL NPM-ALK→21813-1；BRAF V600E組織→**58415-1**、V600(Tiss)→97025-1、一般→58483-9、V600K→89861-9；KRAS→21702-6、**KRAS+NRAS套組→81420-2**、全定序→82535-6；NRAS→21719-0；ROS1→**102038-7**(唯一)；BRCA1+2套組→**50995-0**、BRCA1→21636-6、BRCA2→38530-2、全定序+del/dup→94191-4。③新增「★不要選」清單：所有 *mutations tested for*（21666-3/21703-4/21720-8/21639-0/38531-0/59041-4）與 VCF 類（83059-6/83060-4/83061-2）。**僅收錄畫面實查代碼，未見者不臆造**（坑#14）。⚠️ 坑 #24：同基因多筆差異在檢體(Bld/Tiss vs Bone marrow vs Colon vs Plas.cfDNA)與方法(Molgen vs FISH vs Sequencing)與尺度(Nom=突變名/Ord=有無/Doc=敘述/Qn=定量)，須三者比對報告後選 |
| V0.26.6 | **精靈「事審品項」段依實機畫面完成**（新截圖：分頁主畫面）。原⚠️待補 1 步改為 2 步（總 14→15）：**①key 碼帶出藥品**——下半部三頁籤（藥品/特材/醫療服務），★**必須先 key「健保碼」或「院內碼」，項目名稱才帶出、下方欄位才啟用；沒 key 碼整頁不動作**（使用者實測回報）；院內碼＝OncoPA 藥名旁醫令代碼之落點；多藥併用需逐支加入。**②用法用量、線別與申請量**——＋ 新增用法列（次用量/劑量/服用時機/次日/日Cycle/途徑/天數/使用起日/週期），三關鍵欄：適應症（用 OncoPA 條文標頭）、**用藥線別（預設「不適用」必改，接 V0.26.1 標頭線別成果）**、持續用藥狀況（初次使用／申請再次使用＝12週續用）；申請數量須與次用量×次/日×天數算得一致；儲存後入上方清單（序/健保碼/院內碼/名稱/申請量/途徑/用法）。⚠️ 坑 #23：本分頁為「先 key 碼才啟用」的表單，畫面看似可填實則未動作；用藥線別預設「不適用」忘改與續用誤選初次使用，為兩大退件原因 |
| V0.26.5 | **精靈補「基因檢測」LOINC 代碼選法**（新截圖：基因檢測項目的 UBrowList，含 LOINC_NUM/COMPONENT/PROPERTY/SYSTEM/SCALE_TYP/METHOD_TYP/CLASS 欄，以 KRAS 搜尋為例）。基因明細 1 步拆為 2 步（總 13→14）：**②選 LOINC 代碼**——教「靠四欄判斷」：COMPONENT(單基因 vs 合併套組)、**SCALE_TYP**(Nom=突變名稱／Ord=陽性陰性／Doc=整段文字)、METHOD_TYP(Molgen vs 定序)、SYSTEM(Bld/Tiss)；KRAS 實例：targeted 熱點→**21702-6**、大腸直腸 RAS 套組(KRAS+NRAS)→**81420-2**、NGS 全基因→**82535-6**；並點名兩個易選錯：**21703-4「mutations tested for」是套組涵蓋範圍不是結果**、**83059-6 是 VCF 原始檔格式**。**③填突變類型/結果/判讀**——照報告原文寫、wild type 也要填（抗 EGFR 需證明 RAS wild type）。**未臆造未見於畫面的 LOINC**（EGFR/ALK 等改教搜尋規則），沿用坑 #14 原則。⚠️ 坑 #22：LOINC 清單常有 COMPONENT 同名多筆（如 21702-6 vs 53620-1）與同碼重覆列，須拉寬 LONG_COMMON_NAME 依檢體/方法挑；勿選 tested-for 或 VCF 類代碼當結果 |
| V0.26.4 | **操作精靈「基因資訊」段依實機畫面細化**（新截圖：檢測方法的 UBrowList 選取視窗，LOINC LA 代碼全清單）。原 1 步拆為 2 步（總步驟 12→13）：**①開新增與檢測基本欄位**——評估項目固定 69548-6；檢測方法按鈕開 UBrowList，寫入常用對照（NGS/Sanger→**LA26398-0 Sequencing**、即時定量 PCR如 cobas EGFR→**LA26419-4 qPCR**、一般 PCR→LA26418-6、FISH(ALK/ROS1/HER2)→**LA26404-6**、核型→LA26406-1 Karyotyping、MLPA→LA26415-2、SNP array→LA26400-4）；提示可用「搜尋條件」關鍵字篩選、無對應才按【選取[空白]】；外院報告勾選。**②基因檢測明細與判讀**——基因檢測小表逐列（基因名/突變類型/結果）、分析結果、臨床判讀兩下拉、附件非必要、按確認回清單。並提示條文指定生物標記（EGFR/ALK/MSI-H·dMMR/NTRK/FGFR2）須在此看得到對應結果。⚠️ 坑 #21：PD-L1、HER2 等 **IHC 染色不在檢測方法(LOINC 分子方法)清單中**，PD-L1 表現量報告應循「報告／檔案管理」檢附（該路徑待截圖確認）；勿為求填欄硬選不相符的分子方法代碼 |
| V0.26.3 | **操作精靈「評估項目」段依實機畫面細化**（新截圖：三子表＋三個新增對話框的完整下拉清單）。原 1 步拆為 3 步（總步驟 10→12）：**①癌症分期**——評估日期/評估者自動帶入，評估項目下拉為分期系統（TNM stage grouping 399390009／BCLC C115134／Ann Arbor 254372002／Myeloma ISS·RISS／Gleason·ISUP／FIGO／Rai·Binet／Clark·厚度／FNCLCC／Fuhrman／WHO CNS／Nottingham／Dukes·Astler-Coller·ACPS 等），寫成癌別→分期系統對照，並提示可多筆（TNM＋器官專用）。**②病人狀態評估**——鎖定四個關鍵 LOINC：**89247-1 ECOG**（幾乎必填，多數條文 ≦1、部分 ≦2）、**88020-3 NYHA**（免疫共通規定 Class I/II）、**98153-0 Child-Pugh panel**（晚期 HCC 需 A）、89243-0 KPS；備用 8277-6 BSA、711434002 CTCAE、IPS。**③治療後疾病狀態評估**——僅五選項 REC1(RECIST 1.1)／IREC(i-RECIST)／MREC(mRECIST)／ICLL(iwCLL)／IWGC(IWG)，對應「免疫每 12 週以 i-RECIST、HCC 用 mRECIST」條文；初次可不填、續用必填。此段直接對接 OncoPA 共通規定（ECOG／NYHA／Child-Pugh／療效評估標準）。⚠️ 坑 #20：療效評估標準須依藥別選（免疫→i-RECIST、HCC→mRECIST），選錯等同未依條文評估；分期需與病理/影像報告一致 |
| V0.26.2 | **操作精靈「病人資訊」段依實機畫面細化**（新截圖：已填妥的病人資訊頁＋「門診醫囑(主訴資料)」對話框）。原 3 步拆為 5 步：①開新案（key 病歷號→自動帶身分證/姓名/生日/性別）②選癌別 ③基本欄位（申請日期自動今日民國7碼、身高體重、**醫師/科別 key 代碼→右側自動顯示中文**、申請案件=一般事前審查、申請類型=送核；補「送核補件/申復須填原受理編號」）④診斷碼與診斷日期（**key ICD→右側自動顯示英文診斷名作為驗證**，如 C20→Malignant neoplasm of rectum；診斷日期民國7碼、為確診日）⑤**簡要病歷(申請理由)★最關鍵**：按【門診醫囑(主訴)】開窗，可切醫師/本科/全院、左列就診日期、🔄重整，選取後帶入欄位。流程注意事項補「日期一律民國7碼」「代碼欄要跳出中文才算正確」。步驟數 8→10，草稿旗標保留（事審品項/報告/檔案管理/送出仍待補）。⚠️ 坑 #19：門診醫囑帶入的是歷次門診主訴流水帳（鼻炎/頭痛等），與癌藥申請無關，**必須改寫成對條文逐條交代的申請理由**（OncoPA【複製條文】為材料），直接送出等於沒寫理由會被退件 |
| V0.26.1 | **送審條件標頭一眼可讀（補線別/情境）**：全面複查 71 個 clause 標頭＋84 支 items 標頭，多數已清楚（含第一線/二線/三線/xx後）。改寫 7 個一眼不易懂或缺重要線別者：9.34 Sorafenib／9.63 Lenvatinib 肝癌「晚期肝細胞癌·Child-Pugh A」→加「第一線」（別於 regorafenib/ramucirumab 之 sorafenib 後）；9.46 TS-1 肺癌「非小細胞肺癌」→「·含鉑化療失敗後」；9.36／9.36.1 Everolimus 乳癌「與 exemestane 併用·HR+/HER2−」→「HR+/HER2− 轉移性乳癌·AI 失敗後（＋exemestane）」（改為疾病+線別開頭）；9.22 Imatinib「惡性胃腸道基質瘤（GIST）」→「·第一線及術後輔助」；9.37 Bevacizumab 卵巢「卵巢／輸卵管／腹膜癌」→「·第一線維持（＋carbo/紫杉醇）」。依藥號＋癌別＋原標頭精準定位改（同名標頭不誤改）。資料未動、DRUGS=103、JS 通過。⚠️ 坑 #18：標頭應「疾病＋線別/情境」開頭，勿以併用藥名或純疾病名開頭；重要線別(一/二/三線)寫進標頭 |
| V0.26.0 | **癌別對齊院內系統下拉—完成**（使用者確認系統清單就 20 項、無腎癌/胰臟/白血病/骨髓瘤/黑色素瘤；喉癌歸下咽）。承 V0.25.0，`remap_cancers.py` 補第二階段（單一腳本、接 split_hbpg 後、冪等）：腎細胞癌(泌尿癌殘留)／胰臟癌／白血病／多發性骨髓瘤／MDS／黑色素瘤等**一律併入「其他癌症」**；血液淋巴癌拆為 **淋巴癌(淋巴瘤)＋其他癌症(白血病/骨髓瘤/MDS)**，混合適應症藥(Rituximab/Bortezomib/Lenalidomide/Ibrutinib/Zanubrutinib/Obinutuzumab)兩類皆入；頭頸癌拆 **口腔/口咽/下咽(喉→下咽)**，通用頭頸鱗癌→三部位、鼻咽排除(免疫「不含鼻咽」)。最終 **CANCERS 18 類**＝系統清單中有藥者。修 bug：per_cancer=null 血液藥 items 混病種需多目標(NONLYMPH 關鍵字)；merge_slice 併入既有 slice 不覆蓋(9.69 免疫 RCC 併入其他癌症 immune)；頭頸「不含鼻咽」排除。驗證：DRUGS=103、無孤兒、消失類別(泌尿/胰臟/血液淋巴/頭頸/鼻咽)無殘留、淋巴癌17/其他癌症56、JS 通過。⚠️ 坑 #17：多適應症/多病種藥拆分須「一 clause/items 可命中多目標」＋併入既有 slice 不可覆蓋；「不含X」語意要排除 X |
| V0.25.0 | **癌別對齊院內事審系統下拉（無爭議部分）**。可重跑腳本 `remap_cancers.py`（在 `split_hbpg.py` 之後執行、冪等）。①純改名：大腸直腸癌→結直腸癌、膽道癌→肝內膽管癌、其他癌→其他癌症。②拆分：婦癌→子宮頸癌／卵巢、腹膜、輸卵管；泌尿癌→攝護腺癌／膀胱癌(泌尿道上皮)，**腎細胞癌留「泌尿癌」**；其他癌症→碎出胃腸道間質瘤(GIST)／甲狀腺惡性腫瘤，其餘留其他癌症。③**依使用者指示保留原樣**：胰臟癌、血液淋巴癌(系統僅有淋巴癌)、頭頸癌(系統無「喉癌」、且頭頸藥為跨部位)——待使用者確認去向。CANCERS 13→18 類。per_cancer 空的單類藥改用 items 關鍵字判定(可多命中，修了 9.49/9.109/9.97/9.123/9.86)。Larotrectinib(NTRK 泛腫瘤)主家仍在其他癌症、額外浮現甲狀腺(正確)。驗證：DRUGS=103、無孤兒藥、無舊名殘留、不動類別(胰臟3/血液43/頭頸2)保持、JS 通過。⚠️ 坑 #16：per_cancer=null 單類藥拆分須讀 items 判子癌別，勿逕丟 residual；系統癌別清單疑不完整(缺腎癌/胰臟/白血病/骨髓瘤/黑色素瘤)，有爭議者一律留原類待確認 |
| V0.24.0 | **操作精靈（NHOS3001 癌藥事審申請作業）草稿版上線預覽**：依院內截圖填入 `WIZARD_STEPS`（8 步：開新案/病歷號自動帶資料 → 選癌別[含 OncoPA→系統下拉對應] → 病人資訊分頁 → 事審品項⚠️待補 → 評估項目分頁 → 基因資訊[接病摘 AI Prompt] → 報告/檔案管理⚠️待補 → 送出⚠️順序待確認）＋ `WIZARD_NOTES`（流程注意事項）。`WIZARD_ENABLED=true` 啟用、新增 `WIZARD_DRAFT=true` 顯示未完成橫幅；🧭 操作精靈鈕現身。缺的分頁（事審品項醫令代碼/事審碼、報告上傳、送出順序）明確標「待補」。純前端、資料未動。待補：事審品項/用藥資訊/報告/檔案管理/審查回覆截圖、匯入事審資料行為、送出順序，齊了即補完並移除草稿旗標。⚠️ 坑 #15：系統癌別下拉比 OncoPA 細（肝內膽管癌/胃腸道間質瘤獨立、頭頸/泌尿/婦拆細），採「OncoPA癌別→系統下拉值」對應表而非再拆 OncoPA |
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
