# ASR Efficiency & Accuracy Report / 语音识别效率与准确率汇总报告

## 1. Executive Summary / 核心结论

The `faster-whisper-asr` service utilizes the `Large-V3` model, the most advanced open-source ASR engine. By leveraging **CTranslate2** optimization, it achieves 4x-10x speed improvement over the original OpenAI Whisper implementation while maintaining the same accuracy.

`faster-whisper-asr` 服务采用 `Large-V3` 模型，这是目前最先进的开源 ASR 引擎。通过 **CTranslate2** 优化技术，在保持相同准确率的前提下，其推理速度比原始 OpenAI Whisper 快 4 到 10 倍。

---

## 2. Performance Comparison (Efficiency) / 效率对比

### 2.1 Processing Speed for a "200KB" Audio File / 200KB 音频文件处理耗时
*Assumption: 16kHz, Mono, 16-bit PCM (standard voice quality).*
*假设：16kHz, 单声道, 16位 PCM (标准语音质量)。*

| Metric (指标) | CPU Mode (Intel/AMD) | GPU Mode (NVIDIA T4/A10) | Notes (说明) |
| :--- | :--- | :--- | :--- |
| **Duration (音频时长)** | ~6.5 Seconds | ~6.5 Seconds | - |
| **Inference Time (识别耗时)** | ~1.5 - 3 Seconds | **~0.1 - 0.3 Seconds** | Near instantaneous on GPU. / GPU 上几乎瞬时完成。 |
| **Real-Time Factor (RTF)** | ~0.3 - 0.5 | **~0.02 - 0.05** | Lower is better. / 越低越好。 |

### 2.2 Throughput (吞吐量)
- **Hourly Processing**: One NVIDIA A10 GPU can process approximately **30-50 hours** of audio per hour of wall-clock time.
- **每小时处理量**: 一块 NVIDIA A10 显卡每小时可处理约 **30-50 小时** 的音频数据。

---

## 3. Accuracy Benchmarks / 准确率指标 (WER)

The `Large-V3` model is the industry benchmark for zero-shot ASR performance.
`Large-V3` 模型是零样本 ASR 性能的行业标杆。

| Language (语言) | Word Error Rate (WER) / 字错率 | Quality Level (质量分) |
| :--- | :--- | :--- |
| **English (英语)** | < 4.2% | Excellent / 极佳 |
| **Chinese (中文)** | < 6.5% | High / 高 |
| **Malay (马来语)** | < 12.0% | Good / 良好 |

*Note: Accuracy significantly improves with higher audio quality (noise reduction). / 注意：准确率随音频质量（降噪效果）的提升而显著提高。*

---

## 4. Why Faster-Whisper? / 为什么选择 Faster-Whisper?

1.  **Speed (速度)**: CTranslate2 quantization (int8/float16) makes it feasible for production high-concurrency. / CTranslate2 量化技术使其适用于高性能高并发场景。
2.  **Accuracy (准确性)**: No loss in accuracy compared to the 1.5B parameter original model. / 与 15 亿参数的原始模型相比，准确率无损。
3.  **Privacy (隐私)**: 100% Offline, no data leaves the private cloud. / 100% 离线，数据不流出私有云。
