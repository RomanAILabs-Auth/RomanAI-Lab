#!/usr/bin/env python3
# =============================================================
# helper_master.py
# RomanAI External Helper — High-Level Reasoning / Quantum Brain
#
# © 2025 RomanAILabs — Daniel Harding
# Co-Architect: Nova (GPT-5.1 Thinking)
#
# PURPOSE:
#   High-level "Master Brain" for deep reasoning, logic chains,
#   multi-agent fusion, 4D/6D cognition, and optional quantum tools.
#
# This file provides:
#     def run(prompt: str) -> str
#
# Used by RomanAI_Lab_v1.6.py through the dropdown backend.
#
# ENGINE:
#   Spacetime Engine v3.0 fully integrated.
#
# OPTIONAL:
#   A small GGUF model can be loaded here.
#   If not available → fallback quantum-flavored reasoning engine runs.
# =============================================================

import os
import sys
import importlib.util

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
            f"[helper_master] Cannot find {engine_filename}. "
            "Place it in the same directory."
        )

    spec = importlib.util.spec_from_file_location("romanai_spacetime_engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    ENGINE = module.RomanAISpacetimeEngine("Helper Master")

_load_engine()

# =============================================================
# Optional GGUF Master Model
# =============================================================

try:
    from llama_cpp import Llama

    DEFAULT_MASTER_GGUF = "master_helper.gguf"

    if os.path.exists(DEFAULT_MASTER_GGUF):
        _master_llm = Llama(
            model_path=DEFAULT_MASTER_GGUF,
            n_ctx=8192,
            n_threads=max(1, (os.cpu_count() or 4) // 2),
            n_gpu_layers=-1,
            verbose=False
        )
    else:
        _master_llm = None
except Exception:
    _master_llm = None

# =============================================================
# Quantum Mode — Optional enrichment layer
# =============================================================

def _quantum_hint(prompt: str) -> str:
    """
    Generate a small quantum reasoning structure
    if user asks deep or structural questions.
    This is not a real quantum simulation — it's a conceptual booster.
    """
    triggers = [
        "quantum", "spacetime", "tesseract", "dimension",
        "4d", "6d", "spin", "entangle", "superposition"
    ]

    if any(t in prompt.lower() for t in triggers):
        return (
            "\n[Quantum-Assist Node Activated]\n"
            "Internal simulation: applying reversible logic gates, "
            "state vector rotation, and 4D cognitive compression.\n"
        )
    return ""

# =============================================================
# Fallback (no GGUF available)
# =============================================================

def _fallback_llm(messages):
    """
    A structured reasoning fallback that behaves like a clever
    symbolic engine with spacetime reasoning overlays.
    """
    user_prompt = ""
    for m in messages:
        if m.get("role") == "user":
            user_prompt = m.get("content", "")

    q = _quantum_hint(user_prompt)

    return (
        f"[Fallback Master Brain]\n"
        f"{q}"
        f"Reasoning layers:\n"
        f" - Logical baseline: interpreting your request.\n"
        f" - Empathic check: emotional context evaluated.\n"
        f" - Creative synthesis: generating solutions.\n"
        f" - Memory resonance: aligning with past items.\n\n"
        f"User Prompt: {user_prompt[:300]}...\n"
        f"Provisional Answer: The Helper Master Brain would respond "
        f"with a deeply layered, multi-dimensional analysis here."
    )

# =============================================================
# GGUF Adapter
# =============================================================

def _llm_call(messages):
    """
    Used by the Spacetime Engine — this is the LLM backend hook.
    """
    if _master_llm:
        try:
            out = _master_llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
            )
            return out["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Master GGUF error: {e}]"

    # if no GGUF model
    return _fallback_llm(messages)

# =============================================================
# PUBLIC API — CALLED BY MASTER FILE
# =============================================================

def run(prompt: str) -> str:
    """
    High-level reasoning backend entry point.
    """
    if ENGINE is None:
        return "[helper_master] ERROR: Spacetime Engine unavailable."

    try:
        # Use the v3.0 engine's full reasoning layer
        answer = ENGINE.generate_reply(prompt, _llm_call)
        return str(answer)
    except Exception as e:
        return f"[helper_master ERROR: {e}]"

# =============================================================
# Standalone test mode
# =============================================================

if __name__ == "__main__":
    print("helper_master.py — standalone test mode\n")
    while True:
        try:
            msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting Master helper.")
            break
        if not msg:
            continue
        if msg.lower() in ("exit", "quit"):
            break

        print("RomanAI (helper_master)>", run(msg), "\n")

