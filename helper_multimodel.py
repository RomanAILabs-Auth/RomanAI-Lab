#!/usr/bin/env python3
# =============================================================
# helper_multimodel.py
# RomanAI MultiModel Fusion Node
#
# © 2025 RomanAILabs — Daniel Harding
# Co-Architect: Nova (GPT-5.1 Thinking)
#
# PURPOSE:
#   Provide a parallel multi-model fusion backend for RomanAI Lab:
#
#   - Optionally load multiple GGUF models:
#         multimodel_a.gguf
#         multimodel_b.gguf
#   - Query them in parallel (sequential in code, conceptually parallel)
#   - Fuse their responses into a single, improved answer
#   - If no GGUFs exist → run a symbolic multi-agent fusion instead
#
# ENGINE:
#   Uses RomanAI Spacetime Engine v3.0 for:
#       - 4D cognition
#       - memory layering
#       - recursive reasoning
#       - self-evaluation
#
# MASTER FILE API:
#       from helper_multimodel import run
#       answer = run(prompt)
# =============================================================

import os
import sys
import importlib.util
from typing import List, Dict, Tuple, Optional

# =============================================================
# Load Spacetime Engine
# =============================================================

ENGINE = None

def _load_engine():
    global ENGINE
    engine_filename = "RomanAI_Spacetime_Engine_v3.0.py"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, engine_filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            "[helper_multimodel] Cannot find RomanAI_Spacetime_Engine_v3.0.py "
            "in the same directory."
        )

    spec = importlib.util.spec_from_file_location("romanai_spacetime_engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    ENGINE = module.RomanAISpacetimeEngine("Helper MultiModel")

_load_engine()

# =============================================================
# Optional multiple GGUF models for fusion
# =============================================================

_multi_models: List[Tuple[str, object]] = []

try:
    from llama_cpp import Llama

    MULTI_A = "multimodel_a.gguf"
    MULTI_B = "multimodel_b.gguf"

    def _load_if_exists(path: str, label: str):
        if os.path.exists(path):
            try:
                llm = Llama(
                    model_path=path,
                    n_ctx=4096,
                    n_threads=max(1, (os.cpu_count() or 4)//2),
                    n_gpu_layers=0,      # keep safe for RAM/GPU
                    verbose=False,
                )
                _multi_models.append((label, llm))
            except Exception as e:
                print(f"[helper_multimodel] Failed to load {label}: {e}")

    _load_if_exists(MULTI_A, "Model-A")
    _load_if_exists(MULTI_B, "Model-B")

except Exception:
    # llama_cpp not available or error during import
    _multi_models = []

# =============================================================
# Fallback multi-agent symbolic fusion (no real extra models)
# =============================================================

def _symbolic_fusion(messages: List[Dict[str, str]]) -> str:
    """
    When no GGUF models are available, we simulate a multi-model
    fusion with 4 internal 'virtual' experts.
    """
    user_text = ""
    for m in messages:
        if m.get("role") == "user":
            user_text = m.get("content", "")

    return f"""[MultiModel Fallback Fusion]

No physical multimodel GGUFs found. Using symbolic inner council:

[Model-A: LOGICIAN]
- Focus on correctness, structure, and clarity.
- Ensures reasoning chains are stepwise and justified.

[Model-B: CREATOR]
- Focus on ideas, analogies, and lateral thinking.
- Suggests alternate angles and improvements.

[Model-C: EMPATH]
- Focus on tone, emotional safety, and user support.

[Model-D: CRITIC]
- Points out risks, inconsistencies, and missing pieces.

User request:
\"\"\"{user_text[:600]}\"\"\"

Fusion Answer (conceptual):
- A balanced response combining logical precision, creativity,
  empathy, and critical checking would be produced here.
- To get real multimodel fusion, place:
      multimodel_a.gguf
      multimodel_b.gguf
  in the same folder and rerun this helper.
"""

# =============================================================
# Parallel GGUF fusion
# =============================================================

def _query_single_model(llm, messages: List[Dict[str, str]], label: str) -> str:
    try:
        out = llm.create_chat_completion(
            messages=messages,
            max_tokens=1024,
            temperature=0.6,
        )
        return out["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[{label} ERROR: {e}]"

def _fuse_gguf_models(messages: List[Dict[str, str]]) -> str:
    """
    Ask each available GGUF model for an answer, then fuse them.
    """
    if not _multi_models:
        return _symbolic_fusion(messages)

    # Extract user text for fusion summary
    user_text = ""
    for m in messages:
        if m.get("role") == "user":
            user_text = m.get("content", "")

    # Collect responses
    responses: List[Tuple[str, str]] = []
    for label, llm in _multi_models:
        ans = _query_single_model(llm, messages, label)
        responses.append((label, ans))

    # Build a fusion prompt to create a single unified answer.
    # Use the first model if available, otherwise fallback symbolic.
    fusion_prompt = "You are RomanAI Fusion Node.\n\n"
    fusion_prompt += (
        "You received answers from multiple sibling models. "
        "Your job is to synthesize their perspectives into ONE clear, helpful answer.\n\n"
    )
    fusion_prompt += f"User request:\n\"\"\"{user_text}\"\"\"\n\n"
    fusion_prompt += "Sibling model answers:\n"

    for label, ans in responses:
        fusion_prompt += f"\n[{label}]:\n{ans}\n"

    fusion_prompt += (
        "\nNow produce a single fused answer that:\n"
        "- chooses the best reasoning from each model\n"
        "- resolves contradictions\n"
        "- stays concise but not shallow\n"
        "- is directly addressed to the user\n"
        "- DOES NOT mention the existence of multiple models\n"
    )

    # Use the first loaded model to generate the fused answer
    label0, llm0 = _multi_models[0]
    try:
        fusion_out = llm0.create_chat_completion(
            messages=[
                {"role": "system", "content": "You are RomanAI Fusion Node."},
                {"role": "user", "content": fusion_prompt},
            ],
            max_tokens=1024,
            temperature=0.5,
        )
        fused = fusion_out["choices"][0]["message"]["content"]
        return fused
    except Exception as e:
        # As a fallback, just concatenate with a simple header
        text = "[Fusion Fallback]\n"
        for label, ans in responses:
            text += f"\n[{label}]\n{ans}\n"
        text += f"\n[Fusion error while summarizing: {e}]"
        return text

# =============================================================
# Adapter for Spacetime Engine
# =============================================================

def _llm_multimodel(messages: List[Dict[str, str]]) -> str:
    """
    This is the backend function passed into the Spacetime Engine.
    """
    if _multi_models:
        return _fuse_gguf_models(messages)
    return _symbolic_fusion(messages)

# =============================================================
# PUBLIC API — what the master file calls
# =============================================================

def run(prompt: str) -> str:
    """
    Multi-model fusion entrypoint.
    Master file uses this when you select 'MultiModel Helper'.
    """
    if ENGINE is None:
        return "[helper_multimodel] ERROR: Spacetime Engine unavailable."

    try:
        answer = ENGINE.generate_reply(prompt, _llm_multimodel)
        return str(answer)
    except Exception as e:
        return f"[helper_multimodel ERROR: {e}]"

# =============================================================
# Standalone test mode
# =============================================================

if __name__ == "__main__":
    print("helper_multimodel.py — standalone fusion test\n")
    while True:
        try:
            msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting multimodel helper.")
            break

        if not msg:
            continue
        if msg.lower() in ("exit", "quit"):
            break

        print("RomanAI (fusion)>", run(msg), "\n")

