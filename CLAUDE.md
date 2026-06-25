# CLAUDE.md — 癌藥事審送審準備工具

> **這份是給下次 Claude 看的工作上下文，不是文件。**
> 維護章法：`SELA-Starter-Kit/conventions/CLAUDE-MD-章法.md`，每次升版前複習。
> 每升一版至少更新三處：踩過的坑、版本歷程、下版候選工作。

---

## 〇、當前狀態

- **版本：** V0.5.0（雛型階段；版本號自 V0.2.0 重新定基）
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

---

## 四、踩過的坑（編號累積，永不重排）

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

---

## 五、煙霧測試（可貼上執行）

```bash
python -m http.server 8000   # 開 http://localhost:8000
```

**手動檢查：**
- [ ] 通行碼 `Sela` 進入
- [ ] 肺癌 → 免疫 → 免疫檢查點抑制劑 → 看到子分型分組（非小細胞/小細胞）、單用/併用卡
- [ ] 搜 pembrolizumab 找得到（灰底為條文提及）
- [ ] 選一條 → 複製條文、資料清單可勾、列印正常
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

> 先前對話迭代曾用 V1.x 內部編號，現重定基為 V0.2.0（雛型階段）。超過 10 版砍最舊的，搬到 README.md。

---

## 七、下版候選工作（按優先序）

1. **更新資料流程驗證** — 下次母程式改版時實走第八節流程（維護命脈）
2. 肺腺癌等子型字串未對到 `subtitles`，目前歸「其他」→ 建子型對應表歸入非小細胞肺癌
3. P 碼／PD-L1 由「全表自選」升級為情境↔P 碼可信配對（保留全表兜底）
4. `form_no` 待母程式補齊後自動帶入（無需改本工具）

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

V0.5.0（雛型）：功能完整的獨立事審送審準備工具 OncoPA。蘋果風桌機優先 master-detail 工作台、手機響應收合、鍵盤可及性與 focus-visible 品質地板齊備；密碼 cbshow；已對齊 SELA Kit、正式 app logo 與雙 logo 制完成。版本自成一軌、不對齊母程式。下版第一優先是「下次母程式改版時實走資料更新流程」。

---

## 十、雙 logo 制（SELA Kit §8-9、§17）

- **App logo（主視覺）：** `favicon/app-logo.png`（512²，正式 logo）＋ `app-logo-master.png`（滿版方形母圖）。由 Gemini 依 `SELA-logo-prompt.md` 生成，Claude 走 §10.2 四步轉檔（取底色 #446e86 → sentinel floodfill 去白底+鋸齒環 → 純底色合成白 glyph → 生 16/32/180/192/512 + ico）。**重生方式：** 換新圖重跑 favicon/ 內處理腳本即可。logo 為點陣（含文字「CB Show」），無 SVG 版。
- **logo prompt：** `SELA-logo-prompt.md`（根目錄，範本 B 醫療型、北歐霧藍 #436f8a、壁虎 not a natural fit）。
- **SELA logo（品牌歸屬）：** footer 角標 `.sela-credit`，引用**獨立**的 `favicon/sela.svg`（不重用 favicon 引用）。
- **出現位置：** 登入頁、topbar、favicon、手機捷徑皆為 app logo；**SELA 主 logo 顯示於登入頁底部 + 頁尾 footer**（30px + 標籤，明確但仍為輔助）。
- **配色不撞：** app 北歐霧藍 vs SELA 橘，不同色。manifest `theme_color`/`icons` 用 app 自己的（#2c4f66 + app logo）。
