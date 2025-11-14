#!/usr/bin/env python3
# =============================================================
# tool_rewriter.py
# RomanAI Utility Tool — Text & Code Rewriter
#
# © 2025 RomanAILabs — Daniel Harding
# Co-Architect: Nova (GPT-5.1 Thinking)
#
# PURPOSE:
#   Small helper tool used by RomanAI Lab to provide:
#       - Text rewriting
#       - Code refactoring
#       - Explanation simplification
#       - Polishing or restructuring
#
#   This is *not* a patcher — it is a transformation tool.
#
#   It plugs directly into the dropdown backend:
#       "Tool Rewriter"
#
# API:
#       run(prompt: str) -> str
#
# ENGINE:
#   Fully uses Spacetime Engine v3.0 for structured reasoning.
# =============================================================

import os
import importlib.util

# =============================================================
# Load Spacetime Engine v3.0
# =============================================================

ENGINE = None

def _load_engine():
    global ENGINE
    engine_filename = "RomanAI_Spacetime_Engine_v3.0.py"
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, engine_filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            "[tool_rewriter] Cannot find RomanAI_Spacetime_Engine_v3.0.py"
        )

    spec = importlib.util.spec_from_file_location("romanai_spacetime_engine", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    ENGINE = module.RomanAISpacetimeEngine("Tool Rewriter")

_load_engine()

# =============================================================
# Optional lightweight GGUF rewriter model
# =============================================================

try:
    from llama_cpp import Llama

    REWRITER_GGUF = "rewriter_helper.gguf"

    if os.path.exists(REWRITER_GGUF):
        _rewrite_llm = Llama(
            model_path=REWRITER_GGUF,
            n_ctx=4096,
            n_threads=max(1, (os.cpu_count() or 4)//2),
            n_gpu_layers=0,
            verbose=False
        )
    else:
        _rewrite_llm = None
except Exception:
    _rewrite_llm = None

# =============================================================
# Fallback rewriting engine (no GGUF)
# =============================================================

def _fallback(messages):
    """
    Lightweight restructuring logic if no GGUF is present.
    Produces simpler, clearer versions of the content.
    """
    user_text = ""
    for m in messages:
        if m.get("role") == "user":
            user_text = m.get("content", "")

    return (
        "[Rewriter Fallback]\n"
        "No GGUF model found. Performing simplification:\n\n"
        "=== Rewritten Text ===\n"
        + user_text.replace("    ", "  ")
                   .replace("\t", "  ")
                   .strip()
                   .replace("\n\n\n", "\n\n")
    )

# =============================================================
# LLM adapter for rewriting
# =============================================================

def _llm(messages):
    if _rewrite_llm:
        try:
            out = _rewrite_llm.create_chat_completion(
                messages=messages,
                max_tokens=2048,
                temperature=0.6,
            )
            return out["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[rewriter GGUF error: {e}]"

    return _fallback(messages)

# =============================================================
# PUBLIC API
# =============================================================

def run(prompt: str) -> str:
    """
    The Master File calls this function when you select:
        Tool Rewriter
    """
    if ENGINE is None:
        return "[tool_rewriter] ERROR: Spacetime Engine unavailable."

    try:
        rewriter_prompt = (
            "You are RomanAI Rewriter Tool.\n"
            "Rewrite, polish, or restructure the following text/code.\n"
            "Preserve meaning and accuracy.\n"
            "Improve clarity, structure, and flow.\n"
            "Do NOT hallucinate.\n\n"
            f"CONTENT:\n{prompt}\n"
            "=== END CONTENT ==="
        )

        answer = ENGINE.generate_reply(rewriter_prompt, _llm)
        cleaned = str(answer).replace("```python", "").replace("```", "").strip()
        return cleaned

    except Exception as e:
        return f"[tool_rewriter ERROR: {e}]"

# =============================================================
# Standalone tool test
# =============================================================

if __name__ == "__main__":
    print("tool_rewriter.py — standalone rewriter tool\n")
    while True:
        try:
            msg = input("Rewrite> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting rewriter.")
            break

        if not msg:
            continue
        if msg.lower() in ("exit", "quit"):
            break

        print("\nRewritten:\n")
        print(run(msg))
        print("\n")

