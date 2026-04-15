"""
PBC-Analysis 成品演示（Streamlit）

运行（在项目根目录）:
  pip install -r requirements.txt
  streamlit run app_streamlit.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _bootstrap_env() -> None:
    try:
        from dotenv import dotenv_values
    except ImportError:
        return
    p = ROOT / ".env"
    if p.is_file():
        for k, v in dotenv_values(p).items():
            if v is not None and str(v).strip() != "":
                os.environ[k] = str(v).strip()


_bootstrap_env()

import streamlit as st  # noqa: E402
from hello_agents import HelloAgentsLLM  # noqa: E402

from src.api_client import submit_planning  # noqa: E402
from src.extract import extract_pbc_payload  # noqa: E402
from src.normalize import normalize_khjd, normalize_khnf  # noqa: E402
from src.schema import validate_pbc_payload  # noqa: E402


def _load_sample_text() -> str:
    p = ROOT / "data" / "sample_quarterly_work.txt"
    if p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    return ""

def _hero_badge(text: str) -> str:
    return f'<span style="display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(120,255,255,0.20);background:rgba(10,12,18,0.40);margin-right:8px;font-size:12px;color:rgba(235,245,255,0.85);">{text}</span>'


def _summary_cards(payload: dict) -> None:
    """把 JSON 做成用户可读摘要（不展示技术字段名）。"""
    dllzb = payload.get("dllzb") if isinstance(payload.get("dllzb"), list) else []
    dxlzb = payload.get("dxlzb") if isinstance(payload.get("dxlzb"), list) else []
    grcz = payload.get("grcz") if isinstance(payload.get("grcz"), list) else []

    total_items = len(dllzb) + len(dxlzb)
    total_weight = 0.0
    for it in list(dllzb) + list(dxlzb):
        try:
            total_weight += float(it.get("qz"))
        except Exception:
            pass

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="pbc-card"><div style="font-size:12px;color:rgba(235,245,255,0.70)">指标条目</div>'
                    f'<div style="font-size:28px;font-weight:800;line-height:1.2">{total_items}</div>'
                    '<div class="pbc-sub">定量 + 定性</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="pbc-card"><div style="font-size:12px;color:rgba(235,245,255,0.70)">权重合计</div>'
                    f'<div style="font-size:28px;font-weight:800;line-height:1.2">{total_weight:.2f}</div>'
                    '<div class="pbc-sub">目标应为 100.00</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="pbc-card"><div style="font-size:12px;color:rgba(235,245,255,0.70)">个人成长</div>'
                    f'<div style="font-size:28px;font-weight:800;line-height:1.2">{len(grcz)}</div>'
                    '<div class="pbc-sub">不计入权重</div></div>', unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="pbc-card"><div style="font-weight:750;margin-bottom:6px">定量类指标</div>', unsafe_allow_html=True)
        if dllzb:
            for it in dllzb[:6]:
                st.markdown(
                    f"- **{it.get('KPI') or '（未填写KPI）'}**：目标 {it.get('mb') or '（未填写目标）'}（权重 {it.get('qz','')}）",
                )
            if len(dllzb) > 6:
                st.caption(f"已隐藏其余 {len(dllzb)-6} 条")
        else:
            st.caption("暂无定量指标")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="pbc-card"><div style="font-weight:750;margin-bottom:6px">定性类指标</div>', unsafe_allow_html=True)
        if dxlzb:
            for it in dxlzb[:6]:
                st.markdown(
                    f"- **{it.get('khmd','')}**：{it.get('zdgz','')}（权重 {it.get('qz','')}）",
                )
            if len(dxlzb) > 6:
                st.caption(f"已隐藏其余 {len(dxlzb)-6} 条")
        else:
            st.caption("暂无定性指标")
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="PBC 结构化演示", layout="wide")
    st.markdown(
        """
<style>
/* --- Tech theme (dark / futuristic) --- */
:root{
  --pbc-bg: #070A12;                 /* deep space */
  --pbc-panel: rgba(10,12,18,0.55);  /* glass */
  --pbc-panel-strong: rgba(10,12,18,0.72);
  --pbc-line: rgba(120,255,255,0.18);/* tech cyan line */
  --pbc-cyan: #35E5FF;               /* tech cyan */
  --pbc-blue: #2B7CFF;               /* electric blue */
  --pbc-purple: #B14CFF;             /* neon purple */
  --pbc-text: rgba(235,245,255,0.92);
  --pbc-muted: rgba(235,245,255,0.72);
}
section.main > div { padding-top: 1.2rem; }
.stApp {
  background:
    /* subtle grid */
    linear-gradient(rgba(53,229,255,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(177,76,255,0.05) 1px, transparent 1px),
    /* glows */
    radial-gradient(1100px 700px at 10% 0%, rgba(53,229,255,0.12), rgba(0,0,0,0)),
    radial-gradient(900px 600px at 90% 12%, rgba(177,76,255,0.14), rgba(0,0,0,0)),
    radial-gradient(800px 600px at 50% 110%, rgba(43,124,255,0.10), rgba(0,0,0,0)),
    var(--pbc-bg);
  background-size: 64px 64px, 64px 64px, auto, auto, auto, auto;
}

/* panels */
div[data-testid="stSidebar"] > div {
  background: var(--pbc-panel-strong);
  border-right: 1px solid rgba(120,255,255,0.10);
  backdrop-filter: blur(12px);
}
.block-container { color: var(--pbc-text); }

.pbc-card {
  background: var(--pbc-panel);
  border: 1px solid var(--pbc-line);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow:
    0 0 0 1px rgba(120,255,255,0.06) inset,
    0 16px 60px rgba(0,0,0,0.45);
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
}
.pbc-card:hover{
  transform: translateY(-2px);
  border-color: rgba(53,229,255,0.34);
  box-shadow:
    0 0 0 1px rgba(53,229,255,0.10) inset,
    0 18px 70px rgba(0,0,0,0.55),
    0 0 28px rgba(53,229,255,0.12);
}

.pbc-muted { color: var(--pbc-muted); }
.pbc-title { font-size: 28px; font-weight: 750; letter-spacing: 0.3px; }
.pbc-sub { font-size: 13px; color: rgba(235, 245, 255, 0.70); }

/* inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[role="combobox"]{
  background: rgba(10,12,18,0.55) !important;
  border: 1px solid rgba(120,255,255,0.14) !important;
  transition: box-shadow 160ms ease, border-color 160ms ease, transform 160ms ease;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stSelectbox"] div[role="combobox"]:focus-within{
  border-color: rgba(53,229,255,0.35) !important;
  box-shadow: 0 0 0 1px rgba(53,229,255,0.10) inset, 0 0 18px rgba(53,229,255,0.16);
}

/* buttons (hover glow / lift) */
div.stButton > button{
  border: 1px solid rgba(120,255,255,0.18) !important;
  background: linear-gradient(135deg, rgba(43,124,255,0.24), rgba(177,76,255,0.18)) !important;
  color: var(--pbc-text) !important;
  transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, filter 160ms ease;
}
div.stButton > button:hover{
  transform: translateY(-1px);
  border-color: rgba(53,229,255,0.35) !important;
  box-shadow: 0 10px 26px rgba(0,0,0,0.45), 0 0 20px rgba(53,229,255,0.12);
  filter: brightness(1.08);
}
div.stButton > button:active{ transform: translateY(0px) scale(0.99); }

/* code blocks */
code { background: rgba(0,0,0,0.35) !important; }
</style>
        """,
        unsafe_allow_html=True,
    )

    # --- HERO ---
    st.markdown(
        f"""
<div class="pbc-card">
  <div class="pbc-title">PBC 结构化助手</div>
  <div class="pbc-sub">把工作总结转成可对接系统的结构化 JSON，并支持一键提交绩效制订。</div>
  <div style="margin-top:10px">
    {_hero_badge("Step 1  填写参数")}
    {_hero_badge("Step 2  粘贴/上传总结")}
    {_hero_badge("Step 3  生成 / 下载 / 提交")}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    with st.sidebar:
        st.header("参数")
        gh = st.text_input("工号（必填）", value="", placeholder="例如 80025013")
        year = st.selectbox(
            "考核年份（必填）",
            options=list(range(2023, 2031)),
            index=3,  # 2026
        )
        quarter_label = st.selectbox(
            "考核季度（必填）",
            options=["第一季度", "第二季度", "第三季度", "第四季度", "年度"],
            index=0,
        )
        st.divider()
        # 对普通用户隐藏环境细节：折叠展示即可
        with st.expander("高级设置（可选）", expanded=False):
            st.caption("该页会读取项目根目录 `.env` 的 LLM 配置与接口地址。")
            llm_ok = bool(os.getenv("LLM_API_KEY") and os.getenv("LLM_BASE_URL") and os.getenv("LLM_MODEL_ID"))
            st.write(f"- LLM 配置：{'已就绪' if llm_ok else '未就绪'}")
            planning_url = os.getenv("PBC_PLANNING_URL", "").strip()
            st.write(f"- 绩效制订接口：{'已配置' if planning_url else '未配置'}")
            if not llm_ok:
                st.info("如需生成 JSON，请在 `.env` 中配置 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL_ID。")

    if "work_body" not in st.session_state:
        st.session_state.work_body = ""

    # --- TABS (programmable): use radio so we can auto-switch after generation ---
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "输入"

    tab_choice = st.radio(
        "导航",
        options=["输入", "结果", "提交"],
        horizontal=True,
        label_visibility="collapsed",
        index=["输入", "结果", "提交"].index(st.session_state.active_tab),
    )
    st.session_state.active_tab = tab_choice

    if tab_choice == "输入":
        st.markdown('<div class="pbc-card"><div style="font-weight:750">输入工作总结</div><div class="pbc-sub">支持粘贴或上传 .txt</div></div>', unsafe_allow_html=True)
        st.write("")
        col_a, col_b = st.columns([2, 1])
        # 必须先处理会修改 session_state 的控件，再实例化绑定同一 key 的 text_area，
        # 否则 Streamlit 会报：widget 已创建后不能再改 session_state[key]
        with col_b:
            st.subheader("快捷操作")
            if st.button("载入示例文本"):
                st.session_state.work_body = _load_sample_text()
            up = st.file_uploader("或上传 .txt", type=["txt"])
            if up is not None:
                st.session_state.work_body = up.read().decode("utf-8", errors="replace")
        with col_a:
            work_text = st.text_area(
                "工作总结（粘贴文本）",
                height=320,
                placeholder="粘贴本季度/年度工作叙述…",
                key="work_body",
            )

            st.write("")
            gen = st.button("生成结构化 JSON", type="primary", use_container_width=True)
    else:
        # 防止未进入「输入」页时引用未初始化的局部变量
        gen = False
        work_text = ""

    if gen:
        if not str(gh).strip():
            st.error("请填写工号")
            return
        if not str(work_text).strip():
            st.error("请填写工作总结文本")
            return

        try:
            # 下拉框给的是“人类可读”，这里统一走 normalize 以保持一致
            khnf = normalize_khnf(int(year))
            khjd = normalize_khjd(quarter_label)
        except ValueError as e:
            st.error(str(e))
            return

        if "llm" not in st.session_state:
            st.session_state.llm = HelloAgentsLLM(
                model=os.getenv("LLM_MODEL_ID"),
                api_key=os.getenv("LLM_API_KEY"),
                base_url=os.getenv("LLM_BASE_URL"),
                timeout=int(os.getenv("LLM_TIMEOUT", "120")),
            )
        llm = st.session_state.llm

        with st.spinner("正在调用大模型生成结构化 JSON…"):
            try:
                payload = extract_pbc_payload(
                    llm,
                    work_text.strip(),
                    gh=str(gh).strip(),
                    khnf=khnf,
                    khjd=khjd,
                )
            except Exception as e:
                st.exception(e)
                return

        ok, errs = validate_pbc_payload(payload)

        st.session_state.last_payload = payload
        st.session_state.last_payload_schema_ok = ok
        # Auto switch to Result tab after generation
        st.session_state.active_tab = "结果"
        st.rerun()

        out = json.dumps(payload, ensure_ascii=False, indent=2)
        runtime = ROOT / "outputs" / "runtime"
        runtime.mkdir(parents=True, exist_ok=True)
        out_path = runtime / "pbc_payload.json"
        out_path.write_text(out, encoding="utf-8")

    if tab_choice == "结果":
        payload = st.session_state.get("last_payload")
        ok = bool(st.session_state.get("last_payload_schema_ok"))
        st.markdown('<div class="pbc-card"><div style="font-weight:750">生成结果</div><div class="pbc-sub">摘要 + 可下载 JSON</div></div>', unsafe_allow_html=True)
        st.write("")
        if payload is None:
            st.info("尚未生成结果，请先到「输入」页点击生成。")
        else:
            if ok:
                st.success("已生成结构化 JSON")
            else:
                st.error("生成结果未通过校验（建议补充信息后重试）")
            _summary_cards(payload)
            out = json.dumps(payload, ensure_ascii=False, indent=2)
            st.download_button(label="下载 JSON", data=out.encode("utf-8"), file_name="pbc_payload.json", mime="application/json")
            with st.expander("查看 JSON（技术人员/联调用）", expanded=False):
                st.json(payload)

    if tab_choice == "提交":
        st.markdown('<div class="pbc-card"><div style="font-weight:750">提交到绩效制订</div><div class="pbc-sub">可选：配置接口后再启用</div></div>', unsafe_allow_html=True)
        st.write("")
        plan_url = os.getenv("PBC_PLANNING_URL", "").strip()
        payload_cached = st.session_state.get("last_payload")
        schema_ok = bool(st.session_state.get("last_payload_schema_ok"))

        if payload_cached is None:
            st.info("请先在「输入」页生成结构化 JSON。")
        else:
            gh_view = str(payload_cached.get("gh") or "")
            khnf_view = payload_cached.get("khnf")
            khjd_view = payload_cached.get("khjd")
            st.markdown(
                f"""
<div class="pbc-card">
  <div style="font-size:12px;color:rgba(235,245,255,0.70)">待提交摘要</div>
  <div style="font-size:18px;font-weight:800">工号 {gh_view}</div>
  <div class="pbc-sub">khnf={khnf_view}, khjd={khjd_view}</div>
</div>
                """.strip(),
                unsafe_allow_html=True,
            )

        require_ok = st.checkbox("提交前必须通过校验", value=True)
        can_submit = bool(plan_url) and payload_cached is not None and (schema_ok or not require_ok)

        if plan_url:
            st.caption("接口地址已配置，可提交。")
        else:
            st.warning("未配置 `PBC_PLANNING_URL`，无法提交。请在项目根 `.env` 填写后重启 Streamlit。")

        if st.button(
            "更新绩效制订",
            type="secondary",
            use_container_width=True,
            disabled=not can_submit,
        ):
            if require_ok and not schema_ok:
                st.error("校验未通过，已阻止提交。")
            else:
                with st.spinner("正在调用绩效制订接口…"):
                    try:
                        res = submit_planning(payload_cached)
                    except Exception as e:
                        st.exception(e)
                    else:
                        if res is None:
                            st.error("未配置 PBC_PLANNING_URL，无法提交。")
                        else:
                            code, body = res
                            if 200 <= int(code) < 300:
                                st.success(f"提交成功：HTTP {code}")
                            else:
                                st.error(f"提交失败：HTTP {code}")
                            with st.expander("查看接口响应", expanded=False):
                                st.code(body or "(空响应体)", language="text")


if __name__ == "__main__":
    main()
