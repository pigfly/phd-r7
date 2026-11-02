# 05 · 论文骨架（草稿 v0，2026-11-01）

**暂定标题**：*Spend Pixels Where It Hurts: Training-Free Hazard-Aware Resolution Allocation for Optical Context Compression*
（备选：*The Renderer Knows Where the Hazard Is*）
**定位**：R-or-R 的直接续作 / workshop 或 Findings 短文（4–8 页）。零训练、黑盒、只改渲染器。

## 一句话贡献
在**相同视觉 token 预算**下，按文本侧风险图把渲染分辨率从 prose 挪到高熵 verbatim span，可把 verbatim 精确率提升 17–58 点、把静默错误降到接近 0，跨 2 个商用 VLM、跨合成与真实数据；而文本 anchor sidecar 虽更准，却贵 70–100% 且会让弱读者"停止看图"。

## 主张 → 证据映射

| # | 主张 | 证据（`04_real_pilot_results.md`） | 状态 |
|---|---|---|---|
| C1 | 同预算下 hazard 渲染 ≫ 均匀渲染（verbatim） | 3 轮 × 2 读者 × 2 密度 + 真实数据，C−A 全部显著（+16…+58） | ✅ |
| C2 | 主要收益来自**分配**而非排版（不折断） | B−A n.s.（+4…+8）；C−B 显著 | ✅（N=12，可补） |
| C3 | 放大幅度关键，prose 下限无益 | C−C' +13/+24；C' prose 无改善 | ✅ |
| C4 | 与 anchors 的 Pareto：中等密度下 C≈anchors，便宜 41%；极高密度仍需 anchors | run2/run3 D vs C | ✅ |
| C5 | anchors 对弱读者的副作用：prose 读取崩溃 | MiniMax D/CD prose −13…−50（短文本探针）；**长文本 LongBench QA 上不成立**（MiniMax K/X +0.12） | ⚠️ 只限短文本探针 |
| C6 | 静默错误非 prompt 产物：模型不知道自己读错 | "[unreadable]" 变体放弃率 ≤6%、静默不降 | ✅ |
| C7 | 合成数据上无 prose 代价 | 3 探针，4 格中 3 格 n.s. | ⚠️ Claude 6px 临界 |
| C8 | 真实数据：verbatim ↔ prose 是可调权衡（s_lo 旋钮） | run3/run4_real：C −14/−21 prose；C' prose n.s. 但 ids 只 +8；C2 子串放大预检无版面收益；+1px 行距（L）无效；3 seed 均值 prose ≈ −12 | ⚠️ 按权衡写 |
| C10 | 跨 7 个读者（含 2 个开源）+ 公开 benchmark RULER-NIAH 成立；阴性对照无效应 | 第六轮：27/27 + 33/36 格显著 | ✅ |
| C11 | 真实计费下不更贵：M 比 A 便宜 0–20% | OpenRouter usage.prompt_tokens | ✅ |
| C12 | 收益随密度呈倒 U，峰值随读者强弱平移（机理） | E2 相图 6 读者 × 4 密度 | ✅ |
| C13 | 普通 QA 上无害（方法 S） | LongBench 留出：S−A +0.000，0/12 显著为负 | ✅ |
| C14 | 收益来自检测器精度而非局部缩放 | S ≥ M（RULER 5px 137%），L 在 6px 只有 84% | ✅ 消融 |
| C15 | 长上下文（32K–128K、多图）收益不衰减，A 随长度退化 | 第九轮 46/54 格显著 | ✅ |
| C16 | S ≫ 黑盒均匀 baseline（字体/字号搜索、降采样） | 第九轮 0/72 格更差 | ✅ |
| C17 | 单独 S 不如 anchors；S + anchors（X）在 k≤16 最优：近乎免费的 anchors、中密度更准 | 第十轮密度扫描 | ✅ 定位改为"互补" |
| C18 | 高密度（k≥64）所有图像方案失效 → 需路由回文本 | 第十轮 | ✅ 边界 |
| C19 | 最终方法 X 在普通 QA 上无害 | LongBench 留出 X−A +0.009，0/12 显著为负 | ✅ |
| C9 | 子代理读者的 prose 指标被跨图记忆污染 | Claude 错答 50–100% 来自名字池，MiniMax 0–10% | ✅ 方法学告诫 |

## 结构
1. **Introduction** — 光学压缩省钱但 verbatim 静默出错；R-or-R 只能整块退回文本或付 anchor；我们问：能否在**图像内部**重新分配预算？
2. **Related work** — 光学压缩（DeepSeek-OCR/OCR 2、Glyph、Text-or-Pixels）；免训练 token 剪枝（RTPrune、PruneSID…，均只看视觉侧）；R-or-R（block 级路由 + anchors）；内容自适应预算（DeepSeek-OCR 2 需训练）。
3. **Method** — 文本侧 hazard 检测（regex + 窗口熵）→ 预算约束下的字号分配（prose 最小可读、hazard 最大可放）→ 可选残余 anchors。视觉 token 公式 `⌈w/28⌉×⌈h/28⌉`。
4. **Setup** — 合成 T-A 族 + 真实包清单数据；2 读者（Claude、MiniMax-M3）；拉丁方防泄漏（**方法学贡献**：校准 1 显示跨图泄漏可把 29% 抬到 100%）；配对 bootstrap。
5. **Results** — 表 1 主结果（C−A）；图 1 Pareto（成本 vs 精确率，两读者两密度）；表 2 消融（B、C'、CD）；图 2 anchors 副作用；§ prompt 稳健性。
6. **Limitations** — 2 个读者；每格 N=30–42；文本 token 成本估算；子代理读者通道；真实数据 prose 代价（若 C2 未修复）。

## 图表清单
- 图 1：Pareto 散点（x=总 token，y=标识符精确率；A/C/CD/D；两读者 × 两密度）← `analysis.json`、`analysis3.json`
- 图 2：prose 探针准确率 by arm（突出 MiniMax 在 D/CD 的崩溃）
- 表 1：C−A 配对差汇总（所有条件）
- 附录：渲染示例图（A vs C 同一 item）、校准相图

## 投稿前缺口（按优先级）
1. ~~C2 子串级放大~~（预检证伪）、~~+1px 行距~~（证伪）→ C8 按权衡写，图 1 加真实数据前沿 A/C/C'/L。Claude 读者协议改为每图一个子代理。
2. ~~第 3 个读者~~ ✅ 已有 7 个读者（Qwen3-VL、Llama-4 为开源权重）。
3. ~~核验 token 成本~~ ✅ 视觉侧已用厂商真实计费；anchors 文本侧仍是估算，可用 usage 补。
4. 每格 N 提到 ≥50 以收紧 prose CI。
