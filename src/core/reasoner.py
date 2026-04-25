import httpx
import json
import asyncio

class Reasoner:
    def __init__(self, model="qwen2:1.5b"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

    async def decide(self, snapshot):

        # ✅ Short, structured prompt (better for small models)
        prompt = f"""
You are a memory controller.

Processes:
{json.dumps(snapshot)}

Select ONE process to suspend to reduce memory usage.

Rules:
- Output ONLY valid JSON.
- No text outside JSON.
- Format:
{{"action":"SIGSTOP","pid":1234,"reason":"short"}}
- If no action needed:
{{"action":"NONE","pid":0,"reason":"stable"}}
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,      # ✅ Deterministic
                "num_predict": 120       # ✅ Prevent over-generation
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.post(self.url, json=payload, timeout=1.0),
                    timeout=1.0
                )

                if response.status_code != 200:
                    raise Exception("HTTP error")

                data = response.json()
                raw = data.get("response", "{}")

                try:
                    result = json.loads(raw)

                    if not isinstance(result, dict):
                        raise ValueError("Invalid JSON structure")

                    if "action" not in result or "pid" not in result:
                        raise ValueError("Missing fields")

                except Exception:
                    raise Exception("Malformed AI output")

                return result

        except Exception as e:
            # ✅ Safe fallback
            return {
                "action": "NONE",
                "pid": 0,
                "reason": f"AI Fallback: {str(e)[:20]}"
            }