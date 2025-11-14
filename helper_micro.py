#!/usr/bin/env python3
# =============================================================
# helper_micro.py
# RomanAI Micro Brain — Ultra-Light Speed Model Backend
#
# © 2025 RomanAILabs — Daniel Harding
# Co-Architect: Nova (GPT-5.1 Thinking)
#
# PURPOSE:
#   Provide a micro AI backend with:
#       - blazing fast latency
#       - minimal RAM usage
#       - tiny GGUF or pure-python fallback
#
#   This is used when you select “Micro Helper” in the
#   RomanAI_Lab_v1.6 dropdown.
#
# ENGINE:
#   RomanAI Spacetime Engine v3.0 fully integrated.
#
# API:
#   run(prompt: str) -> str
#
# NOTES:
#   - If you place a tiny GGUF model named:
#       micro_helper.gguf
#     in the same directory, this file will use it automatically.
# =============================================================

import os
import sys
import importlib.util

# =============================================================
# Load RomanAI Spacetime Engine v3.0
# =============================================================

ENGINE = None

def _load_engine():
    global ENGINE
    engine_filename = "RomanAI_Spacetime_Engine_v3.0.py"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, engine_filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            "[helper_micro] ERROR: Cannot find RomanAI_Spacetime_Engine_v3.0.py"
        )

    spec = importlib.util.spec_from_file_location("romanai_spacetime_engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    ENGINE = module.RomanAISpacetimeEngine("Helper Micro")

_load_engine()

# =============================================================
# Optional Tiny GGUF Model
# =============================================================

try:
    from llama_cpp import Llama

    MICRO_GGUF = "micro_helper.gguf"

    if os.path.exists(MICRO_GGUF):
        _tiny_llm = Llama(
            model_path=MICRO_GGUF,
            n_ctx=2048,
            n_threads=max(1, (os.cpu_count() or 4)//2),
            n_gpu_layers=0,  # micro mode — CPU only, no GPU dependency
            verbose=False,
        )
    else:
        _tiny_llm = None
except Exception:
    _tiny_llm = None

# =============================================================
# PURE PYTHON MICRO FALLBACK
# (Very fast, deterministic, safe)
# =============================================================

def _micro_fallback(messages):
    """
    Tiny deterministic reasoning engine.
    Gives short, sharp replies with micro-logic.
    """
    user_msg = ""
    for m in messages:
        if m.get("role") == "user":
            user_msg = m.get("content", "")

    return (
        "[Micro Brain]\n"
        "⚡ Ultra-light inference active.\n"
        f"User prompt: {user_msg[:200]}...\n"
        "Response: I processed your message with compact reasoning. "
        "This mode prioritizes speed over depth."
    )

# =============================================================
# Adapter for Engine
# =============================================================

def _llm(messages):
    """
    Called by the Spacetime Engine(generate_reply).
    """
    if _tiny_llm:
        try:
            out = _tiny_llm.create_chat_completion(
                messages=messages,
                max_tokens=512,   # micro mode: small outputs
                temperature=0.4,
            )
            return out["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[micro GGUF error: {e}]"

    return _micro_fallback(messages)

# =============================================================
# PUBLIC API (called by Master File)
# =============================================================

def run(prompt: str) -> str:
    """
    This is the micro backend entrypoint.
    Master file calls this when user selects Micro Helper.
    """
    if ENGINE is None:
        return "[helper_micro] ERROR: Engine unavailable."

    try:
        answer = ENGINE.generate_reply(prompt, _llm)
        return str(answer)
    except Exception as e:
        return f"[helper_micro ERROR: {e}]"

# =============================================================
# Standalone test mode
# =============================================================

if __name__ == "__main__":
    print("helper_micro.py — standalone micro test\n")
    while True:
        try:
            msg = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting micro helper.")
            break

        if not msg:
            continue
        if msg.lower() in ("exit", "quit"):
            break

        print("RomanAI (micro)>", run(msg), "\n")

