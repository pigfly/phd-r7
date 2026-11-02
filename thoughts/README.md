# thoughts/ — 研究记录（免训练 token 压缩 · 光学上下文压缩）

| 文件 | 内容 |
|---|---|
| `01_research_questions.md` | 5 个研究问题：重要性 / 空白 / 切入点 / 为什么是它 |
| `02_micro_experiment.md` | 5 秒 toy 实验：模型结构、输入输出、预期 vs 实际 |
| `03_decision_log.md` | 每轮"看到 → 意味着 → 下一步"，以及提前写死的 kill criteria |
| `04_real_pilot_results.md` | 真实 VLM pilot：RQ1 成立，RQ2 弱 |
| `exp/real/` | 渲染 / 评分代码与 pilot 数据 |
| `05_paper_outline.md` | 论文骨架：主张、证据、图表、缺口 |
| `glossary.md` | 一句话概念解释 |
| `exp/toy_optical.py` | 实验代码（`python3 exp/toy_optical.py [sigma=0.10] [seed=0]`，~3 s） |
| `exp/results_v1.json` | seed 0 的完整结果 |

## 当前状态（2026-11-01）
- **主线**：*The renderer knows where the hazard is* —— 用文本侧风险图做免训练的像素/视觉 token 分配。
- **RQ1 toy 结果**：同视觉预算下，span 精确率 0.31–0.38 → **0.92–0.95**，静默错误 0.21–0.32 → **0.01–0.03**，prose CER 0.02→0.05（4 seeds）。
- **已知问题**：离散档位悬崖（需 prose 下限）；anchors（完美抄写假设）仍更精确但贵 ~20%。
- **真实 VLM pilot（Claude 子代理当读者，$0）**：同视觉 token 下 hazard 分配使标识符精确率 0.32→**0.78**（5px）、0.79→**0.99**（6px），静默错误 0.50→0.15 / 0.15→0.00，prose 无可见代价；RQ2（不折断标识符）效应小且不显著。
- **第二家 VLM（MiniMax-M3）复现**：C−A = +47 / +51 点，6px 时 0.46→**0.97**、静默错误→0；弱读者收益更大；5px 弱读者可能有 prose 代价（不显著）。
- **第二轮（N=42、2 读者）**：C−A 全部显著（+16…+52 点）；prose 下限变体 C' 更差（−13…−24），无 prose 收益；anchors 只在极高密度下明显更好，14 ch/vtok 时 C≈D 但便宜 41%；anchors 会显著降低 MiniMax 的 prose 读取。
- **第三轮**：C−A 在真实数据上也显著（+17/+24）；合成数据无 prose 代价，真实数据有（−13/−21，原因：整条清单行被放大）；anchors 使 MiniMax 的 prose 暴跌（两轮复现）；CD 无独立价值；允许 "[unreadable]" 不降低静默错误（模型不知道自己读错）。
- **第四轮（2026-11-02）**：C2 子串放大预检无版面收益（未跑读者）；run4_real 复现真实数据 C−A ids +0.21 / prose −0.14；C' 保 prose 但 ids 只 +0.08 → 真实数据是可调权衡。Claude 子代理的 prose 答错多来自其他图的名字（跨图污染），prose 以 MiniMax 为准。
- **第五轮**：+1px prose 行距（arm L）不能修复 prose 代价（同 item L−C = 0.00）。真实数据 3 个 seed：C−A ids +0.15…+0.21（全显著），prose −0.21/−0.14/0.00。→ 按权衡写（C vs C'）。
- **第六轮（多模型 + RULER）**：新增 5 个 OpenRouter 读者（Sonnet 5.5、Gemini 3.5 flash-lite、GPT-6-luna、Qwen3-VL-235B、Llama-4）。已有数据 C−A 27/27 格显著；RULER-NIAH 4 个子任务 × 2 密度 × 6 读者，M−A 33/36 格显著，阴性对照 ≈0；真实计费 M ≤ A。新 arm M（prose 按字符折行）在紧预算下也能工作 → 设为方法默认。
- **第七轮（E1/E2/E3）**：纯文本基线 ≈1.00、RULER 上图片省 3–8× token；密度相图呈倒 U、峰值随读者强弱平移；**LongBench QA 上 M 平均 −0.05（3/12 显著）**——M 用 prose 分辨率换标识符精度，不是免费的。
- **目标**：CVPR 2027 / IJCAI 2027；先做完实验再写论文。
- **第八轮（只做长文本）**：严格检测器（不放大年份等）+ 全局缩放 = **arm S，方法默认**：LongBench 留出 0/12 格掉点，RULER 5px +0.57、6px +0.40，计费比 A 少 11%。M-local（L）无额外收益。
- **第九轮**：长上下文 32K–128K（多图）S−A +0.45…+0.49，A 随长度退化而 S 不退化，S 比文本省 5–8×；S ≫ 均匀配置搜索 / 降采样；**但稀疏危险串下 anchors 更准、只贵 5%**。
- **第十轮（密度扫描）**：没有"S 胜 anchors"的交叉点；**X = S + anchors 最优**：稀疏时近乎满分且比均匀渲染还便宜（anchors 近乎免费），中密度比 anchors 高 +0.10；k≥64 一切图像方案失效 → 退回文本。定位改为"渲染端重分配与 anchors 互补"。
- **第十一轮**：LongBench QA 上 X（S + anchors）0/12 格掉点、平均 +0.009 → **X 定为最终方法**（S 为无文本旁路变体）。短文本上"anchors 伤害弱读者"的发现没有延伸到长文本 QA。

## 参考
- R-or-R：`ref/main.pdf`, `ref/appendix.pdf`
- [DeepSeek-OCR 2 (2601.20552)](https://arxiv.org/abs/2601.20552)
- [RTPrune (2605.00392)](https://arxiv.org/abs/2605.00392) — DeepSeek-OCR 上的免训练剪枝，按文本密度定剪枝率
- [Optical Context Compression Is Just (Bad) Autoencoding (2512.03643)](https://arxiv.org/abs/2512.03643)
- [PIO-FVLM (2602.04657)](https://arxiv.org/abs/2602.04657), [VPRune (2609.24485)](https://arxiv.org/abs/2609.24485v1), [PruneSID (2603.09480)](https://arxiv.org/html/2603.09480v2) — 免训练视觉 token 剪枝
- [FCoT-VL (2502.18512)](https://arxiv.org/pdf/2502.18512) — 免训练剪枝在文本密集基准上掉点
- [Glyph (2510.17800)](https://arxiv.org/pdf/2510.17800), [DeepSeek-OCR (2510.18234)](https://arxiv.org/pdf/2510.18234)
- KV 侧免训练：[Expected Attention (2510.00636)](https://arxiv.org/pdf/2510.00636), [PagedEviction (2509.04377)](https://arxiv.org/pdf/2509.04377), [DepthKV (2604.24647)](https://arxiv.org/pdf/2604.24647)
