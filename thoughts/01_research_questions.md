# 01 · 研究问题（Research Questions）

> 起点：`ref/main.pdf`（*Render or Retain*，下称 **R-or-R**：零训练、黑盒、按 block 决定 text / image / image+anchors，加 check-and-retry）
> 与 arXiv 2601.20552（**DeepSeek-OCR 2**：DeepEncoder V2 用 learnable *causal flow queries* 按语义重排视觉 token，视觉 token 预算 256–1120 可变，OmniDocBench 87.36→91.09，reading-order edit distance 0.085→0.057）。
> 领域约束：**no training**（压缩器/路由器都不训练）。

## 一条主线（为什么这 5 个问题放在一起）

R-or-R 把渲染器当成"冻结的黑箱"，只做 **离散的 block 级路由**；DeepSeek-OCR 2 证明 **按内容分配视觉 token / 调整阅读顺序** 很值钱，但它是靠训练实现的。
两者之间的空白是：**渲染器本身就"知道"每个字符画在哪里、有多危险**——这是一张免费的、文本侧的、像素级的风险图。
👉 主论点草案：*"The renderer knows where the hazard is."* 用文本侧风险图在**不训练、不看模型内部**的前提下，去分配像素（黑盒）或保护视觉 token（白盒）。

**为什么是这条主线**：它直接接在你已发表/在投工作的 Limitations（"all results use one frozen renderer"、"gist closure 52.1%"）上，复用你已有的 gate、renderer、评测代码，审稿人一眼能看出增量，且每一步都能用小实验快速证伪。

---

## RQ1 ★（首选，已做 toy 验证）Hazard-aware resolution allocation
**一句话**：在**固定视觉 token 预算**下，把渲染分辨率按文本侧风险**不均匀分配**（高熵 verbatim span 用大字号、普通 prose 用小字号），能否比均匀渲染和 anchor sidecar 更省、更不容易静默出错？

- **为什么重要**：R-or-R 的路由是"整块 text 或整块 image"三选一，粒度太粗——一个 6000 字符的 log block 里可能只有 3 个 hash，却因此整块退回 text 或付 anchor 的 text token 钱（hex 在 BPE 下约 2 字符/token，很贵）。像素比 text token 便宜得多。
- **空白**：DeepSeek-OCR 2 / Glyph 的自适应预算都要训练；R-or-R 用单一冻结渲染器；RTPrune 按"文本密度"决定剪枝比例但不认 verbatim 风险。**没人做过黑盒下的 span 级分辨率分配**。
- **切入点**：只改渲染器——对 entropy detector 标出的 span 放大字号（或加行距、独占一行），其余 prose 缩小；用 `count_tokens` 做反事实计费，与 uniform / anchors 在**相同计费**下比 T-A 精确率与静默错误率。
- **为什么是这个切入点**：零新依赖（渲染器、gate、计费、评测都在你 repo 的 `render/`, `gates/`, `economics/` 里），一个 API 小 pilot（~$10–20）就能证伪。

## RQ2 Reading-order-aware layout（DeepSeek-OCR 2 的免训练版）
**一句话**：黑盒 VLM 的编码器无法重排 token，那么**在渲染前重排版面**（不在标识符中间折行、表格对齐、单栏流式）能否在同等密度下降低失败率？

- **为什么重要**：DeepSeek-OCR 2 的最大收益正来自阅读顺序（edit distance −33%），说明"raster 扫描顺序 ≠ 语义顺序"是真实瓶颈。
- **空白**：R-or-R 冻结了 312 列的版式，长 UUID/路径很可能被折到两行——这种"跨行标识符"的失败从未被单独测量。
- **切入点**：先做**零成本的事后分析**：在已有 T-A 结果里把 span 分成"跨行 vs 不跨行"，比较失败率。若差异显著，再做 no-break 渲染的 A/B。
- **为什么是这个切入点**：不用新 API 花费，只用已有日志就能判断这个方向值不值得做。

## RQ3 Training-free semantic-drift verification
**一句话**：check-and-retry 只能抓 verbatim 错误，能否用**免训练的跨通道一致性**（image 回答 vs 极短 text 抽取式 sidecar 的关键主张）检测 gist 类的语义漂移？

- **为什么重要**：R-or-R 自己承认 T-E 只闭合了 52.1% 的 gap，语义漂移占 4.1–20.1%，是论文最大的未解问题。
- **空白**：现有 verifier 都是字符串匹配；语义级验证通常要训练一个 NLI/判别器。
- **切入点**：在 T-E 上，用文本侧 TF-IDF 抽 top-k 关键词/数字作为 "claim sidecar"，检查回答是否与之矛盾；报告检测 AUROC。
- **为什么排第三**：价值高但更难做干净（"语义错误"的标注本身有噪声），适合作为 RQ1 之后的第二篇。

## RQ4 Delete vs Demote vs Retain：三通道率失真路由
**一句话**：对每个 span 在 **删除**（LLMLingua 式，低 surprisal）、**降级**（渲染成图）、**保留**（原文）三者间做统一的免训练决策，能否支配任何单一通道？

- **为什么重要**：直接回应 *"Optical context compression is just (bad) autoencoding"*（Lee et al. 2512.03643）的批评——不是二选一，而是各取所长。
- **空白**：R-or-R 只在相同预算下比了 LongLLMLingua（−5.2 / −13.9），没有把两者组合。
- **切入点**：用小开源 LM 算 token surprisal + 你的 hazard gate，三分类路由；toy 模型可直接扩展（加"删除"通道）。
- **为什么排第四**：组合空间大，容易变成工程堆砌；需要 RQ1 先确立"span 级"这个粒度是有效的。

## RQ5 White-box：用文本侧风险图指导免训练视觉 token 剪枝
**一句话**：在开源 OCR-VLM（DeepSeek-OCR/OCR 2、Qwen2.5-VL）上，用渲染器给出的"字符→patch"坐标把高风险 span 所在的视觉 token **保护起来**，再做 RTPrune/PruneSID 式免训练剪枝，能否在同等剪枝率下消除 verbatim 损伤？

- **为什么重要**：RTPrune 作者自己警告其方法不适用于高风险场景（信息丢失）；而我们**精确知道**哪些 patch 装着 hash——这是任何纯视觉剪枝方法都拿不到的先验。
- **空白**：现有剪枝的重要性分数全来自视觉侧（attention、norm、相似度），没有任何方法利用"图片是我们自己渲染的"这一事实。
- **切入点**：DeepSeek-OCR 开源推理 + 简单 top-k 剪枝基线 + "受保护 token 集合"；T-A 风格合成数据。
- **为什么放这里**：与 RQ1 是**同一主张的白盒版本**——RQ1 分配像素、RQ5 分配 token。两者合起来就是一篇完整论文的黑盒+白盒双证据。

---

## 优先级与理由

| 顺序 | 问题 | 理由 |
|---|---|---|
| 1 | RQ1 | toy 已显示强信号；最省钱；直接延伸你的论文 |
| 2 | RQ2（事后分析部分） | 零成本，可与 RQ1 并行 |
| 3 | RQ5 | 同一论点的白盒证据，需要 GPU 但无 API 费用 |
| 4 | RQ3 | 第二篇论文候选 |
| 5 | RQ4 | 等粒度问题定下来再做 |

**会让我改变排序的信号**：见 `03_decision_log.md` 的 kill criteria。
