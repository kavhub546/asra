# 🚀 ASRA: Autonomous System Resilience Agent

**ASRA** is an AI-augmented real-time memory orchestration engine that prevents system instability. Instead of reacting to crashes like a standard OOM (Out-Of-Memory) killer, ASRA proactively monitors system memory velocity and dynamically throttles non-critical processes to preserve system uptime.

## 🎥 Live Demo
**View the project walkthrough:** [Watch Demo Video](demo.mp4)
---

## 💡 The Problem
Operating systems are **reactive**. When RAM is exhausted, they trigger an OOM killer that randomly terminates processes, causing data loss and system stutters (thrashing). 

## ⚡ The ASRA Solution
ASRA is **proactive**. It treats system memory as a managed resource, prioritizing stability over raw, unchecked process execution. It acts as a "safety harness" for your OS.

---

## 🏗 Architecture: A Layered Defense
ASRA uses a multi-layered approach to ensure reliability:

1.  **Survival Layer (Fast Path):** Deterministic, hard-coded logic. If memory > 93% or a rapid spike is detected, it acts in milliseconds. No AI latency, no risk.
2.  **Logic Plane (AI):** Uses a lightweight LLM (`qwen2:1.5b`) to reason about which processes are non-critical and can be safely throttled.
3.  **Safety Gate:** The "Circuit Breaker." It enforces a hard-coded whitelist, ensuring system-critical processes (Kernel, Drivers, Ollama) can never be touched.
4.  **Observability Plane:** A real-time FastAPI-powered dashboard that visualizes system pressure, AI decision logs, and memory reclamation metrics.

---

## 🛠 Tech Stack
- **Engine:** Python `psutil` (Process management)
- **Intelligence:** Ollama (Llama3/Qwen2) via `httpx`
- **Dashboard:** FastAPI + `Rich` (Terminal) + HTML/JS (Web)
- **Safety:** Deterministic process-tree verification

---

## 🚀 Key Features
- **Predictive Throttling:** Detects "Memory Velocity" (how fast RAM is filling up) rather than just waiting for a static percentage.
- **Circuit Breaker:** Hard-coded protection for kernel/system processes ensures system integrity.
- **Recursive Resume:** Automatically restores process trees (including children) when memory pressure subsides.
- **Telemetry Dashboard:** Live tracking of system stability, AI decision history, and memory pressure.

---

## ⚙️ Installation
1. Install dependencies:
   ```bash
   pip install psutil httpx fastapi uvicorn rich
