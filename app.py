"""
Streamlit Web Application for AI-Powered Conversational Workflow Builder.
Polished with UI/UX Pro Max Design System standards:
- Sleek dark theme with slate palette (#0F172A, #1E293B, #334155)
- Vibrant indigo-purple gradient branding (#6366F1 to #8B5CF6)
- Semantic status pills & dynamic parameter badges
- Interactive Mermaid DAG workflow visualizer & JSON accordion
- One-click preset scenario triggers for testing
"""

import sys
import os
import json
import uuid
import streamlit as st

# Ensure workspace root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state_manager import state_manager


# Page configuration
st.set_page_config(
    page_title="AI Conversational Workflow Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS implementing UI/UX Pro Max Design System
st.markdown("""
<style>
    /* Global Container Styles */
    .stApp {
        background-color: #0B0F17;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Brand Header Gradient */
    .brand-header {
        font-family: 'Space Grotesk', system-ui, sans-serif;
        font-size: 2.25rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        background: linear-gradient(135deg, #7C3AED 0%, #6366F1 50%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    
    .brand-subhead {
        color: #94A3B8;
        font-size: 1rem;
        line-height: 1.5;
        margin-bottom: 1.5rem;
    }

    /* Card Containers */
    .ux-card {
        background: rgba(22, 31, 48, 0.75);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.3);
    }

    /* Progress Bar */
    .progress-track-st {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 9999px;
        height: 10px;
        border: 1px solid rgba(148, 163, 184, 0.14);
        overflow: hidden;
        margin-bottom: 1rem;
    }
    
    .progress-fill-st {
        height: 100%;
        background: linear-gradient(90deg, #7C3AED 0%, #06B6D4 100%);
        transition: width 300ms ease;
    }

    /* Status Pills */
    .pill-ready {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .pill-clarify {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 6px 14px;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.875rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    /* Badges */
    .badge-req {
        background-color: rgba(51, 65, 85, 0.5);
        color: #E2E8F0;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8125rem;
        font-weight: 500;
        display: inline-block;
        margin: 3px;
        border: 1px solid rgba(148, 163, 184, 0.2);
    }

    .badge-miss {
        background-color: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8125rem;
        font-weight: 500;
        display: inline-block;
        margin: 3px;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-col {
        background-color: rgba(16, 185, 129, 0.15);
        color: #6EE7B7;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8125rem;
        font-weight: 500;
        display: inline-block;
        margin: 3px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    /* Parameter Row */
    .param-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        background-color: rgba(15, 23, 42, 0.6);
        border-radius: 8px;
        margin-bottom: 6px;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    .param-key {
        color: #94A3B8;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .param-val {
        color: #06B6D4;
        font-size: 0.875rem;
        font-weight: 600;
        font-family: 'Fira Code', monospace;
        background: rgba(6, 182, 212, 0.1);
        padding: 2px 8px;
        border-radius: 4px;
    }

    /* Clarification Banner */
    .clarification-banner {
        background: rgba(124, 58, 237, 0.12);
        border: 1px solid rgba(124, 58, 237, 0.4);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
</style>
""", unsafe_allow_html=True)


# Session Initialization
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = f"session_{uuid.uuid4().hex[:8]}"

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []


def reset_session():
    state_manager.reset_state(st.session_state.conversation_id)
    st.session_state.conversation_id = f"session_{uuid.uuid4().hex[:8]}"
    st.session_state.chat_messages = []
    st.rerun()


# Sidebar Controls & Preset Scenarios
with st.sidebar:
    st.markdown("### ⚙️ Session Controls")
    if st.button("🔄 Start New Workflow", use_container_width=True, type="primary"):
        reset_session()

    st.divider()
    st.markdown("### 🧪 Quick Test Scenarios")
    
    scenarios = [
        {
            "name": "Scenario 1: Invoice Alert",
            "desc": "Gmail invoice trigger -> Slack #finance notification",
            "prompt": "I want to receive a Slack notification whenever I get a new invoice."
        },
        {
            "name": "Scenario 2: GitHub Bug Alert",
            "desc": "GitHub issue with bug label -> Slack channel alert",
            "prompt": "When a GitHub issue labeled bug is created, notify Slack."
        },
        {
            "name": "Scenario 3: Web Form Ingestion",
            "desc": "Website contact form submission -> Google Sheets row",
            "prompt": "When someone submits my website contact form, save their details to Google Sheets."
        },
        {
            "name": "Scenario 4: Fully Specified",
            "desc": "All parameters provided in initial request (no clarification needed)",
            "prompt": "When a new email with subject 'Urgent' arrives in my Gmail inbox account user@example.com, send a Slack message to #alerts channel in Acme workspace."
        },
        {
            "name": "Scenario 5: Ambiguous Request",
            "desc": "Vague request with multiple interpretations requiring clarification",
            "prompt": "Send important emails to my team."
        }
    ]

    for idx, sc in enumerate(scenarios, 1):
        if st.button(f"{sc['name']}", help=sc['desc'], use_container_width=True):
            reset_session()
            st.session_state.preset_prompt = sc['prompt']

    st.divider()
    st.caption(f"Active Session: `{st.session_state.conversation_id}`")


# Header Section
st.markdown('<div class="brand-header">⚡ AI Conversational Workflow Builder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="brand-subhead">Describe your automation goal in plain English. The AI agent will dynamically identify requirements and ask one clarification at a time until complete.</div>',
    unsafe_allow_html=True
)

# Responsive Columns Layout
col_chat, col_inspector = st.columns([7, 5])

# Retrieve Current State
current_state = state_manager.get_state(st.session_state.conversation_id) or {
    "workflow_type": None,
    "required_information": [],
    "collected_information": {},
    "missing_information": [],
    "ambiguities": [],
    "workflow_ready": False,
    "generated_workflow": None
}

# Left Column: Chat Interface
with col_chat:
    st.markdown("#### 💬 Interactive Chat Assistant")
    
    chat_box = st.container(height=480)
    with chat_box:
        if not st.session_state.chat_messages:
            st.info("👋 **Hello!** Tell me what workflow or automation you want to build.")
        
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Handle Preset Trigger or User Input
    preset_input = st.session_state.pop("preset_prompt", None)
    user_input = st.chat_input("Type your automation request or reply...")

    active_prompt = preset_input or user_input

    if active_prompt:
        st.session_state.chat_messages.append({"role": "user", "content": active_prompt})
        with chat_box:
            with st.chat_message("user"):
                st.write(active_prompt)

        with chat_box:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing requirements & updating state..."):
                    updated_state = state_manager.process_message(
                        st.session_state.conversation_id,
                        active_prompt
                    )
                    
                    if updated_state.get("workflow_ready"):
                        wf = updated_state.get("generated_workflow", {})
                        res_msg = f"🎉 **Workflow Completed!** Generated: **{wf.get('name', 'Custom Workflow')}**."
                    else:
                        res_msg = updated_state.get("current_question") or "Could you please specify further?"

                    st.write(res_msg)
                    st.session_state.chat_messages.append({"role": "assistant", "content": res_msg})

        st.rerun()


# Right Column: Dynamic State Inspector & Visualizer
with col_inspector:
    st.markdown("#### 🔍 Live Dynamic State Inspector")
    
    ready = current_state.get("workflow_ready", False)
    wf_type = current_state.get("workflow_type") or "Not yet determined"

    # Compute Readiness Percentage
    col_info = current_state.get("collected_information", {})
    miss_info = current_state.get("missing_information", [])
    ambig_info = current_state.get("ambiguities", [])
    total_items = len(col_info) + len(miss_info) + len(ambig_info)
    
    if ready:
        progress_pct = 100
    elif total_items > 0:
        progress_pct = min(90, int((len(col_info) / total_items) * 100))
    elif len(col_info) > 0:
        progress_pct = 50
    else:
        progress_pct = 0

    # Status & Progress Gauge Card
    st.markdown('<div class="ux-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([6, 6])
    with c1:
        st.markdown(f"**Workflow Type:** `{wf_type}`")
    with c2:
        st.markdown(f"**Readiness:** `{progress_pct}%`")
        if ready:
            st.markdown('<div class="pill-ready">● Complete & Ready</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="pill-clarify">● Clarifying Requirements</div>', unsafe_allow_html=True)
    
    st.markdown(f'''
    <div class="progress-track-st">
        <div class="progress-fill-st" style="width: {progress_pct}%;"></div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Required Information Section
    req_info = current_state.get("required_information", [])
    st.markdown("**📌 Dynamically Identified Requirements**")
    if req_info:
        badge_html = " ".join([f'<span class="badge-req">{r}</span>' for r in req_info])
        st.markdown(badge_html, unsafe_allow_html=True)
    else:
        st.caption("Awaiting initial user prompt...")

    st.markdown("---")

    # Collected Parameters Section
    st.markdown("**✅ Collected Parameters**")
    if col_info:
        for k, v in col_info.items():
            st.markdown(f"""
            <div class="param-row">
                <span class="param-key">{k}</span>
                <span class="param-val">{v}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No parameters collected yet.")

    st.markdown("---")

    # Missing Parameters Section
    st.markdown("**❓ Missing Parameters**")
    if miss_info:
        badge_miss_html = " ".join([f'<span class="badge-miss">{m}</span>' for m in miss_info])
        st.markdown(badge_miss_html, unsafe_allow_html=True)
    else:
        st.caption("No missing parameters.")

    # Ambiguities Section
    if ambig_info:
        st.markdown("---")
        st.markdown("**⚠️ Detected Ambiguities**")
        for amb in ambig_info:
            st.warning(f"• {amb}")

    # Generated Workflow Graph Visualizer
    gen_wf = current_state.get("generated_workflow")
    if gen_wf:
        st.markdown("---")
        st.markdown("### ⚡ Generated Workflow Diagram")
        
        nodes = gen_wf.get("nodes", [])
        edges = gen_wf.get("edges", [])

        mermaid_lines = ["graph LR"]
        for n in nodes:
            nid = n.get("id", "").replace("-", "_")
            nname = n.get("name", nid)
            ntype = n.get("type", "node").upper()
            mermaid_lines.append(f'    {nid}["<b>{nname}</b><br/><code>[{ntype}]</code>"]')

        for e in edges:
            src = e.get("source", "").replace("-", "_")
            tgt = e.get("target", "").replace("-", "_")
            mermaid_lines.append(f'    {src} --> {tgt}')

        mermaid_str = "\n".join(mermaid_lines)
        st.markdown(f"```mermaid\n{mermaid_str}\n```")

        wf_json_bytes = json.dumps(gen_wf, indent=2).encode("utf-8")
        st.download_button(
            label="💾 Download Workflow Specification (.json)",
            data=wf_json_bytes,
            file_name=f"workflow_{current_state.get('conversation_id', 'spec')}.json",
            mime="application/json",
            use_container_width=True
        )

        with st.expander("📄 Detailed Workflow JSON Spec"):
            st.json(gen_wf)

