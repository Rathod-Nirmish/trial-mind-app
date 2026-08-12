import google.generativeai as genai
import re
from trialmind.config import get_settings

genai.configure(api_key=get_settings().gemini_api_key)

for m in [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-2.5-flash",
]:
    try:
        r = genai.GenerativeModel(m).generate_content("reply ok")
        print(f"  {m}: OK ({r.text.strip()[:20]})")
    except Exception as e:
        msg = str(e)
        if "429" in msg:
            q = re.search(r'quota_id: "([^"]+)"', msg)
            d = re.search(r"retry.{0,10}(\d+)", msg)
            print(f"  {m}: 429 {q.group(1) if q else '?'} retry={d.group(1) if d else '?'}s")
        else:
            print(f"  {m}: ERR {type(e).__name__}: {msg[:80]}")
