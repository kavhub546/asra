import sys
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import asyncio

# --- FIX: Point Python to the 'src' directory ---
# This adds the folder containing your state.py and main.py to Python's "search path"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import cleanly
from state import shared_state
from main import main as engine_main

app = FastAPI(title="ASRA Dashboard")


# ✅ Start engine when FastAPI starts
@app.on_event("startup")
async def start_engine():
    asyncio.create_task(engine_main())


# ✅ GET Live Status
@app.get("/status")
def get_status():
    return shared_state.snapshot()


# ✅ POST Resume All Trigger
@app.post("/resume")
def resume_all():
    shared_state.request_resume_all()
    return {"status": "Resume triggered"}


# ✅ Dashboard UI
@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ASRA Dashboard</title>

    <style>
        body {
            background-color: #0f172a;
            color: #e2e8f0;
            font-family: "Segoe UI", Arial, sans-serif;
            text-align: center;
            padding: 40px;
        }

        h1 {
            margin-bottom: 30px;
            font-weight: 600;
        }

        .state-banner {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 20px;
        }

        .stable { color: #22c55e; }
        .warning { color: #facc15; }
        .critical { color: #ef4444; }

        .card {
            background-color: #1e293b;
            padding: 30px;
            margin: 0 auto 30px auto;
            width: 65%;
            border-radius: 16px;
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
        }

        .metric {
            font-size: 20px;
            margin: 10px 0;
        }

        .bar-container {
            background-color: #334155;
            border-radius: 10px;
            height: 18px;
            margin: 20px 0;
            overflow: hidden;
        }

        .bar {
            height: 100%;
            width: 0%;
            background-color: #22c55e;
            transition: width 0.5s ease, background-color 0.5s ease;
        }

        .trend {
            font-family: monospace;
            margin-top: 15px;
            font-size: 20px;
        }

        button {
            margin-top: 20px;
            padding: 10px 20px;
            font-size: 16px;
            background-color: #3b82f6;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }

        button:hover {
            background-color: #2563eb;
        }

        .history {
            text-align: left;
            font-family: monospace;
            font-size: 14px;
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
        }

        .history-entry {
            margin-bottom: 5px;
            opacity: 0.8;
        }
    </style>
</head>

<body>

    <h1>ASRA — Autonomous System Resilience Agent</h1>

    <div id="state" class="state-banner">Loading...</div>

    <div class="card">

        <div class="bar-container">
            <div id="memBar" class="bar"></div>
        </div>

        <div id="memory" class="metric"></div>
        <div id="stability" class="metric"></div>
        <div id="suspended" class="metric"></div>
        <div id="ai_calls" class="metric"></div>
        <div id="decision" class="metric"></div>
        <div id="action_type" class="metric"></div>

        <div id="trend" class="trend"></div>

        <button onclick="triggerResume()">Resume All</button>

        <div class="history" id="history"></div>

    </div>

<script>

    function sparkline(data) {
        const bars = "▁▂▃▄▅▆▇█";
        if (!data.length) return "";
        let min = Math.min(...data);
        let max = Math.max(...data);
        let span = max - min || 1;

        return data.map(v => {
            let idx = Math.floor((v - min) / span * (bars.length - 1));
            return bars[idx];
        }).join("");
    }

    async function fetchStatus() {
        const res = await fetch('/status');
        const data = await res.json();

        let stateText = "";
        let stateClass = "";
        let barColor = "#22c55e";

        if (data.mem_pct < 75) {
            stateText = "STABLE";
            stateClass = "stable";
            barColor = "#22c55e";
        } else if (data.mem_pct < 90) {
            stateText = "WARNING";
            stateClass = "warning";
            barColor = "#facc15";
        } else {
            stateText = "CRITICAL PRESSURE";
            stateClass = "critical";
            barColor = "#ef4444";
        }

        document.getElementById("state").innerHTML =
            `<span class="${stateClass}">${stateText}</span>`;

        document.getElementById("memory").innerText =
            `Memory Usage: ${data.mem_pct.toFixed(1)}%`;

        document.getElementById("stability").innerText =
            `Stability Score: ${data.stability.toFixed(1)}%`;

        document.getElementById("suspended").innerText =
            `Suspended Processes: ${data.suspended_count}`;

        document.getElementById("ai_calls").innerText =
            `AI Decisions: ${data.ai_calls}`;

        document.getElementById("decision").innerText =
            `Last Action: ${data.last_decision}`;

        document.getElementById("action_type").innerText =
            `Decision Source: ${data.last_action_type}`;

        document.getElementById("trend").innerText =
            sparkline(data.mem_history);

        const bar = document.getElementById("memBar");
        bar.style.width = data.mem_pct + "%";
        bar.style.backgroundColor = barColor;

        // ✅ Render history
        const historyDiv = document.getElementById("history");
        historyDiv.innerHTML = "<strong>Action History:</strong><br>";

        data.action_history.forEach(entry => {
            historyDiv.innerHTML += `<div class="history-entry">${entry}</div>`;
        });
    }

    async function triggerResume() {
        await fetch('/resume', { method: 'POST' });
    }

    setInterval(fetchStatus, 1000);
    fetchStatus();

</script>

</body>
</html>
"""