import psutil
import os
import getpass


class Controller:

    PROTECTED_PROCESS_LIST = {
        # Windows critical
        "dwm.exe", "explorer.exe", "svchost.exe", "csrss.exe",
        "wininit.exe", "services.exe", "lsass.exe",
        "fontdrvhost.exe", "system", "winlogon.exe", "smss.exe",

        # ✅ ASRA Infrastructure Protection
        "ollama.exe", "python.exe", "powershell.exe", 
        "cmd.exe", "wt.exe", "conhost.exe",

        # ✅ Demo Critical Apps (Don't kill the recorder!)
        "snippingtool.exe", 
        "screenclippinghost.exe" 
    }

    def __init__(self, max_suspended=3):
        self.max_suspended = max_suspended
        self.suspended_processes = {}
        self.my_pid = os.getpid()
        self.current_user = getpass.getuser().lower()

        # ✅ Load whitelist safely from project root
        self.whitelist = set()

        try:
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..")
            )

            whitelist_path = os.path.join(project_root, "whitelist.txt")

            with open(whitelist_path, "r") as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        self.whitelist.add(name)

            print(f"[ASRA] Loaded {len(self.whitelist)} whitelisted apps from {whitelist_path}")

        except FileNotFoundError:
            print("[ASRA] whitelist.txt not found at expected project root.")

    def _is_safe(self, pid):
        try:
            # 1️⃣ Self Protection
            if pid == self.my_pid:
                return False, "Self-Protection triggered."

            # ✅ Protect Engine Parent Process Tree (CRITICAL FIX)
            try:
                engine_proc = psutil.Process(self.my_pid)
                protected_pids = {engine_proc.pid}

                current = engine_proc
                while current.parent():
                    current = current.parent()
                    protected_pids.add(current.pid)

                if pid in protected_pids:
                    return False, "Protected: Engine parent process tree"

            except Exception:
                pass

            # 2️⃣ Already suspended?
            if pid in self.suspended_processes:
                return False, "Already suspended."

            # 3️⃣ Exists?
            if not psutil.pid_exists(pid):
                return False, "Process no longer exists."

            proc = psutil.Process(pid)

            # 4️⃣ User validation
            username = proc.username() or ""
            if username.split('\\')[-1].lower() != self.current_user:
                return False, "Not user-owned process."

            name = (proc.name() or "").lower()

            # 5️⃣ Hard Protected (System + Infra)
            if name in self.PROTECTED_PROCESS_LIST:
                return False, f"Protected infrastructure: {name}"

            # 6️⃣ User whitelist
            if name in self.whitelist:
                return False, f"Whitelisted: {name}"

            # 7️⃣ Suspension cap
            if len(self.suspended_processes) >= self.max_suspended:
                return False, "Capacity reached (Max 3)."

            return True, "Safe"

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False, "Access Denied or Invalid Process."

    def suspend(self, pid):
        safe, reason = self._is_safe(pid)
        if not safe:
            return False, reason

        try:
            proc = psutil.Process(pid)
            proc.suspend()
            self.suspended_processes[pid] = proc
            return True, f"Throttled {proc.name()}"
        except Exception as e:
            return False, f"Execution error: {str(e)}"

    def resume_one(self):
        if not self.suspended_processes:
            return False

        pid, proc = next(iter(self.suspended_processes.items()))
        try:
            if proc.is_running():
                proc.resume()
            del self.suspended_processes[pid]
            return True
        except Exception:
            del self.suspended_processes[pid]
            return False

    def resume_all(self):
        for pid, proc in list(self.suspended_processes.items()):
            try:
                if proc.is_running():
                    proc.resume()
                del self.suspended_processes[pid]
                print(f"[RESUME] PID {pid}")
            except Exception:
                continue