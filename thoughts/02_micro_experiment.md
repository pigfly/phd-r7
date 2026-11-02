# 02 · 5 秒微型实验：Hazard-aware resolution allocation（RQ1）

代码：`thoughts/exp/toy_optical.py` · 运行：`python3 thoughts/exp/toy_optical.py [sigma] [seed]` · 实测 **2.4–3.4 s**（M 系 Mac，CPU，numpy + Pillow）
输出：终端表格 + `thoughts/exp/results_v1.json`

## 1. 要验证的核心假设
> **H1**：在相同视觉预算下，按文本侧风险不均匀分配渲染分辨率，比均匀渲染显著降低 verbatim span 的静默错误，而 prose 只付很小代价（因为语言先验能"脑补"prose，却无法脑补随机 hash）。

**为什么先验证这个**：如果 H1 在一个"语言先验 + 视觉噪声"的最简机制里都不成立，那在真实 VLM 上更不会成立——toy 是最便宜的证伪器。

## 2. 模型结构（为什么这样搭）

```
text ──► renderer(Menlo 字体, 每字符 h×w 像素) ──► + 高斯噪声 σ ──► reader ──► 解码文本
              ▲                                                     │
              │ 每字符分辨率 = 分配策略决定                          └─ Viterbi(视觉似然 + λ·bigram 先验)
```

| 组件 | 实现 | 为什么 |
|---|---|---|
| Renderer | Pillow 用真实等宽字体 Menlo 画 42 个字符，BOX 下采样到 8 档分辨率 (4×2 … 14×7) | 真字体才有真实的形近混淆（0/o、1/l、b/6）；分辨率=每视觉 token 的字符密度的代理 |
| 视觉编码器 | 低分辨率字形 + 高斯噪声 σ | 最简"读不清"模型 |
| 语言先验 | 字符 bigram，从 Python stdlib docstring 估计（与测试 prose 不同模块） | 代替 VLM 的语言先验；它会把看不清的 hash "纠正"成像英文的串——正是静默错误的机制 |
| Reader | Viterbi 解码 | 先验 × 似然的精确 MAP，向量化后很快 |
| Hazard detector | regex + 16 窗口 Shannon 熵 ≥3.5（照搬 R-or-R） | 和你论文的 gate 一致，结论可迁移 |

**概念一句话**
- *Viterbi*：在"每个位置是什么字符"的所有组合里，用动态规划找出"看起来像 × 读起来通顺"乘积最大的那一个。
- *bigram 先验*：只看前一个字符来猜下一个字符的概率表。
- *静默错误 (silent corruption)*：输出错了，但格式完全合法（仍是 12 位 hex），下游无法察觉。
- *AUROC*：随机挑一个出错的 token 和一个没出错的 token，打分把前者排在前面的概率；0.5=瞎猜，1=完美。

## 3. 输入 / 输出
- **输入**：24k 字符流 = 测试 prose + 每 ~18 词插入 1 个 verbatim span（hex12 / UUID / 路径 / 6 位数，共 192 个）。
- **输出（每种分配策略）**：prose 字符错误率 (CER)、span 精确率 (exact)、静默错误率 (silent)、视觉成本（相对纯文本 token 的比值）。

## 4. 对照组（arms）
| arm | 含义 | 为什么要它 |
|---|---|---|
| uniform | 全部同一分辨率 | = R-or-R 的 always-image / 单冻结渲染器 |
| anchors | uniform + 被标 span 以文本 sidecar 给出（假设模型完美抄写） | = R-or-R 的 image+anchors；**对 baseline 是乐观的** |
| gated (v1) | 标记字符用一个固定"可读"档位，其余吃剩余预算 | 最朴素的不均匀分配 |
| **v2** | 每个标记 span 按**长度**选最便宜的档位使 `L·p_char ≤ ε=0.02`，p_char 由字形模板间距的 Gaussian 尾概率算出（**无标签**） | 我们的方法 |
| *@A | 预算 = uniform + anchor 的文本成本 | 回答"同样的钱，花在像素上还是 text anchor 上？" |

## 5. 预期现象 vs 实际观察

| 预期 | 实际（seed 0–3，σ=0.10） | 判定 |
|---|---|---|
| E1 均匀渲染复现 R-or-R 相图：prose 先存活、verbatim 先崩 | 14.2 字符/vtok：prose CER 0.022–0.025，span exact 0.31–0.38，silent 0.21–0.32（论文 Fable 未门控 silent 0.249） | ✅（σ 是为复现此现象**校准**的，见下） |
| E2 文本侧分数能预测哪里出错 | token 分数→错误 AUROC 0.72–0.81（论文 0.864） | ✅ 方向一致 |
| E3 **H1：同预算下 v2 ≫ uniform** | 14.2 ch/vtok：exact **0.31–0.38 → 0.92–0.95**，silent **0.21–0.32 → 0.01–0.03**，成本 0.241 vs 0.243；prose CER 0.022→~0.048 | ✅ 强信号 |
| E4 v2 比 uniform 更便宜也更准 | 以 9.1 ch/vtok 为预算：v2 实际只花 0.275（−27%），exact 0.84–0.89 → 0.94–0.97，代价 prose CER 0.002→0.022 | ✅ |
| E5 v2 打败 anchors | anchors（完美抄写假设）exact=1.000 但成本 0.53；v2@A 成本 0.43、exact 0.93–0.98 | ⚠️ **部分**：v2 更省 ~20%，但不如完美 anchors 精确 |
| — 意外 1 | v1 固定"3σ 可读档"在 exact≈0.85 封顶：长 UUID（36 字符）需要 per-char 错误 ≪ 1/36 | 🔁 催生了 v2（按长度定档） |
| — 意外 2 | seed 3：预算差一点点，prose 被挤到最低档 → CER 0.373（**离散档位悬崖**） | 🔁 v3 需加 prose 下限保护 |

## 6. 诚实的局限（必须写进任何后续文档）
1. **σ 被校准过**：σ∈{0.10,0.15,0.20} 中选了 0.10，因为只有它复现了 R-or-R 已报告的相图（E1）。H1（E3–E5）是在 σ 冻结**之后**才测的——这是"用已知事实校准、再预测未知"，不是调参刷结果；但仍需在真实 VLM 上复测。
2. **bigram 先验远弱于真实 VLM**；真实 VLM 对 prose 的脑补更强（prose 代价可能更小），对 hex 的"自信编造"也可能更强。
3. **anchors 假设完美抄写**（对 baseline 有利）；R-or-R 实测含 retry 也只有 0.955。
4. **成本汇率是假设**：256 px/vtoken、prose 4 字符/token、hex 2 字符/token。uniform vs v2 的比较**与汇率无关**（同像素预算），只有 vs anchors 依赖汇率。
5. 单次运行 seed 间波动约 ±0.05；头条效应（+0.55 exact）远大于此。
6. toy 里字号放大不影响版面；真实图片中混排字号会改变图像面积与行布局（计费按像素面积），需要实际 packing。
