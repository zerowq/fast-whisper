# ASR & TTS 轻量化流式模型调研报告 (Research Report on Lightweight Streaming ASR & TTS Models)

## 调研背景 (Background)

### 业务约束 (Business Context)

> [!NOTE]
> - **语言需求**: 英文 + 马来文都是刚需
> - **质量优先**: 不能只关注速度，音质同样重要
> - **马来语评估**: 团队无马来语母语者，马来语音质需谨慎评估
> - **当前方案**: Faster-Whisper + CosyVoice 2.0 + Meta MMS-TTS 已上线运行

### 调研目标 (Research Goals)

1. 支持流式输出 (Streaming output support)
2. 参数小、GPU 占用少 (Small parameters, low GPU usage)
3. 支持英语和马来语 (English and Malay language support)
4. **质量与速度并重** (Balance quality and speed)

---

## 1. ASR 模型调研对比 (ASR Model Comparison)

### 1.1 核心候选模型 (Core Candidate Models)

| 模型 (Model) | 研发主体 (Creator) | 参数量 (Params) | 显存占用 (VRAM) | 流式支持 (Streaming) | 核心优势 (Pros) | 局限性 (Cons) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Faster-Whisper (Small)** ⭐ | SYSTRAN / OpenAI | ~244M | ~1GB - 2GB | VAD 分段流式 | **精度极高**，多语言支持完美，马来语表现优秀。 | 需 VAD 组件实现流式。 |
| **Faster-Whisper (Tiny)** | SYSTRAN / OpenAI | **~39M** | **~200MB** | VAD 分段流式 | **极致轻量**，资源占用最低。 | 复杂场景精度下降。 |
| **SenseVoiceSmall** | 阿里巴巴 FunASR | **~244M** | **~1GB** | Chunk 流式 | **推理极快** (比 Whisper 快 5-15x)，自带情感/事件检测。 | 支持语言: 中/英/粤/日/韩，**不支持马来语**。 |
| **Paraformer-Streaming** | 阿里巴巴 FunASR | **~220M** | **~0.8GB** | **原生流式** | **专为流式设计**，端到端延迟极低。 | 主要支持中文，英语精度略逊于 Whisper。 |
| **Vosk (Small)** | AlphaCep | 50M - 100M | < 500MB | 原生流式 | 资源占用极低，支持 CPU 运行。 | 复杂度高时识别率下降。 |
| **NVIDIA Parakeet-TDT-0.6B** | NVIDIA | ~600M | ~2GB | 支持 | **速度极快** (RTFx=3386)，英语精度顶尖。 | 英语专用，不支持马来语。 |

### 1.2 流式能力说明 (Streaming Capability Notes)

> [!NOTE]
> **VAD 分段流式**: 需要配合 Voice Activity Detection 组件将音频切分为小段后逐段处理。延迟略高但精度更好。
> **原生 Chunk 流式**: 模型本身支持按块（如 200ms）持续处理，延迟最低，适合实时对话。

### 1.3 ASR 推荐 (ASR Recommendations)

> [!TIP]
> **综合推荐**: **Faster-Whisper (Small/Large)** ⭐
> - 精度业界顶尖，**唯一同时支持英语和马来语的高质量方案**
> - 多语言表现稳定，社区成熟
> - 如需极致轻量：可选 Tiny 版本 (~200MB)
>
> **备选（仅英语场景）**: **SenseVoiceSmall**
> - 速度快 5-15 倍，但不支持马来语

---

## 2. TTS 模型调研对比 (TTS Model Comparison)

### 2.1 核心候选模型 (Core Candidate Models)

| 模型 (Model) | 研发主体 (Creator) | 参数量 (Params) | 显存占用 (VRAM) | 流式支持 (Streaming) | 英语质量 | 马来语支持 | 核心优势 (Pros) | 局限性 (Cons) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CosyVoice2-0.5B** ⭐ | 阿里巴巴 FunAudioLLM | 500M | **6-8GB** | ✅ 150ms | ⭐⭐⭐⭐⭐ | ❌ | **音质顶尖**，零样本克隆能力极强。 | **显存占用最高**。 |
| **Meta MMS-TTS** ⭐ | Meta AI | ~300M | ~1GB | ❌ 非流式 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **马来语发音最纯正**，唯一稳定马来语方案。 | 不支持克隆，音色固定。 |
| **Kokoro-82M** | Hexgrad | **82M** | **< 500MB** | ✅ 支持 | ⭐⭐⭐⭐ | ❓ 待验证 | **极致轻量**，音质极佳，ONNX 跨平台支持。 | 马来语支持未明确。 |
| **MeloTTS** | MyShell | ~300M | ~1GB | ✅ 支持 | ⭐⭐⭐⭐ | ❓ 待验证 | **多语言支持好**，流式稳定。 | 音色丰富度略低于 CosyVoice。 |
| **XTTS-v2** | Coqui AI | ~400M | ~2.5GB | ✅ <150ms | ⭐⭐⭐⭐ | ⭐⭐⭐ | 支持 **17 种语言含马来语**，音色克隆能力强。 | 马来语质量需实测验证。 |
| **Piper TTS** | Home Assistant | < 100M | **< 200MB** | ✅ 实时 | ⭐⭐⭐ | ❓ | 专为嵌入式设计，极度省资源。 | 机械感稍重，不支持克隆。 |
| **Chatterbox-Turbo** | Resemble AI | 350M | ~2GB | ✅ <200ms | ⭐⭐⭐⭐ | ⭐⭐⭐ | 23+ 语言，支持笑声/咳嗽等副语言标签。 | 显存占用比 Kokoro 高。 |
| **Soprano-80M** | 开源社区 | **80M** | **< 1GB** | ✅ 超低延迟 | ⭐⭐⭐ | ❌ | 开源界最轻量之一，速度优先。 | 音色表现力弱，不支持克隆。 |

### 2.2 马来语支持分析 (Malay Language Support)

> [!IMPORTANT]
> **马来语 TTS 选项有限**:
> | 模型 | 马来语支持 | 质量评估 | 备注 |
> | :--- | :--- | :--- | :--- |
> | **Meta MMS-TTS** | ✅ 完美支持 | ⭐⭐⭐⭐⭐ | **唯一高质量稳定方案** |
> | **XTTS-v2** | ✅ 支持 | ⭐⭐⭐ (待验证) | 支持克隆，但质量需实测 |
> | **Chatterbox** | ✅ 支持 | ⭐⭐⭐ (待验证) | 23+ 语言支持 |
> | 其他模型 | ❌/❓ | - | 马来语支持不明确或不支持 |

### 2.3 TTS 推荐 (TTS Recommendations)

> [!TIP]
> **英语 TTS 推荐**:
> - **质量优先**: CosyVoice2-0.5B ⭐ (音质顶尖，但显存 6-8GB)
> - **轻量优先**: Kokoro-82M (< 500MB，音质优秀)
> - **均衡选择**: MeloTTS (~1GB，多语言稳定)
>
> **马来语 TTS 推荐**:
> - **首选**: Meta MMS-TTS ⭐ (唯一高质量稳定方案)
> - **备选**: XTTS-v2 (如需克隆能力，但质量需实测)

---

## 3. 显存预算对比 (VRAM Budget Comparison)

### 3.1 当前方案 vs 轻量方案

| 配置 | ASR | TTS (英语) | TTS (马来语) | Guardrails | 总计 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **当前方案** | Whisper Large (~3GB) | CosyVoice (6-8GB) | MMS (~1GB) | GPU (~0.5GB) | **10.5-12.5GB** |
| **轻量方案 A** | Whisper Small INT8 (~1GB) | Kokoro-82M (<0.5GB) | MMS (~1GB) | GPU (~0.5GB) | **~3GB** |
| **轻量方案 B** | Whisper Small (~1.5GB) | MeloTTS (~1GB) | MMS (~1GB) | GPU (~0.5GB) | **~4GB** |
| **极致轻量** | Whisper Tiny (~0.2GB) | Piper (<0.2GB) | MMS (~1GB) | GPU (~0.5GB) | **~2GB** |

### 3.2 显存节省分析

| 切换 | 节省显存 | 质量影响 |
| :--- | :--- | :--- |
| CosyVoice → Kokoro-82M | **-6GB** | 英语音质略降，但仍优秀 |
| CosyVoice → MeloTTS | **-5GB** | 英语音质可比，多语言更均衡 |
| Whisper Large → Small INT8 | **-2GB** | 精度略降，但仍足够 |

---

## 4. 综合推荐 (Final Recommendations)

### 4.1 按场景推荐

| 场景 | ASR | TTS (英语) | TTS (马来语) | 总显存 |
| :--- | :--- | :--- | :--- | :--- |
| **质量优先** | Faster-Whisper Large | CosyVoice 2.0 | Meta MMS | ~12GB |
| **显存紧缺** | Faster-Whisper Small INT8 | Kokoro-82M | Meta MMS | ~3GB |
| **均衡配置** | Faster-Whisper Small | MeloTTS | Meta MMS | ~4GB |
| **极致轻量** | Faster-Whisper Tiny | Piper TTS | Meta MMS | ~2GB |

### 4.2 核心结论

> [!IMPORTANT]
> 1. **ASR**: Faster-Whisper 是英语+马来语双语的最佳选择，其他方案（SenseVoice/Paraformer）不支持马来语。
> 2. **TTS 英语**: CosyVoice 质量最好但显存高；Kokoro-82M 是轻量化的最佳替代。
> 3. **TTS 马来语**: Meta MMS-TTS 是**唯一高质量选择**，暂无可靠替代品。
> 4. **显存优化**: 主要通过替换英语 TTS 实现，可节省 5-6GB。

---

## 5. 最终结论与验证建议 (Final Conclusions & Validation Recommendations)

### 5.1 ASR 结论：不需要对比验证，当前方案已是最优

| 项目 | 说明 |
| :--- | :--- |
| **当前方案** | Faster-Whisper |
| **是否需要对比** | ❌ **不需要** |
| **结论** | ✅ **已是最优方案** |

**理由**：
1. **唯一满足双语需求**：在所有候选模型中，Faster-Whisper 是**唯一同时高质量支持英语和马来语**的方案
   - SenseVoiceSmall：不支持马来语
   - Paraformer：主要支持中文，英语/马来语弱
   - NVIDIA Parakeet：仅英语
2. **精度业界顶尖**：基于 OpenAI Whisper，多语言 WER 最低
3. **社区成熟稳定**：开源活跃，生产验证充分

> [!TIP]
> **优化建议**：如需降低显存，可从 Large → Small + INT8 (3GB → 1GB)，精度损失可接受。

---

### 5.2 TTS 英语结论：建议验证 Kokoro-82M 作为轻量化替代

| 项目 | 说明 |
| :--- | :--- |
| **当前方案** | CosyVoice 2.0 (6-8GB) |
| **是否需要对比** | ⚠️ **建议验证** |
| **建议验证模型** | **Kokoro-82M** (< 500MB) |

**理由**：
1. **当前方案显存过高**：CosyVoice 占用 6-8GB，是单卡部署的最大瓶颈
2. **Kokoro-82M 潜力极高**：
   - 显存仅 < 500MB，**节省 90%+**
   - 音质评价极高，英语表现优秀
   - 支持流式，ONNX 跨平台
3. **验证成本低**：部署简单，可快速对比音质

> [!IMPORTANT]
> **验证任务**：建议用相同英语文本，对比 CosyVoice vs Kokoro-82M 的音质差异。如可接受，可大幅降低显存。

---

### 5.3 TTS 马来语结论：不需要对比验证，当前方案是唯一选择

| 项目 | 说明 |
| :--- | :--- |
| **当前方案** | Meta MMS-TTS |
| **是否需要对比** | ❌ **不需要** |
| **结论** | ✅ **唯一高质量选择** |

**理由**：
1. **唯一高质量马来语方案**：在所有候选模型中，MMS-TTS 是**唯一明确支持马来语且质量稳定**的方案
2. **无可靠替代品**：
   - XTTS-v2：声称支持马来语，但质量未经验证，且需马来语母语者评估
   - 其他模型：均不支持或未明确支持马来语
3. **替换风险极高**：团队无马来语母语者，无法评估替换后的音质

> [!CAUTION]
> **强烈建议维持 MMS-TTS**，除非未来有马来语母语同事可协助评估其他方案。

---

### 5.4 总结

| 服务 | 当前方案 | 结论 | 行动建议 |
| :--- | :--- | :--- | :--- |
| **ASR** | Faster-Whisper | ✅ 已是最优 | 无需对比，可选优化显存 |
| **TTS 英语** | CosyVoice 2.0 | ⚠️ 显存过高 | **建议验证 Kokoro-82M** |
| **TTS 马来语** | Meta MMS-TTS | ✅ 唯一选择 | 无需对比，维持现状 |

---

## 附录：数据来源 (Data Sources)

- Faster-Whisper: [SYSTRAN GitHub](https://github.com/SYSTRAN/faster-whisper)
- CosyVoice: [FunAudioLLM](https://github.com/FunAudioLLM/CosyVoice)
- Meta MMS-TTS: [Meta Research](https://github.com/facebookresearch/fairseq/tree/main/examples/mms)
- SenseVoice: [FunASR GitHub](https://github.com/modelscope/FunASR)
- Kokoro: [Hugging Face](https://huggingface.co/hexgrad/Kokoro-82M)
- XTTS-v2: [Coqui TTS](https://github.com/coqui-ai/TTS)
- MeloTTS: [MyShell GitHub](https://github.com/myshell-ai/MeloTTS)
- Piper: [Home Assistant](https://github.com/rhasspy/piper)
