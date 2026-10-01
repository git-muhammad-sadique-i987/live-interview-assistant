"""Regenerate the README screenshots in docs/images from the DEMO vault (fictional data only).

    python tools/readme_screenshots.py [OUTPUT_DIR]      # default: docs/images

Run it after a visible UI change so the README never shows an old interface. It reuses
qa/frontend_check.py's sandbox (a copy of the working tree, the demo index, headless Chrome) and
asks about six questions, so it needs INTERVIEW_ASSISTANT_GEMINI_KEY and costs about two cents.
No real key is ever visible: the shots stop above the API key list, and the sandbox holds no other
keys."""
import base64, importlib.util, json, os, shutil, subprocess, sys, tempfile, time, urllib.parse
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("fc", APP / "qa" / "frontend_check.py")
fc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fc)
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else APP / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True)

CASE = """<!doctype html><title>Case study: checkout errors</title><!-- checkout-review -->
<style>body{font-family:Segoe UI,Arial,sans-serif;margin:32px;max-width:760px;color:#222}</style>
<h1>Case study: checkout errors</h1>
<p>Checkout requests have failed with HTTP 502 since the 14:05 deploy. The NGINX error log shows
"upstream prematurely closed connection while reading response header". The app servers restarted
twice in that window.</p>
<iframe style="width:700px;height:330px;border:1px solid #ccc" srcdoc="<p style='font-family:Segoe UI,Arial'>Answer both questions.</p>
<label style='font-family:Segoe UI,Arial'>1. What is the most likely cause of the 502 errors?</label><br>
<textarea rows=4 style='width:640px'></textarea><br>
<label style='font-family:Segoe UI,Arial'>2. How would you confirm it before rolling back?</label><br>
<textarea rows=4 style='width:640px'></textarea>"></iframe>"""


def shot(c, name, clip=None):
    params = {"format": "png"}
    if clip:
        params["clip"] = dict(clip, scale=1)
    data = c.call("Page.captureScreenshot", params)["data"]
    (OUT / name).write_bytes(base64.b64decode(data))
    print("saved", name, (OUT / name).stat().st_size // 1024, "KB")


port, cdp_port = fc.free_port(), fc.free_port()
base = "http://127.0.0.1:%d" % port
box = fc.make_sandbox(cdp_port, port)
cfg = json.loads((box / "config.json").read_text(encoding="utf-8"))
cfg["interview"]["screen_url_hint"] = ["checkout-review"]
(box / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
profile = Path(tempfile.mkdtemp(prefix="ia-shots-chrome-"))
server = chrome = None
try:
    r = subprocess.run([fc.PY, "-u", "interview_assistant.py", "--build-index"], cwd=str(box),
                       capture_output=True, text=True, timeout=900)
    assert "Index written" in r.stdout, r.stdout[-800:]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("INTERVIEW_ASSISTANT_ANTHROPIC_KEY", None)
    env.pop("INTERVIEW_ASSISTANT_OPENAI_KEY", None)
    (box / "api_keys.json").unlink(missing_ok=True)          # no fake keys in any screenshot
    server = subprocess.Popen([fc.PY, "-u", "interview_assistant.py", "--serve", "--port", str(port)],
                              cwd=str(box), env=env, stdout=open(box / "server.log", "w", encoding="utf-8"),
                              stderr=subprocess.STDOUT)
    for _ in range(120):
        try:
            fc.http_json(base + "/settings", timeout=2); break
        except Exception:
            time.sleep(0.5)
    chrome = subprocess.Popen([fc.find_browser(), "--headless=new", "--remote-debugging-port=%d" % cdp_port,
                               "--user-data-dir=%s" % profile, "--no-first-run", "--no-default-browser-check",
                               "--disable-extensions", "--window-size=1280,800", "--hide-scrollbars", "about:blank"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            version = fc.http_json("http://127.0.0.1:%d/json/version" % cdp_port, timeout=2); break
        except Exception:
            time.sleep(0.5)
    bws = fc.Cdp(version["webSocketDebuggerUrl"])
    tid = bws.call("Target.createTarget", {"url": "about:blank"})["targetId"]
    ws = next(x["webSocketDebuggerUrl"] for x in fc.http_json("http://127.0.0.1:%d/json/list" % cdp_port)
              if x.get("id") == tid)
    c = fc.Cdp(ws); p = fc.Page(c)
    for dom in ("Runtime", "Page", "DOM"):
        c.call(dom + ".enable")
    c.call("Emulation.setDeviceMetricsOverride", {"width": 1280, "height": 800, "deviceScaleFactor": 1, "mobile": False})
    c.call("Page.navigate", {"url": base + "/"})
    p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 30)

    # Settings for the shots: Concise, Lead, Vault only, sources and the scope cue on.
    fc.post_json(base + "/settings", {"depth": "concise", "mode": "lead", "grounding": "strict", "role": "general"})
    c.call("Page.reload"); p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 30)
    p.click("#settingsBtn"); time.sleep(0.4)
    for t in ("sourcesToggle", "scopeCueToggle"):
        if not c.js("document.getElementById('%s').checked" % t):
            p.click("label.switch:has(#%s)" % t)
    time.sleep(0.5)
    c.js("(function(){const p=document.getElementById('settingsPanel'); p.scrollTop = 0; p.scrollLeft = 0;})()")
    time.sleep(0.3)
    rect = c.js("(function(){const p=document.getElementById('settingsPanel').getBoundingClientRect();"
                "const k=document.getElementById('provList').getBoundingClientRect();"
                "return {x:p.left, y:p.top, w:p.width, h:Math.min(k.top - 8, p.bottom) - p.top};})()")
    time.sleep(1.0)
    rect = c.js("(function(){const p=document.getElementById('settingsPanel').getBoundingClientRect();"
                "const k=document.getElementById('provList').getBoundingClientRect();"
                "return {x:p.left, y:p.top, w:p.width, h:Math.min(k.top - 8, p.bottom) - p.top};})()")
    shot(c, "_settings_full.png")
    from PIL import Image
    im = Image.open(OUT / "_settings_full.png")
    im.crop((int(rect["x"]) - 2, int(rect["y"]) - 2, int(rect["x"] + rect["w"]) + 2, int(rect["y"] + rect["h"]))).save(OUT / "settings.png")
    (OUT / "_settings_full.png").unlink()
    p.click("#settingsPanel h2"); p.click("#settingsBtn"); time.sleep(0.4)

    # Answers: a study-tier one first (its own shot), then the production one for the hero.
    fc.ask_and_wait(p, "How does Kubernetes decide where to schedule a pod?")
    time.sleep(0.5)
    shot(c, "answer-conceptual.png", {"x": 320, "y": 88, "width": 960, "height": 370})
    fc.ask_and_wait(p, "What is your experience with Salesforce Apex?")
    fc.post_json(base + "/settings", {"show_sources": False})
    c.call("Page.reload"); p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 30)
    fc.ask_and_wait(p, "How do you troubleshoot a Linux service that will not start?")
    p.click("#tab-history"); time.sleep(0.6)
    c.js("(function(){const t=document.getElementById('toast'); t.classList.remove('show');})()")
    time.sleep(0.6)
    shot(c, "hero.png")

    # Scope it on a vague scenario question, with a reply typed in.
    p.type("#qbox", "Our checkout page got slow right after a deploy. How would you troubleshoot it?")
    time.sleep(0.4)
    p.click("#composerFollowup")
    p.wait("document.querySelectorAll('#clarifyList li').length >= 2", 40)
    p.type("#clarifyConstraints", "Only the web tier, since the 14:05 deploy. Database looks healthy.")
    time.sleep(0.4)
    c.js("(function(){const t=document.getElementById('toast'); t.classList.remove('show');})()")
    time.sleep(0.6)
    shot(c, "scope-it.png")
    p.click("#clarifyClose")

    # A case study on screen: Screen answers from the page, Boxes drafts into its answer fields.
    case = bws.call("Target.createTarget", {"url": "data:text/html;charset=utf-8," + urllib.parse.quote(CASE)})
    time.sleep(1.5)
    bws.call("Target.activateTarget", {"targetId": case["targetId"]})
    n0 = c.js("document.querySelectorAll('#paneHistory .hitem').length")
    p.click("#screenBtn")
    p.wait("document.querySelectorAll('#paneHistory .hitem').length > %d && !document.getElementById('answer').classList.contains('streaming')" % n0, 90, 0.3)
    p.click("#boxesBtn")
    p.wait("document.querySelectorAll('#boxesList .box-row').length === 2", 20)
    p.click("#boxesList .box-row:nth-child(1) .box-actions button:nth-child(1)")
    p.wait("document.querySelector('#boxesList .box-row:nth-child(1) .box-a').value.trim().length > 20", 90, 0.3)
    c.call("Page.bringToFront"); time.sleep(0.8)
    c.js("(function(){const t=document.getElementById('toast'); t.classList.remove('show');})()")
    time.sleep(0.6)
    shot(c, "screen-boxes.png")
    case_ws = next(x["webSocketDebuggerUrl"] for x in fc.http_json("http://127.0.0.1:%d/json/list" % cdp_port)
                   if x.get("id") == case["targetId"])
    bws.call("Target.activateTarget", {"targetId": case["targetId"]})
    cc = fc.Cdp(case_ws); cc.call("Page.enable"); cc.call("Page.bringToFront")
    cc.call("Emulation.setDeviceMetricsOverride", {"width": 820, "height": 560, "deviceScaleFactor": 1, "mobile": False})
    time.sleep(0.8); shot(cc, "case-study-page.png", {"x": 0, "y": 0, "width": 820, "height": 430}); cc.close()
    bws.call("Target.activateTarget", {"targetId": tid}); c.call("Page.bringToFront"); time.sleep(0.5)
    p.click("#boxesClose")

    # Phone: the same session at 390 px (the last answer replays from the session).
    c.call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
    c.call("Page.reload")
    p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 30)
    time.sleep(1.0)
    fc.ask_and_wait(p, "Have you run PostgreSQL replication in production?")
    c.js("(function(){const t=document.getElementById('toast'); t.classList.remove('show');})()")
    time.sleep(0.8)
    shot(c, "phone.png")
finally:
    for proc in (chrome, server):
        if proc and proc.poll() is None:
            proc.terminate()
    time.sleep(1)
    shutil.rmtree(profile, ignore_errors=True)
    shutil.rmtree(box, ignore_errors=True)
