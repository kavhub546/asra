import asyncio
import psutil
import atexit
import time

from core.monitor import SystemObserver
from core.controller import Controller
from core.reasoner import Reasoner
from state import shared_state

ctrl = Controller()
observer = SystemObserver()
brain = Reasoner(model="qwen2:1.5b")

mem_buffer = []
stable_ticks = 0


def cleanup():
    print("\n[ASRA] EMERGENCY CLEANUP: Resuming all processes...")
    ctrl.resume_all()


atexit.register(cleanup)


async def main():
    global stable_ticks

    print("[ASRA] Engine started.")

    while True:

        # ✅ Check if Resume All was requested from Web UI
        if shared_state.consume_resume_flag():
            ctrl.resume_all()
            shared_state.add_history(
                f"[{time.strftime('%H:%M:%S')}] Manual Resume All Triggered"
            )

        # 1️⃣ Observe
        snapshot = observer.get_snapshot()
        mem_pct = psutil.virtual_memory().percent

        # 2️⃣ Spike detection
        mem_buffer.append(mem_pct)
        if len(mem_buffer) > 20:
            mem_buffer.pop(0)

        is_spike = (
            len(mem_buffer) >= 3
            and (mem_buffer[-1] - mem_buffer[-3]) > 4
            and mem_pct > 75
        )

        decision = {
            "action": "NONE",
            "pid": 0,
            "reason": "System Stable"
        }

        action_type = "NONE"

        # 3️⃣ FAST PATH
        if snapshot and (mem_pct > 93.0 or is_spike):

            candidate_found = False

            for proc in snapshot:
                safe, _ = ctrl._is_safe(proc["pid"])
                if safe:
                    decision = {
                        "action": "SIGSTOP",
                        "pid": proc["pid"],
                        "reason": "FAST PATH: Critical Pressure"
                    }
                    action_type = "FAST_PATH"
                    candidate_found = True
                    break

            if not candidate_found:
                decision["reason"] = "FAST PATH: No safe candidate"

        # 4️⃣ LLM PATH
        elif snapshot:
            shared_state.ai_calls += 1

            ai_decision = await brain.decide(snapshot)

            if (
                isinstance(ai_decision, dict)
                and ai_decision.get("action") == "SIGSTOP"
                and isinstance(ai_decision.get("pid"), int)
                and any(p["pid"] == ai_decision["pid"] for p in snapshot)
            ):
                decision = ai_decision
                action_type = "AI"

        # 5️⃣ Execution
        if decision.get("action") == "SIGSTOP" and decision.get("pid"):

            success, reason = ctrl.suspend(decision["pid"])

            if success:
                shared_state.actions_taken += 1
                decision["reason"] = (
                    f"Actioned PID {decision['pid']} | {reason}"
                )
                stable_ticks = 0

                # ✅ Log action
                shared_state.add_history(
                    f"[{time.strftime('%H:%M:%S')}] Suspended PID {decision['pid']} ({action_type})"
                )
            else:
                decision["reason"] = f"Blocked | {reason}"

        # 6️⃣ Resume Hysteresis
        if mem_pct < 70:
            stable_ticks += 1
        else:
            stable_ticks = 0

        if stable_ticks >= 5:
            resumed = ctrl.resume_one()
            if resumed:
                decision["reason"] = "Recovered: Resumed one process"

                shared_state.add_history(
                    f"[{time.strftime('%H:%M:%S')}] Auto Resume Triggered"
                )

            stable_ticks = 0

        # 7️⃣ Update Shared State
        shared_state.update(
            mem_pct=mem_pct,
            stability=max(0, 100 - mem_pct),
            suspended_count=len(ctrl.suspended_processes),
            last_decision=decision.get("reason", ""),
            last_action_type=action_type,
            mem_history=list(mem_buffer),
        )

        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass