import psutil
import os
import getpass

class SystemObserver:
    def __init__(self):
        self.my_pid = os.getpid()
        self.current_user = getpass.getuser().lower()

        self.system_blacklist = {
            "system", "wininit.exe", "smss.exe", "csrss.exe",
            "services.exe", "winlogon.exe", "lsass.exe",
            "fontdrvhost.exe"
        }

    def get_snapshot(self):
        snapshot = []

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'username']):
            try:
                pinfo = proc.info

                # 1️⃣ Skip self
                if pinfo['pid'] == self.my_pid:
                    continue

                # 2️⃣ Username check
                username = pinfo.get('username')
                if not username:
                    continue

                user_clean = username.split('\\')[-1].lower()
                if user_clean != self.current_user:
                    continue

                # 3️⃣ Name safety
                name = (pinfo.get('name') or "").lower()
                if not name:
                    continue

                if name in self.system_blacklist:
                    continue

                # 4️⃣ Memory calculation
                mem_info = pinfo.get('memory_info')
                if not mem_info:
                    continue

                mem_mb = mem_info.rss / (1024 * 1024)

                snapshot.append({
                    "pid": pinfo['pid'],
                    "name": pinfo.get('name') or "unknown",
                    "memory_mb": round(mem_mb, 2)
                })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # ✅ Only send Top 5 to LLM (faster, cleaner, safer)
        return sorted(snapshot, key=lambda x: x['memory_mb'], reverse=True)[:8]