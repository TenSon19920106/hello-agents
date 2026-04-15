# PBC-Analysis — 季度工作叙述 → 固定 JSON → 绩效流程接口

> 基于 HelloAgents：从用户粘贴的一段话或 `data/` 下的工作总结文件，梳理为统一 PBC JSON，并可选择调用 HTTP 接口同步「绩效制订」或「反馈」流程。

## 项目简介

企业内部 PBC（Personal Business Commitment）或季度回顾，常见形态是员工自由撰写。本工具用 LLM 做**结构化抽取与归纳**，输出**固定键名**的 JSON，便于对接现有绩效系统（POST 到网关即可）。若未配置接口地址，默认**干跑**（只生成文件、不外呼）。

## 核心功能

- 从**纯文本**或 **data/ 内文本文件**读取本季度工作情况
- 使用 **HelloAgents `SimpleAgent`** 生成符合约定的 **PBC JSON**（失败时自动进入**校验/修复**第二轮）
- **信息不足时追问**：`src/completeness.py` 中 `list_information_gaps` 做规则检查；`USER_SUPPLEMENT` 合并原文后可再次结构化（见 `main.ipynb` 第 2.5 节）
- 轻量 **`validate_pbc_payload`** 校验（不引入 jsonschema）
- 工具：**读文件**、**提交绩效制订**、**提交绩效反馈**（`requests` POST + Bearer Token）
- 将结果写入 `outputs/runtime/pbc_payload.json`（该目录已 `.gitignore`，避免误提交大文件）

## 固定 JSON 结构

字段说明见 `src/schema.py` 中的 `SCHEMA_DOC` 与 `validate_pbc_payload`。若你司字段不同，请**只改** `schema.py` 的校验与 `extract.py` 中的提示词，保持与接口文档一致。

## 技术栈

- HelloAgents（`SimpleAgent` + `HelloAgentsLLM`）
- `python-dotenv`、`requests`
- Jupyter：`main.ipynb` 演示端到端流程
- Streamlit：`app_streamlit.py` 提供**成品展示页**（表单 + 生成 + 下载 JSON）

## 快速开始

### 环境要求

- Python 3.10+
- 可访问的 LLM API（与 HelloAgents 环境变量一致）

### 安装依赖

```bash
cd Co-creation-projects/TenSon19920106-PBC-Analysis
pip install -r requirements.txt
```

### 配置

```bash
cp .env.example .env
# 编辑 .env：填入 LLM_API_KEY 等；若已有绩效网关，填写 PBC_PLANNING_URL / PBC_FEEDBACK_URL / PBC_API_TOKEN
```

### 运行

```bash
jupyter lab
# 打开 main.ipynb，自上而下运行
```

### 成品展示（答辩/演示推荐）

```bash
cd Co-creation-projects/TenSon19920106-PBC-Analysis
pip install -r requirements.txt
streamlit run app_streamlit.py
```

浏览器打开后：在侧边栏填写 **工号 / 考核年份 / 考核季度**，粘贴工作总结，点击 **生成 JSON**，可预览、下载，并写入 `outputs/runtime/pbc_payload.json`。页面底部提供 **「更新绩效制订」**：在 `.env` 配置 `PBC_PLANNING_URL`（及可选 `PBC_API_TOKEN`）后，可将最近一次生成的 JSON **POST** 到绩效制订接口。

## 对接说明

- **PBC_PLANNING_URL**：绩效制订流程接收端（示例：`https://hr.example.com/api/pbc/planning`）
- **PBC_FEEDBACK_URL**：绩效反馈流程接收端
- **PBC_API_TOKEN**：可选，`Authorization: Bearer ...`

若网关需要额外头字段（如 `X-Employee-Id`），可在 `src/api_client.py` 中扩展 `_headers`。

## 项目亮点

- 结构化与 HTTP 提交解耦，便于单元测试与联调
- 读文件工具限制在 `data/` 目录，降低路径遍历风险
- 未配置 URL 时安全干跑，适合毕业设计演示与评审

## 许可证

MIT License

## 作者

- GitHub: [@TenSon19920106](https://github.com/TenSon19920106)

## 致谢

Datawhale 与 Hello-Agents 教程第十六章毕业设计指引。
