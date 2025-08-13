# WenetASR 项目

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-brightgreen)](https://www.python.org/)
[![WeNet Version](https://img.shields.io/badge/WeNet-Integrated-blue)](https://github.com/wenet-e2e/wenet)

## 项目概述

WenetASR 是一个基于 WeNet（端到端语音识别工具包）的实时语音识别（ASR）系统，结合了语音活动检测（VAD）功能。该项目旨在提供一个简单、高效的框架，用于从麦克风实时捕获音频，进行语音段检测，并使用预训练的 WeNet 模型进行中文语音识别。它特别适合实时应用场景，如语音助手、会议转录或语音命令系统。

### 项目背景

- **灵感来源**：WeNet 是阿里巴巴达摩院开源的端到端语音识别工具包，支持多种语言和模型架构。该项目将 WeNet 与 FunASR（阿里达摩院的另一个语音工具包）结合，实现实时 VAD 和 ASR。
- **核心功能**：
  - 实时麦克风音频捕获。
  - 语音活动检测（VAD）以识别有效语音段。
  - 基于 WeNet 的 ASR 模型进行语音转文本。
  - 支持自定义配置参数，如 VAD 阈值和 ASR 模型路径。
- **适用场景**：实时语音识别、噪声环境下的语音处理、集成到其他应用中的 ASR 模块。
- **技术栈**：
  - Python 3.10+。
  - 依赖库：sounddevice（音频捕获）、numpy（数据处理）、funasr（VAD 模型）、WeNet（ASR 模型）。
  - 模型：WeNet U2++ Conformer（ASR）和 FSMN-VAD（VAD）。

项目目录结构基于标准 Python 项目布局，并包含 WeNet 的子模块。详细目录见下文。

### 项目优势

- **实时性**：支持低延迟音频处理，适合在线应用。
- **易用性**：通过配置文件（cfg.ini）轻松调整参数，无需修改代码。
- **扩展性**：可以扩展到其他语言模型或多模型集成。
- **开源友好**：基于 Apache 2.0 许可，欢迎贡献。

### 项目局限性

- 当前主要支持中文 ASR（可扩展到其他语言）。
- 依赖 CPU/GPU 性能，实时处理可能在低端设备上受限。
- VAD 参数需要根据环境调优，以避免误检或漏检。

## 安装指南(运行环境搭建)

```bash
pip install -r req.info
```

### 先决条件

- **操作系统**：Linux（推荐 Ubuntu 20.04+）、Windows 或 macOS。
- **Python 版本**：3.8 或更高（使用 virtualenv 管理环境）。
- **硬件要求**：至少 4GB RAM；如果使用 GPU，需要 CUDA 11+。
- **麦克风设备**：确保系统有可用的音频输入设备（使用 `query_dev_infos.py` 检查）。

### 步骤 1: 克隆仓库

```bash
git clone https://github.com/201831771214/WenetASR.git  # 替换为实际仓库 URL
cd WenetASR
```

### 步骤 2: 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

### 步骤 3: 安装依赖

项目依赖 WeNet 和其他库。WeNet 已作为子目录包含，但需要安装其要求。

```bash
pip install -r wenet/requirements.txt
pip install sounddevice numpy funasr torch  # 额外依赖
# 如果使用 GPU：
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118
```

### 步骤 4: 下载模型

项目使用预训练模型，以包含在仓库中，也可以手动下载并放置到 `models/` 目录。
- **ASR 模型**：WeNet U2++ Conformer-16K（中文）。
  - 下载地址：https://wenet.org.cn/downloads?models=wenet (选择 U2++ Conformer 模型)。
  - 解压到 `models/ASR/WeNet-U2pp_Conformer-16K/`。
  - 确保包含 `final.zip`、`configuration.json` 和 `units.txt`。
- **VAD 模型**：FSMN-VAD。
  - 下载地址：https://github.com/funasr/funasr (从 ModelScope 下载 fsmn-vad)。
  - 放置到 `models/VAD/fsmn-vad/`，包含 `am.mvn`、`config.yaml` 等文件。

如果模型路径不同，请修改 `run.py` 中的路径变量。

### 步骤 5: 配置音频设备

运行 `model_utils/query_dev_infos.py` 检查可用设备：

```bash
python model_utils/query_dev_infos.py
```

在 `run.py` 中设置 `device=8`（替换为你的麦克风设备 ID）。

## 使用指南

### 快速启动

主脚本是 `run.py`，它启动实时语音识别。

```bash
python run.py
```

- 系统将开始监听麦克风。
- 检测到语音段后，进行 ASR 并输出结果到控制台和 `run.log`。
- 按 Ctrl+C 停止。

### 运行流程详解

1. **初始化**：
   - 加载配置文件 `configs/cfg.ini`。
   - 初始化 ASR 模型（ModelLoader 类）。
   - 初始化 VAD 模型（AutoModel from funasr）。

2. **音频捕获**：
   - 使用 sounddevice 以 48kHz 采样率捕获音频（可配置）。
   - 块大小：2048 * 50 = 102400 采样点（约 2 秒音频）。

3. **VAD 处理**：
   - 重采样到 16kHz。
   - 分块处理（chunk_size=200ms）。
   - 更新语音段：检测起始/结束时间，超时（800ms）强制结束段。
   - 参数详见下文配置部分。

4. **ASR 处理**：
   - 提取有效语音段。
   - 使用 WeNet 模型推理，输出文本和置信度。
   - 结果记录到日志。

5. **停止**：
   - KeyboardInterrupt 优雅退出。

### 示例输出（从 run.log）
```
2025-08-13 11:49:33,128 - __main__ - INFO - ASR Result: {'text': '喂', 'confidence': 0.8567727412431149}
2025-08-13 11:49:36,761 - __main__ - INFO - ASR Result: {'text': '喵', 'confidence': 0.04825797354399008}
2025-08-13 11:49:36,854 - __main__ - INFO - ASR Result: {'text': '你好', 'confidence': 0.9029370670130575}
```

### 高级使用

- **自定义音频文件**：修改 `run.py` 以支持文件输入（替换 InputStream）。
- **集成到其他项目**：导入 `model_classes/model_loader.py` 使用 ASR 功能。
- **多语言支持**：替换 ASR 模型为 WeNet 的其他语言版本（e.g., English）。

## 配置详解

配置文件：`configs/cfg.ini`（INI 格式，使用 `model_utils/inireader.py` 读取）。

### 示例 cfg.ini
```
[decibel_thres]
value = -45

[speech_noise_thres]
value = 0.6

[max_end_silence_time]
value = 800

[max_start_silence_time]
value = 3000

[speech_2_noise_ratio]
value = 1.2

[speech_noise_thresh_low]
value = -1.3

[speech_noise_thresh_high]
value = -0.15
```

### 参数解释

- **decibel_thres**：分贝阈值（默认 -45），低于此值的音频视为噪声。
- **speech_noise_thres**：语音/噪声阈值（默认 0.6），用于区分语音和噪声。
- **max_end_silence_time**：最大结束静默时间（ms，默认 800），超过则结束当前语音段。
- **max_start_silence_time**：最大起始静默时间（ms，默认 3000），用于忽略初始噪声。
- **speech_2_noise_ratio**：语音与噪声比率（默认 1.2），影响检测敏感度。
- **speech_noise_thresh_low/high**：噪声阈值范围（默认 -1.3 到 -0.15），用于动态调整。

修改后，重启脚本生效。使用 IniReader 类读取，确保键值对正确。

## 模型详解

### ASR 模型

- **路径**：`models/ASR/WeNet-U2pp_Conformer-16K/`。
- **架构**：U2++ Conformer（端到端 CTC/Attention 模型）。
- **输入**：16kHz 音频。
- **输出**：中文文本 + 置信度。
- **自定义**：beam_size=5（搜索宽度），可调整以平衡速度/准确率。
- **加载**：通过 `model_classes/model_loader.py` 的 ModelLoader 类。

### VAD 模型

- **路径**：`models/VAD/fsmn-vad/`。
- **架构**：FSMN（Feedforward Sequential Memory Network）。
- **输入**：16kHz 音频块。
- **输出**：语音段 [start_ms, end_ms]。
- **参数**：通过 AutoModel 初始化，支持自定义阈值。

模型文件包括权重（final.zip/am.mvn）、配置（configuration.json/config.yaml）和单位文件（units.txt）。

## 项目目录结构详解

```
WenetASR/
├── configs/                # 配置目录
│   └── cfg.ini             # 主配置文件
├── model_classes/          # 模型加载类
│   └── model_loader.py     # ASR 模型加载器
├── model_utils/            # 工具模块
│   ├── inireader.py        # INI 文件读取器
│   └── query_dev_infos.py  # 设备信息查询
├── models/                 # 模型目录
│   ├── ASR/                # ASR 模型
│   │   └── WeNet-U2pp_Conformer-16K/  # WeNet 模型文件
│   └── VAD/                # VAD 模型
│       └── fsmn-vad/       # FSMN-VAD 模型文件
├── wenet/                  # WeNet 子模块（克隆自官方仓库）
│   ├── examples/           # WeNet 示例
│   ├── runtime/            # WeNet 运行时
│   ├── tools/              # WeNet 工具
│   └── ...                 # 其他 WeNet 文件
├── run.py                  # 主脚本：实时 ASR
├── run.log                 # 运行日志
└── wenet_vad.png           # 运行结果图像
```

- **wenet/**：WeNet 完整克隆，包含训练、推理和工具。不要直接修改，除非贡献上游。
- **models/**：存储下载的模型，确保权限正确。

## 调试与日志

- **日志文件**：`run.log`（使用 logging 模块记录 INFO/ERROR）。
- **常见问题**：
  - **音频设备错误**：检查 device ID，确保麦克风可用。
  - **重采样错误**：音频长度太短（见日志），调整 chunk_size。
  - **模型加载失败**：确认路径和文件完整性。
  - **VAD 误检**：调低 speech_noise_thres 或增加 max_end_silence_time。
- **性能优化**：切换到 GPU（修改 device="cuda"），但需安装 CUDA 支持。

运行时监控 CPU/内存使用。如果延迟高，减少 chunk_slider。

## 贡献指南

欢迎贡献！请遵循以下步骤：
1. Fork 仓库。
2. 创建分支：`git checkout -b feature/new-feature`。
3. 提交更改：`git commit -m "Add new feature"`。
4. Push 并创建 Pull Request。
5. 确保代码风格一致（使用 flake8 检查）。

### 贡献领域

- 添加多语言支持。
- 优化实时性能（e.g., 异步处理）。
- 集成更多 VAD/ASR 模型。
- 改进文档或添加测试。

参考 WeNet 的 CONTRIBUTING.md。

## 许可证

本项目基于 Apache 2.0 许可。WeNet 子模块遵循其原许可（Apache 2.0）。

## 联系与支持

- **作者**：公众号"CrazyNET"。
- **问题**：在 GitHub Issues 提交。
- **更新**：定期检查 WeNet 和 FunASR 更新，以保持兼容性。

感谢使用 WenetASR！如果有疑问，请随时反馈。
