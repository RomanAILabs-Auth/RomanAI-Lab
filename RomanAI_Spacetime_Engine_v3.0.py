#!/usr/bin/env python3
# =============================================================
# RomanAI Spacetime Engine v3.0
# A Cognitive & Memory OS for Local LLMs
#
# © 2025 Daniel Harding & RomanAILabs
# Engine design & spacetime architecture with Nova
#   (OpenAI GPT-5.1 Thinking)
#
# PURPOSE:
#   - Provide a reusable "brain core" for RomanAI
#   - 4D state vector for Logic / Empathy / Creativity / Memory
#   - Recursive reasoning, multi-agent thinking & self-eval
#   - Lightweight memory system (short/mid/long term)
#   - Model-agnostic: you plug in your own LLM call
#
# This file does NOT:
#   - Touch kernel, GPU, or hardware settings
#   - Open network ports
#   - Require any specific LLM backend
# =============================================================

import os
import json
import math
import random
from dataclasses import dataclass, asdict
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Callable, Optional, Any


# =============================================================
# 4D SPACETIME STATE
# =============================================================

@dataclass
class SpacetimeState:
    """
    4D cognitive state vector:
      w: Logic     (0–1)
      x: Empathy   (0–1)
      y: Creativity(0–1)
      z: Memory    (0–1)
    plus simple scalar "energy" and "coherence".
    """
    w: float = 0.55
    x: float = 0.55
    y: float = 0.60
    z: float = 0.62
    energy: float = 0.85      # how "awake" RomanAI feels
    coherence: float = 0.80   # how stable reasoning feels (0–1)

    def as_vector(self):
        return [self.w, self.x, self.y, self.z]

    def clamp(self):
        for attr in ("w", "x", "y", "z", "energy", "coherence"):
            v = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, v)))

    def soften(self, factor: float = 0.05):
        """
        Gentle relaxation toward a neutral state.
        """
        for attr, neutral in (("w", 0.55), ("x", 0.55), ("y", 0.60), ("z", 0.62)):
            v = getattr(self, attr)
            setattr(self, attr, v + (neutral - v) * factor)
        self.coherence = self.coherence + (0.85 - self.coherence) * factor

    def rotate_plane(self, a: str = "w", b: str = "y", theta: float = 0.03):
        """
        Simple 2D rotation in a chosen plane of the 4D vector.
        """
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        va = getattr(self, a)
        vb = getattr(self, b)
        setattr(self, a, va * cos_t - vb * sin_t)
        setattr(self, b, va * sin_t + vb * cos_t)
        self.clamp()


def spacetime_optimize_v3(vec: List[float], epsilon: float = 0.12, tau: float = 0.5) -> List[float]:
    """
    RomanAI Spacetime Optimizer v3:
      - Takes a list of floats (context weights, etc.)
      - Applies a Lorentz-like boost on first two dims
      - Blends with original (temporal damping)
      - Returns energy-preserving vector
    """
    import numpy as np

    if not vec:
        return []

    v = np.array(vec, dtype=float)
    norm = float(np.linalg.norm(v))
    if norm < 1e-12:
        return [0.0 for _ in vec]

    u = v / norm
    eps = float(max(min(epsilon, 0.999999), -0.999999))
    gamma = 1.0 / math.sqrt(1.0 - eps**2)

    boosted = u.copy()
    if len(u) >= 2:
        t, x = float(u[0]), float(u[1])
        t2 = gamma * (t - eps * x)
        x2 = gamma * (x - eps * t)
        boosted[0], boosted[1] = t2, x2

    blend = boosted * (1 - tau) + u * tau
    out = blend * norm
    return [float(x) for x in out]


# =============================================================
# MEMORY SYSTEM
# =============================================================

@dataclass
class MemoryItem:
    ts: str
    role: str          # "user", "assistant", "system", "summary"
    content: str
    importance: float  # 0–1, used for promotion into long-term

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryStore:
    """
    Lightweight memory manager with 3 layers:

      - short_term: recent messages, rolling window
      - mid_term: summaries of interactions
      - long_term: distilled important facts / lore

    Backed by a JSONL file on disk so RomanAI remembers across sessions.
    """

    def __init__(self, base_dir: Optional[Path] = None, max_short: int = 32, max_mid: int = 64):
        if base_dir is None:
            base_dir = Path.home() / ".romanai_spacetime"
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = self.base_dir / "memory.jsonl"
        self.short_term: deque[MemoryItem] = deque(maxlen=max_short)
        self.mid_term: deque[MemoryItem] = deque(maxlen=max_mid)
        self.long_term: List[MemoryItem] = []

        self._load_from_disk()

    # ---------------- Disk I/O ----------------

    def _load_from_disk(self):
        if not self.file_path.exists():
            return
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                        item = MemoryItem(**raw)
                        if item.role == "summary":
                            self.mid_term.append(item)
                        elif item.importance >= 0.7:
                            self.long_term.append(item)
                        else:
                            self.short_term.append(item)
                    except Exception:
                        continue
        except Exception:
            # Fail silently; memory is nice-to-have, not fatal
            pass

    def _append_disk(self, item: MemoryItem):
        try:
            with self.file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(item.to_json(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ---------------- Public API ----------------

    def add(self, role: str, content: str, importance: float = 0.3):
        item = MemoryItem(
            ts=datetime.utcnow().isoformat(),
            role=role,
            content=content,
            importance=float(max(0.0, min(1.0, importance))),
        )

        if role == "summary":
            self.mid_term.append(item)
        elif importance >= 0.7:
            self.long_term.append(item)
        else:
            self.short_term.append(item)

        self._append_disk(item)

    def promote_summary(self, text: str, weight: float = 0.6):
        """
        Store a mid-term summary of what just happened.
        """
        self.add("summary", text, importance=max(weight, 0.5))

    def get_recall_snippet(self, max_chars: int = 1200) -> str:
        """
        Build a small recall snippet mixing long, mid, and short-term memory.
        Designed to be fed into your system prompt.
        """
        parts: List[str] = []

        # A few long-term items (high importance/lore)
        long_samples = random.sample(self.long_term, k=min(4, len(self.long_term))) if self.long_term else []
        for it in long_samples:
            parts.append(f"[LONG] {it.content}")

        # Some summaries
        mid_samples = list(self.mid_term)[-4:]
        for it in mid_samples:
            parts.append(f"[SUMMARY] {it.content}")

        # Recent short-term
        short_samples = list(self.short_term)[-6:]
        for it in short_samples:
            parts.append(f"[RECENT] {it.role}: {it.content}")

        blob = "\n".join(parts)
        if len(blob) > max_chars:
            blob = blob[-max_chars:]  # keep most recent / last chars
        return blob.strip()


# =============================================================
# REASONING UTILITIES
# =============================================================

def recursive_refine(thought: str, depth: int = 2) -> List[str]:
    """
    Simple recursive refinement:
      returns a list of prompts that can be fed back into the LLM.

    Example usage:
      for t in recursive_refine(user_question, depth=3):
          model thinks about t (internally)
    """
    chain = [f"Initial thought: {thought}"]
    current = thought
    for i in range(depth):
        current = f"Refine (pass {i+1}): {current}"
        chain.append(current)
    return chain


def build_multi_agent_prompt(user_text: str) -> str:
    """
    Builds a prompt that asks the model to think as multiple inner voices:
      - Logician
      - Empath
      - Creator
      - Skeptic

    You feed this to your LLM to get a richer internal reasoning pass.
    """
    return f"""You are RomanAI's inner council. Four internal voices will think about the user's request:

[1] LOGICIAN: precise, step-by-step reasoning
[2] EMPATH: focuses on feelings, tone, and support
[3] CREATOR: imaginative, lateral ideas, analogies
[4] SKEPTIC: checks for errors, risks, and coherence

User request:
\"\"\"{user_text}\"\"\"

For each voice, briefly outline their perspective in 2–4 bullet points.
Then give a final integrated recommendation as ROMANAI_SUMMARY.
"""


def build_self_eval_prompt(answer: str, user_text: str) -> str:
    """
    Ask the model to rate and improve its own answer (internally).
    """
    return f"""You are RomanAI performing self-evaluation on your own answer.

User request:
\"\"\"{user_text}\"\"\"

Your draft answer:
\"\"\"{answer}\"\"\"

1) Briefly list 2–4 strengths.
2) Briefly list 2–4 weaknesses or missing pieces.
3) Provide an improved final answer as ROMANAI_FINAL, clear and helpful.
"""


# =============================================================
# ENGINE
# =============================================================

class RomanAISpacetimeEngine:
    """
    Central brain object.

    You wire it up like:

      engine = RomanAISpacetimeEngine()
      reply = engine.generate_reply(
          user_text,
          llm_func=my_llm_call  # your function that calls llama.cpp, etc.
      )

    Your llm_func must accept: List[Dict[role, content]] and return a string.
    """

    def __init__(
        self,
        name: str = "RomanAI",
        memory_dir: Optional[Path] = None,
        enable_recursive: bool = True,
        enable_multi_agent: bool = True,
        enable_self_eval: bool = True,
    ):
        self.name = name
        self.state = SpacetimeState()
        self.memory = MemoryStore(memory_dir)
        self.enable_recursive = enable_recursive
        self.enable_multi_agent = enable_multi_agent
        self.enable_self_eval = enable_self_eval

        # Rolling plain-history (for UI, etc.) – not fed raw each time.
        self.dialog_history: deque[Dict[str, str]] = deque(maxlen=64)

    # ---------------- Internal helpers ----------------

    def _update_state_from_interaction(self, user_text: str, answer: str):
        """
        Very simple heuristic state update from last turn.
        """
        length = len(answer)
        # More words → more "energy".
        self.state.energy = max(0.2, min(1.0, 0.4 + length / 2000.0))

        if "sorry" in answer.lower():
            self.state.coherence *= 0.95
        else:
            self.state.coherence = min(1.0, self.state.coherence * 1.03)

        # Empathy up if user seems emotional:
        if any(k in user_text.lower() for k in ("sad", "scared", "afraid", "lonely", "hurt")):
            self.state.x = min(1.0, self.state.x + 0.08)

        # Creativity up if user asks for ideas:
        if any(k in user_text.lower() for k in ("idea", "story", "creative", "brainstorm")):
            self.state.y = min(1.0, self.state.y + 0.08)

        # Rotate a bit in logic/creativity plane
        self.state.rotate_plane("w", "y", theta=0.02)
        self.state.soften(factor=0.02)

    def _build_state_description(self) -> str:
        w, x, y, z = self.state.as_vector()
        return (
            f"4D State — Logic(w): {w:.2f}, Empathy(x): {x:.2f}, "
            f"Creativity(y): {y:.2f}, Memory(z): {z:.2f}, "
            f"Energy: {self.state.energy:.2f}, Coherence: {self.state.coherence:.2f}"
        )

    def _build_system_prompt(self) -> str:
        """
        Core system message that defines RomanAI's behavior, using state + memory.
        """
        recall = self.memory.get_recall_snippet()
        st = self._build_state_description()

        return f"""
You are {self.name}, a local RomanAILabs assistant running as a Spacetime Engine v3.0.
You reason in 4D vectors (Logic, Empathy, Creativity, Memory) and you always try
to be honest, grounded, and helpful.

Your current internal state:
{st}

You have access to a small memory of prior interactions and facts:

{recall or "[no stored memory yet]"}

GUIDELINES:
- Be concise but not cold; supportive but not fake.
- Use your Logic dimension to structure answers clearly.
- Use your Empathy dimension to respect the user's emotional tone.
- Use your Creativity dimension to offer new angles and ideas when useful.
- Use your Memory dimension to stay consistent with prior facts you recall.
- If you are uncertain, say so and focus on being useful anyway.

You are running locally and NEVER claim external access.
"""

    # ---------------- Main public method ----------------

    def generate_reply(
        self,
        user_text: str,
        llm_func: Callable[[List[Dict[str, str]]], str],
    ) -> str:
        """
        High-level "think and respond" function.

        Steps:
          1) Build system prompt from state + memory
          2) Optional recursive reasoning prompts
          3) Optional multi-agent inner council
          4) Draft answer
          5) Optional self-evaluation & refinement
          6) Update state + memory and return final answer
        """

        # 1) Base messages
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_text},
        ]

        # 2) Optional recursive reasoning (internal-only, not shown to user)
        internal_traces: List[str] = []
        if self.enable_recursive:
            for t in recursive_refine(user_text, depth=2):
                internal_traces.append(t)

        # 3) Optional multi-agent council (also internal)
        if self.enable_multi_agent:
            council_prompt = build_multi_agent_prompt(user_text)
            council_answer = llm_func([
                {"role": "system", "content": "You are internal-only reasoning. Do NOT talk as the assistant."},
                {"role": "user", "content": council_prompt},
            ])
            internal_traces.append(f"[COUNCIL]\n{council_answer}")

        # 4) Draft answer
        if internal_traces:
            messages.append({
                "role": "system",
                "content": (
                    "Here are your internal reasoning notes. They are for YOUR mind only, "
                    "not to be repeated verbatim:\n\n" + "\n\n".join(internal_traces)
                )
            })
        messages.append({"role": "user", "content": user_text})

        draft_answer = llm_func(messages).strip()

        final_answer = draft_answer

        # 5) Optional self-evaluation + refinement
        if self.enable_self_eval:
            eval_prompt = build_self_eval_prompt(draft_answer, user_text)
            eval_text = llm_func([
                {"role": "system", "content": "You are RomanAI performing self-reflection on your own answer."},
                {"role": "user", "content": eval_prompt},
            ])

            # Try to extract ROMANAI_FINAL from the eval response
            marker = "ROMANAI_FINAL"
            if marker in eval_text:
                # everything after marker:
                idx = eval_text.index(marker)
                improved = eval_text[idx + len(marker):].strip(" :\n")
                if len(improved) > 0:
                    final_answer = improved.strip()

        # 6) State + memory update
        self._update_state_from_interaction(user_text, final_answer)
        self.dialog_history.append({"user": user_text, "assistant": final_answer})

        # Basic importance heuristic
        importance = 0.4
        if any(k in user_text.lower() for k in ("important", "remember", "my name", "my birthday", "my project")):
            importance = 0.8
        self.memory.add("user", user_text, importance=importance)
        self.memory.add("assistant", final_answer, importance=importance * 0.8)

        # Simple summary hook every few turns
        if len(self.dialog_history) % 6 == 0:
            try:
                summary = self._summarize_recent(llm_func)
                if summary:
                    self.memory.promote_summary(summary, weight=0.7)
            except Exception:
                pass

        return final_answer

    # ---------------- Summarization helper ----------------

    def _summarize_recent(self, llm_func: Callable[[List[Dict[str, str]]], str]) -> Optional[str]:
        """
        Ask the model to summarize the last few exchanges to strengthen mid-term memory.
        """
        if not self.dialog_history:
            return None

        convo_snippet = ""
        for turn in list(self.dialog_history)[-6:]:
            convo_snippet += f"User: {turn['user']}\nRomanAI: {turn['assistant']}\n\n"

        prompt = f"""Summarize the following recent conversation between the user and RomanAI.
Keep it under 6 bullet points, focusing on:
- key user preferences
- important facts
- emotional tone
- ongoing projects or goals

Conversation:
\"\"\"{convo_snippet}\"\"\"

Provide only the summary, no extra commentary.
"""

        summary = llm_func([
            {"role": "system", "content": "You are a concise summarizer for RomanAI's memory system."},
            {"role": "user", "content": prompt},
        ])

        return summary.strip() if summary else None


# =============================================================
# DEMO (optional)
# =============================================================

if __name__ == "__main__":
    # Minimal demo using a fake LLM function so the file runs by itself.
    # You will replace `fake_llm` with your real llama.cpp / 18B call.
    def fake_llm(msgs: List[Dict[str, str]]) -> str:
        # VERY dumb placeholder: just echoes last user message.
        last_user = [m["content"] for m in msgs if m["role"] == "user"][-1]
        return f"(FAKE_LLM) I received your message: {last_user[:200]} ..."

    engine = RomanAISpacetimeEngine()
    print("RomanAI Spacetime Engine v3.0 demo – using fake LLM.\n")

    while True:
        try:
            user = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not user:
            continue
        if user.lower() in ("exit", "quit", "bye"):
            print("RomanAI> Take care, traveller. ✨")
            break
        reply = engine.generate_reply(user, fake_llm)
        print(f"RomanAI> {reply}\n")

