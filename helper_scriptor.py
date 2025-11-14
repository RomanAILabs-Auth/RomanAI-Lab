#!/usr/bin/env python3
# =============================================================
# helper_scriptor.py
# RomanAI Helper Script — Coding Brain (External Backend)
#
# © 2025 RomanAILabs — Daniel Harding
# Co-Architect: Nova (GPT-5.1 Thinking)
#
# PURPOSE:
#   - Provide an external helper backend for the "Scriptor" mode.
#   - This is where you can plug ANY backend you want:
#         * Qwen .gguf
#         * LLaMA small models
#         * Python-only AI stubs
#         * Remote models (future)
#   - The Master File v1.6 calls:
#         result = helper_scriptor.run(prompt)
#
# ENGINE INTEGRATED:
#   Uses RomanAI Spacetime Engine v3.0 for memory/state logic.
#
# API:
#   def run(prompt: str) -> str:
#         return answer
# =============================================================

import os
import sys
import importlib.util

# Load Spacetime Engine v3.0
ENGINE = None

def _load_engine():
    """
    Dynamically import RomanAI_Spacetime_Engine_v3.0.py
    """
    global ENGINE

    engine_filename = "RomanAI_Spacetime_Engine_v3.0.py"
    base_path = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_path, engine_filename)

    if not os.path.exists(full_path):
        raise FileNotFoundError(
            f"[helper_scriptor] ERROR: Cannot find {engine_filename}.\n"
            "Place it in the same directory as helper_scriptor.py"
        )

    spec = importlib.util.spec_from_file_location("romanai_spacetime_engine", full_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    ENGINE = module.RomanAISpacetimeEngine("Helper Scriptor")

_load_engine()

# =====================================================================
# OPTIONAL BACKEND EXAMPLE
# Replace this with any small GGUF model or python-only model you want.
# =====================================================================

try:
    from llama_cpp import Llama
    # You can replace this path with any tiny GGUF file you want:
    DEFAULT_MODEL_PATH = "scriptor_helper.gguf"

    if os.path.exists(DEFAULT_MODEL_PATH):
        _tiny_llm = Llama(
            model_path=DEFAULT_MODEL_PATH,
            n_ctx=4096,
            n_threads=max(1, (os.cpu_count() or 4)//2),
            n_gpu_layers=0,
            verbose=False,
        )
    else:
        _tiny_llm = None
except Exception:
    _tiny_llm = None


# =====================================================================
# FALLBACK LLM — for when no GGUF model exists
# (A safe echo-style model to keep the system working.)
# =====================================================================

def _fallback_llm(messages):
    """
    Minimal safe LLM placeholder.
    Returns a deterministic explanation-style answer.
    """
    user_message = ""
    for m in messages:
        if m.get("role") == "user":
            user_message = m.get("content", "")
    return f"[Fallback Scriptor] Received: {user_message[:240]} ..."


# =====================================================================
# ROUTER FUNCTION (used by the engine)
# =====================================================================

def _llm_call(messages):
    """
    This adapter is used by the Spacetime Engine.
    It must accept List[Dict[str,str]] and return a string.
    """
    if _tiny_llm:
        try:
            out = _tiny_llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.4,
            )
            return out["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Scriptor GGUF error: {e}]"

    # fallback if GGUF isn't available
    return _fallback_llm(messages)


# =====================================================================
# PUBLIC API — THE FUNCTION YOUR MASTER FILE CALLS
# =====================================================================

def run(prompt: str) -> str:
    """
    MAIN HELPER INTERFACE.
    Your Master File will call helper_scriptor.run(prompt)
    """
    if ENGINE is None:
        return "[helper_scriptor] ERROR: Engine not available."

    try:
        answer = ENGINE.generate_reply(prompt, _llm_call)
        return str(answer)
    except Exception as e:
        return f"[helper_scriptor ERROR: {e}]"


# =====================================================================
# STANDALONE TESTING
# =====================================================================

if __name__ == "__main__":
    print("helper_scriptor.py — standalone test mode\n")
    while True:
        try:
            prompt = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting helper.")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit"):
            print("Bye.")
            break

        print("RomanAI (helper_scriptor)>", run(prompt), "\n")

