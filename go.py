"""
go.py — OAuth harvest. Браузер → логин GitHub → OAuth на платформах → токены.
"""
import sys, os, json, time, asyncio
from pathlib import Path
from urllib.parse import urlparse, parse_qs

PROFILE = "C:/Users/User/AppData/Local/Temp/pw_gh3"
OUTPUT = Path("C:/Users/User/Desktop/farm/gh-farm3/harvested.json")

PLATFORMS = [
    {"id": "tabiai", "name": "Tabi AI", "url": "https://tabitoken.com/sign-up", "reward": "$120"},
    {"id": "gorouter", "name": "GoRouter", "url": "https://gorouter.app/sign-up", "reward": "$70"},
    {"id": "codebuddy", "name": "CodeBuddy", "url": "https://www.codebuddy.ai", "reward": "250cr"},
]

async def main():
    from playwright.async_api import async_playwright
    
    print("=== OAuth Harvest ===\n")
    
    existing = []
    if OUTPUT.exists():
        existing = json.loads(OUTPUT.read_text(encoding='utf-8'))
    
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE,
            headless=False,
            args=["--no-sandbox"],
            viewport={"width": 1366, "height": 768},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        
        await page.goto("https://github.com", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        logged_in = await page.evaluate("() => !!document.querySelector('meta[name=\"user-login\"]')?.content")
        
        if not logged_in:
            print("[!] Не залогинен. Логинься в окне браузера (90с)...")
            await page.goto("https://github.com/login", wait_until="domcontentloaded")
            for i in range(90, 0, -10):
                await asyncio.sleep(10)
                logged_in = await page.evaluate("() => !!document.querySelector('meta[name=\"user-login\"]')?.content")
                if logged_in:
                    break
                print(f"  [*] {i-10}с...")
        
        if not logged_in:
            print("[-] Выход.")
            await ctx.close()
            return
        
        user = await page.evaluate("() => document.querySelector('meta[name=\"user-login\"]')?.content")
        print(f"[+] GitHub: {user}")
        
        for p in PLATFORMS:
            print(f"\n--- {p['name']} ({p['reward']}) ---")
            try:
                await page.goto(p["url"], wait_until="networkidle", timeout=30000)
                await asyncio.sleep(3)
                
                clicked = False
                for sel in ["a[href*='github']", "button:has-text('GitHub')"]:
                    try:
                        btn = page.locator(sel).first
                        if await btn.is_visible(timeout=2000):
                            await btn.click()
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    links = await page.evaluate("() => [...document.querySelectorAll(\"a[href*='github']\")].map(e => e.href)")
                    gh = [l for l in links if 'github.com/login/oauth' in l]
                    if gh:
                        await page.goto(gh[0], wait_until="networkidle")
                        clicked = True
                
                if not clicked:
                    print(f"  [-] No GitHub button")
                    continue
                
                await asyncio.sleep(3)
                if "github.com" in page.url:
                    try:
                        auth = page.locator("button[name='authorize'], button:has-text('Authorize')").first
                        if await auth.is_visible(timeout=5000):
                            await auth.click()
                            print(f"  [+] Authorized")
                            await asyncio.sleep(5)
                    except:
                        print(f"  [-] No Authorize")
                        continue
                
                await asyncio.sleep(5)
                url = page.url
                token = None
                parsed = urlparse(url)
                for param in ["token", "access_token", "accessToken", "session", "key", "code"]:
                    for qs in [parse_qs(parsed.query), parse_qs(parsed.fragment)]:
                        if param in qs:
                            token = qs[param][0]
                            break
                
                if not token:
                    try:
                        ls = json.loads(await page.evaluate("() => JSON.stringify(localStorage)"))
                        for k in ["token", "accessToken", "access_token", "authToken", "session"]:
                            if k in ls:
                                token = ls[k]
                                break
                    except:
                        pass
                
                if token:
                    r = {"platform": p["id"], "name": p["name"], "reward": p["reward"], "token": token, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                    existing.append(r)
                    OUTPUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
                    print(f"  [+] TOKEN: {token[:40]}...")
                else:
                    print(f"  [-] URL: {url[:80]}")
            except Exception as e:
                print(f"  [-] {str(e)[:100]}")
        
        await ctx.close()
    print(f"\n=== {len(existing)} tokens ===")

if __name__ == "__main__":
    asyncio.run(main())