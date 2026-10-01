"""Frontend click-through for the Live Interview Assistant overlay.

Why this exists: UI fixes kept being checked from the backend only, and the owner then found buttons
that did nothing in the real page (the provider key Remove button, a notes pane that offered Build
for a folder that was already indexed, toggles stretched to three times their size). This drives the
REAL page in a private headless Chrome, clicks real buttons with mouse events, and checks what
changed on the page AND on the server. Run it after any change to interview_overlay.html or to an
endpoint the page calls.

What it touches: nothing of yours. It copies the app from THIS folder (the working tree, so
uncommitted changes are tested) into a temporary sandbox with the demo vault, fake API keys, and a
stub that stops the sandbox registering global hotkeys next to a running copy of the app. It builds
the demo index there, starts that copy on a free port, and uses a throwaway Chrome profile. The
sandbox is deleted at the end unless --keep.

Not clicked, on purpose: +Frame (it photographs your real desktop), the browser Mic (needs a real
microphone permission), and Start listening unless --listen (it records what your speakers play).

Needs: Chrome or Edge, `pip install websocket-client`, INTERVIEW_ASSISTANT_GEMINI_KEY.
Cost: about 2 cents (the demo index plus a dozen short answers).

Usage: python qa/frontend_check.py [--keep] [--skip-answers] [--listen]
"""
import argparse
import http.client
import json
import os
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
PY = sys.executable
RESULTS = []
FAKE_ENV_CLAUDE = "sk-ant-api03-QA-FAKE-ENV-KEY-111111111111111111111111"
FAKE_FILE_CLAUDE = "sk-ant-api03-QA-FAKE-FILE-KEY-22222222222222222222222"
FAKE_FILE_OPENAI = "sk-proj-QA-FAKE-FILE-KEY-3333333333333333333333333333"


def check(name, ok, note=""):
    RESULTS.append((bool(ok), name, str(note)))
    print("  %-5s %-62s %s" % ("PASS" if ok else "FAIL", name, str(note)[:100]), flush=True)
    return bool(ok)


def section(title):
    print("\n-- %s" % title, flush=True)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def find_browser():
    candidates = [
        os.environ.get("IA_QA_BROWSER", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome") or "", shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "", shutil.which("msedge") or "",
    ]
    return next((c for c in candidates if c and Path(c).exists()), "")


def http_json(url, method="GET", timeout=10):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post_json(url, body, timeout=10):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


# ------------------------------------------------------------------ CDP
class Cdp:
    """Minimal Chrome DevTools Protocol client over one target's websocket."""

    def __init__(self, ws_url):
        import websocket
        self._wsmod = websocket
        self.ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self.n = 0
        self.events = []

    def call(self, method, params=None, timeout=30):
        self.n += 1
        my = self.n
        self.ws.send(json.dumps({"id": my, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            self.ws.settimeout(max(0.05, end - time.time()))
            try:
                msg = json.loads(self.ws.recv())
            except self._wsmod.WebSocketTimeoutException:
                continue
            if msg.get("id") == my:
                if "error" in msg:
                    raise RuntimeError("%s: %s" % (method, msg["error"]))
                return msg.get("result", {})
            if "method" in msg:
                self.events.append(msg)
        raise TimeoutError(method)

    def js(self, expr, timeout=30):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                           "awaitPromise": True}, timeout)
        if r.get("exceptionDetails"):
            d = r["exceptionDetails"]
            raise RuntimeError("JS: " + str((d.get("exception") or {}).get("description") or d)[:300])
        return (r.get("result") or {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


class Page:
    def __init__(self, cdp):
        self.c = cdp
        self._tag = 0

    def wait(self, expr, timeout=10.0, every=0.15):
        end = time.time() + timeout
        while time.time() < end:
            try:
                v = self.c.js(expr)
                if v:
                    return v
            except Exception:
                pass
            time.sleep(every)
        return None

    def click(self, selector):
        """A real mouse click at the element's centre. Refuses an element that is missing,
        zero-sized (hidden) or covered by something else at that point: a click a person could not
        actually make is exactly the class of bug this script exists to catch."""
        info = self.c.js("""(function (sel) {
            const el = document.querySelector(sel);
            if (!el) return {err: 'not found'};
            el.scrollIntoView({block: 'center', inline: 'center'});
            const r = el.getBoundingClientRect();
            if (!r.width || !r.height) return {err: 'zero size (hidden)'};
            const x = r.left + r.width / 2, y = r.top + r.height / 2;
            const top = document.elementFromPoint(x, y);
            if (!top || !(top === el || el.contains(top)))
                return {err: 'covered by ' + (top ? top.tagName.toLowerCase() + (top.id ? '#' + top.id : '') +
                        (top.className && typeof top.className === 'string' ? '.' + top.className.split(' ')[0] : '') : 'nothing')};
            return {x: x, y: y};
        })(%s)""" % json.dumps(selector))
        if not info or info.get("err"):
            raise AssertionError("click %s: %s" % (selector, (info or {}).get("err")))
        self.c.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": info["x"], "y": info["y"]})
        for kind in ("mousePressed", "mouseReleased"):
            self.c.call("Input.dispatchMouseEvent", {"type": kind, "x": info["x"], "y": info["y"],
                                                     "button": "left", "clickCount": 1})

    def click_text(self, container, text, tag="button"):
        """Click the element inside `container` whose visible text is exactly `text`."""
        self._tag += 1
        found = self.c.js("""(function (c, t, tag, n) {
            const root = document.querySelector(c); if (!root) return false;
            const el = [...root.querySelectorAll(tag)].find(e => e.textContent.trim() === t);
            if (!el) return false; el.setAttribute('data-qa-target', n); return true;
        })(%s, %s, %s, %s)""" % (json.dumps(container), json.dumps(text), json.dumps(tag), json.dumps(str(self._tag))))
        if not found:
            raise AssertionError("no %s %r inside %s" % (tag, text, container))
        self.click('[data-qa-target="%d"]' % self._tag)

    def type(self, selector, text):
        self.click(selector)
        self.c.js("(function(){const e=document.querySelector(%s); if (e.select) e.select();})()"
                  % json.dumps(selector))
        self.c.call("Input.insertText", {"text": text})

    def key(self, key, code, vk, text=""):
        base = {"key": key, "code": code, "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
        self.c.call("Input.dispatchKeyEvent", dict(base, type="keyDown", text=text))
        self.c.call("Input.dispatchKeyEvent", dict(base, type="keyUp"))

    def set_select(self, selector, value):
        # A native <select> popup cannot be driven by mouse in headless Chrome, so this sets the
        # value and fires the same change event a person's choice fires.
        return self.c.js("""(function (s, v) {
            const e = document.querySelector(s); if (!e) return false;
            e.value = v; e.dispatchEvent(new Event('change', {bubbles: true})); return e.value === v;
        })(%s, %s)""" % (json.dumps(selector), json.dumps(value)))

    def clear_toast(self):
        self.c.js("(function(){const t=document.getElementById('toast'); t.textContent=''; t.classList.remove('show');})()")

    def toast_has(self, text, timeout=15.0):
        return self.wait("(function(){const t=document.getElementById('toast').textContent; "
                         "return t.includes(%s) ? t : '';})()" % json.dumps(text), timeout)

    def visible(self, selector):
        return self.c.js("""(function (s) {
            const e = document.querySelector(s); if (!e) return false;
            for (let n = e; n && n !== document; n = n.parentNode) {
                if (n.hidden) return false;
                const cs = getComputedStyle(n); if (cs.display === 'none' || cs.visibility === 'hidden') return false;
            }
            const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0;
        })(%s)""" % json.dumps(selector))

    def text(self, selector):
        return self.c.js("(function(){const e=document.querySelector(%s); return e ? e.textContent.trim() : null;})()"
                         % json.dumps(selector))


# ------------------------------------------------------------------ sandbox
def make_sandbox(cdp_port, port):
    box = Path(tempfile.mkdtemp(prefix="ia-fe-"))
    try:
        tracked = subprocess.run(["git", "ls-files"], cwd=str(APP), capture_output=True, text=True,
                                 check=True).stdout.splitlines()
    except Exception:
        tracked = ["interview_assistant.py", "interview_overlay.html", "config.example.json"] + \
                  [str(p.relative_to(APP)) for p in (APP / "demo-vault").rglob("*") if p.is_file()]
    for rel in tracked:
        src = APP / rel
        if src.is_file():
            dst = box / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)          # working tree, so uncommitted changes are what gets tested
    cfg = json.loads((box / "demo-vault" / "config.demo.json").read_text(encoding="utf-8"))
    iv = cfg["interview"]
    iv["port"] = port
    iv["screen_cdp_url"] = "http://127.0.0.1:%d" % cdp_port
    iv["screen_url_hint"] = ["ia-qa-screen"]
    (box / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    (box / "api_keys.json").write_text(json.dumps({"anthropic": FAKE_FILE_CLAUDE,
                                                   "openai": FAKE_FILE_OPENAI}, indent=2), encoding="utf-8")
    (box / "pynput").mkdir(exist_ok=True)
    (box / "pynput" / "__init__.py").write_text('raise ImportError("disabled in the QA sandbox")\n',
                                                encoding="utf-8")
    return box


SCREEN_PAGE = """<!doctype html><title>ia-qa-screen incident review</title>
<h1>Incident review</h1>
<p>Checkout requests have failed with HTTP 502 since the 14:05 deploy. The NGINX error log shows
"upstream prematurely closed connection while reading response header". The app servers restarted
twice in that window.</p>
<iframe style="width:640px;height:360px" srcdoc="<p>Answer both questions.</p>
<label>1. What is the most likely cause of the 502 errors?</label><br>
<textarea rows=4 style='width:560px'></textarea><br>
<label>2. How would you confirm it before rolling back?</label><br>
<textarea rows=4 style='width:560px'></textarea>"></iframe>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--keep", action="store_true", help="Keep the sandbox folder afterwards.")
    ap.add_argument("--skip-answers", action="store_true", help="Skip every check that calls a model.")
    ap.add_argument("--listen", action="store_true", help="Also click Start/Stop listening (records speaker audio for ~3s).")
    args = ap.parse_args()

    browser = find_browser()
    if not browser:
        print("Setup needed: no Chrome or Edge found. Set IA_QA_BROWSER to the browser executable.")
        return 2
    try:
        import websocket  # noqa: F401
    except ImportError:
        print("Setup needed: pip install websocket-client")
        return 2
    if not os.environ.get("INTERVIEW_ASSISTANT_GEMINI_KEY"):
        print("Setup needed: INTERVIEW_ASSISTANT_GEMINI_KEY is not set in this terminal.")
        return 2

    port, cdp_port = free_port(), free_port()
    base = "http://127.0.0.1:%d" % port
    box = make_sandbox(cdp_port, port)
    profile = Path(tempfile.mkdtemp(prefix="ia-fe-chrome-"))
    server = chrome = None
    log_path = box / "server.log"
    print("FRONTEND CHECK -- working tree copied to", box)
    try:
        section("setup")
        t = time.time()
        r = subprocess.run([PY, "-u", "interview_assistant.py", "--build-index"], cwd=str(box),
                           capture_output=True, text=True, timeout=900)
        if not check("demo index builds in the sandbox", r.returncode == 0 and "Index written" in r.stdout,
                     "%.0fs" % (time.time() - t)):
            print(r.stdout[-1500:], r.stderr[-1500:])
            return 1
        env = dict(os.environ, PYTHONIOENCODING="utf-8", INTERVIEW_ASSISTANT_ANTHROPIC_KEY=FAKE_ENV_CLAUDE)
        env.pop("INTERVIEW_ASSISTANT_OPENAI_KEY", None)
        server = subprocess.Popen([PY, "-u", "interview_assistant.py", "--serve", "--port", str(port)],
                                  cwd=str(box), env=env, stdout=open(log_path, "w", encoding="utf-8"),
                                  stderr=subprocess.STDOUT)
        up = False
        for _ in range(120):
            try:
                http_json(base + "/settings", timeout=2)
                up = True
                break
            except Exception:
                time.sleep(0.5)
        if not check("sandbox server starts", up, base):
            return 1
        chrome = subprocess.Popen([browser, "--headless=new", "--remote-debugging-port=%d" % cdp_port,
                                   "--user-data-dir=%s" % profile, "--no-first-run",
                                   "--no-default-browser-check", "--disable-extensions",
                                   "--window-size=1280,900", "about:blank"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        version = None
        for _ in range(60):
            try:
                version = http_json("http://127.0.0.1:%d/json/version" % cdp_port, timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        if not check("headless browser starts", version, (version or {}).get("Browser", "")):
            return 1
        bws = Cdp(version["webSocketDebuggerUrl"])
        tid = bws.call("Target.createTarget", {"url": "about:blank"})["targetId"]
        targets = http_json("http://127.0.0.1:%d/json/list" % cdp_port)
        ws_url = next(x["webSocketDebuggerUrl"] for x in targets if x.get("id") == tid)
        c = Cdp(ws_url)
        p = Page(c)
        for dom in ("Runtime", "Log", "Page", "DOM"):
            c.call(dom + ".enable")

        run_checks(p, c, bws, base, box, cdp_port, args)
        folder_switch_checks(p, c, base)
        if not args.skip_answers:
            cv_only_checks(p, c, box)
        first_run_checks(p, c, box)
        features_off_checks(p, c, box)
        https_and_port_checks(box, port, log_path)
    except Exception as e:
        check("the check itself ran to the end", False, "%s: %s" % (type(e).__name__, e))
    finally:
        for proc in (chrome, server):
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(10)
                except Exception:
                    proc.kill()
        failed = [n for ok, n, _ in RESULTS if not ok]
        if failed and log_path.exists():
            print("\nserver log (last lines):")
            print("\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-25:]))
        shutil.rmtree(profile, ignore_errors=True)
        if args.keep:
            print("\nsandbox kept:", box)
        else:
            shutil.rmtree(box, ignore_errors=True)
    failed = [n for ok, n, _ in RESULTS if not ok]
    print("\nsummary: %d/%d passed" % (len(RESULTS) - len(failed), len(RESULTS)))
    for n in failed:
        print("   FAILED:", n)
    return 1 if failed else 0


def settings(base):
    return http_json(base + "/settings")


def provider(base, pid):
    return next(x for x in http_json(base + "/providers")["providers"] if x["id"] == pid)


def ask_and_wait(p, question, timeout=120):
    """Type a question, press Answer, time the first visible token and the finished turn."""
    n0 = p.c.js("document.querySelectorAll('#paneHistory .hitem').length")
    p.type("#qbox", question)
    t0 = time.time()
    p.click("#askBtn")
    first = p.wait("(function(){const a=document.getElementById('answer');"
                   "return !a.classList.contains('placeholder') && a.innerText.trim().length > 30;})()", 45, 0.05)
    ttft = (time.time() - t0) * 1000 if first else None
    streaming_at_first = p.c.js("document.getElementById('answer').classList.contains('streaming')")
    # Finished = the streaming caret class is gone and Answer is clickable again. The History row is
    # NOT a finish signal: it appears as the answer starts (measured: "done" 1 ms after first token).
    done = p.wait("(function(){const a=document.getElementById('answer'), b=document.getElementById('askBtn');"
                  "return document.querySelectorAll('#paneHistory .hitem').length > %d"
                  " && !a.classList.contains('streaming') && !b.disabled;})()" % n0, timeout, 0.1)
    total = (time.time() - t0) * 1000 if done else None
    badge = p.c.js("(function(){const b=document.querySelector('#answer .badge');"
                   "return b ? b.className + ' | ' + b.textContent.trim() : '';})()") or ""
    text = p.c.js("document.getElementById('answer').innerText") or ""
    if streaming_at_first is False and total is not None:
        badge += " | (whole answer had already arrived when first read)"
    return ttft, total, badge, text


def run_checks(p, c, bws, base, box, cdp_port, args):
    # ---------------------------------------------------------------- load
    section("page load")
    t0 = time.time()
    c.call("Page.navigate", {"url": base + "/"})
    loaded = p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 20, 0.05)
    load_ms = (time.time() - t0) * 1000
    check("page loads and the notes pane gets its state", loaded, "%.0f ms" % load_ms)
    check("load to interactive under 4 s", load_ms < 4000, "%.0f ms" % load_ms)
    html = urllib.request.urlopen(base + "/", timeout=10).read().decode("utf-8")
    body = html[html.index("<body"):]
    bal = {t: body.count("<" + t) - body.count("</%s>" % t) for t in ("div", "aside", "main")}
    check("markup open/close balance is zero for div, aside, main", not any(bal.values()), bal)

    # ---------------------------------------------------------------- settings: notes pane
    section("settings: notes folder")
    p.click("#settingsBtn")
    check("Settings opens", p.wait("document.getElementById('settingsPanel').classList.contains('open')", 3))
    check("indexed folder shows one line plus Refresh (no picker, no Build)",
          p.visible("#vaultCurrent") and not p.visible("#vaultPick") and p.visible("#reindexBtn")
          and not p.visible("#vaultBuild") and not p.visible("#vaultBrowse"),
          "%s | %s" % (p.text("#vaultNowPath"), p.text("#indexMsg")))
    check("exactly one Refresh index button on the page", c.js("document.querySelectorAll('#reindexBtn').length") == 1)
    p.click("#vaultChange")
    check("Change folder opens the picker with Cancel, and no Build or Use-this-folder yet",
          p.wait("!document.getElementById('vaultPick').hidden", 3) and p.visible("#vaultCancel")
          and not p.visible("#vaultBuild") and not p.visible("#vaultSave"),
          c.js("document.getElementById('vaultPath').value"))
    p.type("#vaultPath", "demo-vault/Production")
    check("typing a different folder offers Use this folder",
          p.wait("!document.getElementById('vaultSave').hidden", 3), p.text("#buildMsg"))
    check("the typed folder is inspected (notes counted)",
          p.wait("/\\d+ notes/.test(document.getElementById('vaultInfo').textContent)", 5), p.text("#vaultInfo"))
    p.click("#vaultCancel")
    check("Cancel goes back to the indexed view",
          p.wait("!document.getElementById('vaultCurrent').hidden", 3) and not p.visible("#vaultPick"))
    p.clear_toast()
    p.click("#reindexBtn")
    check("Refresh index runs and reports", p.toast_has("Index updated", 120), p.text("#toast"))
    check("Refresh button comes back ready",
          p.wait("(function(){const b=document.getElementById('reindexBtn');"
                 "return !b.disabled && b.textContent.trim() === 'Refresh index';})()", 10))

    # ---------------------------------------------------------------- settings: toggles
    section("settings: toggles, dropdowns, pause")
    sizes = c.js("[...document.querySelectorAll('#settingsPanel .switch')].map(s => {"
                 "const r = s.getBoundingClientRect(); return Math.round(r.width) + 'x' + Math.round(r.height); })")
    check("every toggle is 40x24 (not stretched)", sizes and all(s == "40x24" for s in sizes), sizes)
    subs = c.js("[...document.querySelectorAll('#settingsPanel .setRow .sub')].map(e => e.textContent.trim().length)")
    check("every Settings description is one short line", subs and max(subs) <= 60,
          "longest %s chars, panel %spx tall" % (max(subs) if subs else "?",
                                                  c.js("document.getElementById('settingsPanel').scrollHeight")))
    check("Settings never scrolls sideways on a desktop",
          c.js("(function(){const p=document.getElementById('settingsPanel');"
               "return p.scrollWidth <= p.clientWidth + 1;})()"),
          c.js("(function(){const p=document.getElementById('settingsPanel');"
               "return p.scrollWidth + ' in ' + p.clientWidth;})()"))
    check("no missing-feature notice when everything is installed",
          not p.visible("#featuresOff") and not http_json(base + "/settings").get("features_off"),
          http_json(base + "/settings").get("features_off"))
    check("no detail text shows until asked",
          c.js("[...document.querySelectorAll('#settingsPanel .more')].every(e => getComputedStyle(e).display === 'none')"))
    scope_before = c.js("document.getElementById('scopeCueToggle').checked")
    p.click('button[aria-controls="more-scopecue"]')
    check("the (i) pins the full detail open",
          p.wait("getComputedStyle(document.getElementById('more-scopecue')).display === 'block'", 2)
          and c.js("document.querySelector('button[aria-controls=\"more-scopecue\"]').getAttribute('aria-expanded')") == "true",
          (p.text("#more-scopecue") or "")[:60])
    check("tapping the (i) does not flip the toggle beside it",
          c.js("document.getElementById('scopeCueToggle').checked") == scope_before)
    p.click("#settingsPanel h2")
    check("a click elsewhere closes the detail",
          p.wait("getComputedStyle(document.getElementById('more-scopecue')).display === 'none'", 2))
    toggles = ["sourcesToggle", "humanizeToggle", "convoToggle", "openerToggle", "scopeCueToggle"]
    before = {t: c.js("document.getElementById('%s').checked" % t) for t in toggles}
    hum0 = settings(base).get("humanize")
    for t in toggles:
        p.click("label.switch:has(#%s)" % t)
    after = {t: c.js("document.getElementById('%s').checked" % t) for t in toggles}
    check("clicking each toggle flips it", all(after[t] != before[t] for t in toggles),
          {t: "%s->%s" % (before[t], after[t]) for t in toggles})
    check("Humanize reaches the server", p.wait("true", 1) and settings(base).get("humanize") == (not hum0))

    for sel, val, key in (("#depthSelect", "balanced", "depth"), ("#modeSelect2", "doer", "mode"),
                          ("#roleSelect", "security", "role"), ("#groundingSelect", "assist", "grounding"),
                          ("#modelSelect", "gemini-3.5-flash", "answer_model")):
        p.set_select(sel, val)
        got = None
        for _ in range(20):
            got = settings(base).get(key)
            if got == val:
                break
            time.sleep(0.15)
        check("%s -> %s saved on the server" % (sel, val), got == val, got)
    check("strip mirrors the Settings dropdowns (Detail, Level, Source, Role, Model)",
          c.js("document.querySelector('#segDetail .segbtn.active').dataset.depth") == "balanced"
          and c.js("document.querySelector('#segRole .segbtn.active').dataset.mode") == "doer"
          and c.js("document.querySelector('#segGrounding .segbtn.active').dataset.grounding") == "assist"
          and c.js("document.getElementById('roleStrip').value") == "security"
          and c.js("document.getElementById('modelStrip').value") == "gemini-3.5-flash")
    p.type("#pauseInput", "2200")
    c.js("document.getElementById('pauseInput').dispatchEvent(new Event('change'))")
    time.sleep(0.6)
    check("Interviewer pause saves", settings(base).get("silence_hangover_ms") == 2200)
    p.type("#pauseInput", "99999")
    c.js("document.getElementById('pauseInput').dispatchEvent(new Event('change'))")
    time.sleep(0.6)
    check("Interviewer pause clamps to 6000",
          settings(base).get("silence_hangover_ms") == 6000 and c.js("document.getElementById('pauseInput').value") == "6000")
    answer_px = "parseFloat(getComputedStyle(document.getElementById('answer')).fontSize)"
    fs0 = c.js(answer_px)
    p.set_select("#textSizeSelect", "1.3")
    fs1 = c.js(answer_px)
    check("Answer text size Extra large scales the answer 1.3x",
          fs0 and fs1 and abs(fs1 / fs0 - 1.3) < 0.02, "%s -> %s px" % (fs0, fs1))
    check("Answer text size stays on this device (not sent to the server)",
          not any("size" in k for k in settings(base)))

    # Reload: what was changed must survive, then put everything back.
    c.call("Page.reload")
    p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 20)
    kept = {t: c.js("document.getElementById('%s').checked" % t) for t in toggles}
    check("toggle states survive a reload", kept == after, kept)
    check("Answer text size survives a reload",
          c.js("document.getElementById('textSizeSelect').value") == "1.3"
          and abs(c.js(answer_px) / fs0 - 1.3) < 0.02, c.js(answer_px))
    p.set_select("#textSizeSelect", "1")
    p.click("#settingsBtn")
    for t in toggles:
        if c.js("document.getElementById('%s').checked" % t) != before[t]:
            p.click("label.switch:has(#%s)" % t)
    for sel, val in (("#depthSelect", "concise"), ("#modeSelect2", "lead"), ("#roleSelect", "general"),
                     ("#groundingSelect", "strict"), ("#modelSelect", "gemini-3.1-flash-lite")):
        p.set_select(sel, val)
    time.sleep(0.8)

    # ---------------------------------------------------------------- settings: provider keys
    section("settings: API keys")
    row_c = '.provRow[data-prov="anthropic"]'
    row_o = '.provRow[data-prov="openai"]'
    check("Claude row says the env var wins and an unused copy is saved",
          "unused copy" in (p.text(row_c + " .provWhere") or ""), p.text(row_c + " .provWhere"))
    p.click(row_c + ' [data-act="toggle"]')
    check("the env-var note shows how to remove the variable",
          "SetEnvironmentVariable" in (c.js("document.querySelector('%s').textContent" % row_c) or ""))
    p.clear_toast()
    p.click(row_c + ' [data-act="clear"]')
    check("Delete saved copy reports that the env key is still in use", p.toast_has("still in use", 10), p.text("#toast"))
    pc = provider(base, "anthropic")
    check("server: saved Claude copy gone, env key still active",
          not pc["saved_copy"] and pc["has_key"] and pc["key_source"] == "env", pc["key_source"])
    check("OpenAI row shows a saved key", "saved on this machine" in (p.text(row_o + " .provWhere") or ""))
    p.click(row_o + ' [data-act="toggle"]')
    p.clear_toast()
    p.click(row_o + ' [data-act="clear"]')
    check("Remove on a saved key says Key removed", p.toast_has("Key removed", 10), p.text("#toast"))
    po = provider(base, "openai")
    check("server: OpenAI key really removed", not po["has_key"] and not po["saved_copy"])
    check("row re-renders as no key", "no key" in (p.text(row_o + " .provWhere") or ""))
    p.click(row_o + ' [data-act="toggle"]')
    p.type(row_o + ' [data-role="key"]', "this is not a key, it is an error message")
    p.clear_toast()
    p.click(row_o + ' [data-act="save"]')
    check("a junk key is rejected, not stored", p.toast_has("rejected", 30) and not provider(base, "openai")["has_key"],
          p.text("#toast"))
    check("the rejected text stays in the box to correct",
          (c.js("document.querySelector('%s [data-role=\"key\"]').value" % row_o) or "").startswith("this is not"))
    p.click("#answer")
    check("clicking away closes Settings", p.wait("!document.getElementById('settingsPanel').classList.contains('open')", 3))

    # ---------------------------------------------------------------- strip
    section("controls strip")
    for selector, key, val, back in (('#segRole .segbtn[data-mode="doer"]', "mode", "doer", '#segRole .segbtn[data-mode="lead"]'),
                                     ('#segDetail .segbtn[data-depth="terse"]', "depth", "terse", '#segDetail .segbtn[data-depth="concise"]'),
                                     ('#segGrounding .segbtn[data-grounding="assist"]', "grounding", "assist", '#segGrounding .segbtn[data-grounding="strict"]')):
        p.click(selector)
        ok = p.wait("document.querySelector(%s).classList.contains('active')" % json.dumps(selector), 3)
        time.sleep(0.5)
        check("strip %s -> %s (active + saved)" % (key, val), ok and settings(base).get(key) == val)
        p.click(back)
        time.sleep(0.5)
    check("strip Source restored to Vault only", settings(base).get("grounding") == "strict")
    p.set_select("#roleStrip", "architect")
    time.sleep(0.6)
    check("strip Role dropdown saves", settings(base).get("role") == "architect")
    p.set_select("#roleStrip", "general")
    p.click("#focusToggle")
    check("Focus toggles on", p.wait("document.getElementById('shell').classList.contains('focus')", 2))
    p.click("#focusToggle")
    check("Focus toggles off", p.wait("!document.getElementById('shell').classList.contains('focus')", 2))
    p.click("#sidebarToggle")
    collapsed = p.wait("document.getElementById('shell').classList.contains('collapsed')", 2)
    p.click("#sidebarToggle")
    check("sidebar hides and comes back", collapsed and p.wait("!document.getElementById('shell').classList.contains('collapsed')", 2))

    # ---------------------------------------------------------------- JD + profile
    section("JD and profile")
    p.click("#tab-jd")
    p.type("#jdText", "Site Reliability Engineer: Linux, NGINX, PostgreSQL and on-call.")
    p.click("#jdSave")
    ok = False
    for _ in range(20):
        if "Site Reliability" in (http_json(base + "/jd").get("jd") or ""):
            ok = True
            break
        time.sleep(0.2)
    check("JD Save persists on the server", ok)
    p.click("#jdClear")
    cleared = False
    for _ in range(20):
        if not (http_json(base + "/jd").get("jd") or "").strip():
            cleared = True
            break
        time.sleep(0.2)
    check("JD Clear empties the box and the server", cleared and c.js("document.getElementById('jdText').value") == "")
    p.click("#tab-profile")
    doc = c.call("DOM.getDocument", {"depth": 1})
    node = c.call("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "#pfFile"})["nodeId"]
    c.call("DOM.setFileInputFiles", {"nodeId": node, "files": [str(box / "demo-vault" / "demo-cv.md")]})
    check("CV import opens the full-size review", p.wait("!document.getElementById('cvModal').hidden", 30))
    check("review shows the converted CV", (c.js("document.getElementById('cvmSource').value.length") or 0) > 200,
          p.text("#cvmMeta"))
    p.click("#cvmViewSource")
    check("Markdown view toggle works", p.wait("!document.getElementById('cvmSource').hidden", 2))
    p.clear_toast()
    p.click("#cvmSave")
    check("Save CV closes the review and says it is in use",
          p.wait("document.getElementById('cvModal').hidden", 10) and p.toast_has("CV saved", 5))
    check("server: a CV is active", bool(http_json(base + "/profiles").get("active_resume")))
    p.click("#pfNewProf")
    p.wait("getComputedStyle(document.getElementById('pfProfEdit')).display !== 'none'", 3)
    p.type("#pfProfName", "QA position")
    p.type("#pfProfPos", "Site Reliability Engineer")
    p.type("#pfProfJd", "Linux, NGINX and PostgreSQL in production.")
    p.clear_toast()
    p.click("#pfSaveUseProf")
    check("Save and use activates the position", p.toast_has("Using", 10), p.text("#toast"))
    check("In use block names it", "Site Reliability" in (p.text("#pfLivePos") or ""), p.text("#pfLivePos"))
    c.js("window.confirm = function () { return true; }")    # a delete confirmation, accepted
    try:
        p.click_text("#pfProfList", "Delete")
        time.sleep(1)
        check("Delete removes the position", not http_json(base + "/profiles").get("profiles"))
    except AssertionError as e:
        check("Delete removes the position", False, e)

    if args.skip_answers:
        return phone_checks(p, c)

    # ---------------------------------------------------------------- answers
    section("answers (these call the model)")
    p.click('#segDetail .segbtn[data-depth="concise"]')
    ttft, total, badge, text = ask_and_wait(p, "How do you troubleshoot a Linux service that will not start?")
    check("typed question answers, grounded badge", ttft and "grounded" in badge, badge)
    # One retry: Gemini alone has stalled a single answer for 5 to 18 s on code that had not changed
    # (1 Oct 2026, twice in four runs). One slow answer is the provider. Two in a row is a regression.
    note = "first %.0f ms, done %.0f ms" % (ttft or 0, total or 0)
    if not (ttft and ttft < 4000):
        ttft_r, total_r, _b, _t = ask_and_wait(p, "How do you check why a systemd service failed?")
        note += " | retry: first %.0f ms, done %.0f ms" % (ttft_r or 0, total_r or 0)
        ttft = ttft_r
    check("first words on screen within 4 s of the click", ttft and ttft < 4000, note)
    check("the answer carries no em or en dash", "\u2014" not in text and "\u2013" not in text)
    body_px = "parseFloat(getComputedStyle(document.getElementById('answerBody')).fontSize)"
    b0 = c.js(body_px)
    p.set_select("#textSizeSelect", "1.15")
    b1 = c.js(body_px)
    p.set_select("#textSizeSelect", "1")
    check("Answer text size Large scales a real answer 1.15x",
          b0 and b1 and abs(b1 / b0 - 1.15) < 0.02, "%s -> %s px" % (b0, b1))
    p.click("#tab-history")
    check("History lists the answer", c.js("document.querySelectorAll('#paneHistory .hitem').length") >= 1)
    check("the header has no copy button (History's Copy A is the route)",
          not c.js("!!document.querySelector('header #copyBtn')"))
    p.clear_toast()
    p.click_text("#paneHistory", "Copy A")
    check("History Copy A reports an outcome", p.wait("document.getElementById('toast').textContent.length > 0", 4), p.text("#toast"))
    p.click("#clearBtn")
    check("Clear answer empties the pane", p.wait("document.getElementById('answer').classList.contains('placeholder')", 3))
    c.js("document.activeElement && document.activeElement.blur()")
    p.clear_toast()
    n_before = c.js("document.querySelectorAll('#paneHistory .hitem').length")
    p.key(" ", "Space", 32, " ")
    check("Space re-asks the last question", p.toast_has("Re-ask", 4), p.text("#toast"))
    # Counted from before the key press: the latency retry above may already have added a row.
    p.wait("document.querySelectorAll('#paneHistory .hitem').length > %d" % n_before, 90, 0.3)
    p.wait("!document.getElementById('answer').classList.contains('streaming')", 90, 0.3)
    ttft2, _t, badge2, _x = ask_and_wait(p, "How does Kubernetes decide where to schedule a pod?")
    check("study-tier question gets the Conceptual badge", "study" in badge2, badge2)
    _a, _b, badge3, text3 = ask_and_wait(p, "What is your experience with Salesforce Apex?")
    check("a topic with no notes gets the honest badge", "honest" in badge3, badge3)
    check("context bar shows after answers", c.js("getComputedStyle(document.getElementById('ctxBar')).display") == "flex")
    p.clear_toast()
    p.click("#newTopicBtn")
    check("New topic clears the context", p.toast_has("New topic", 3)
          and c.js("getComputedStyle(document.getElementById('ctxBar')).display") == "none")
    p.type("#qbox", "Our production website is down after a deploy. How would you troubleshoot it?")
    p.click("#composerFollowup")
    check("Scope it opens with scoping questions",
          p.wait("document.querySelectorAll('#clarifyList li').length >= 2", 30),
          c.js("document.querySelectorAll('#clarifyList li').length"))
    p.type("#clarifyConstraints", "Only the web tier is affected and it started right after the 14:05 deploy.")
    n0 = c.js("document.querySelectorAll('#paneHistory .hitem').length")
    p.click("#clarifyAnswerBtn")
    check("Answer with this closes the panel and answers",
          p.wait("getComputedStyle(document.getElementById('clarifyPanel')).display === 'none'", 3)
          and p.wait("document.querySelectorAll('#paneHistory .hitem').length > %d" % n0, 90, 0.3))
    p.type("#qbox", "Our production website is down after a deploy. How would you troubleshoot it?")
    p.click("#composerFollowup")
    p.wait("getComputedStyle(document.getElementById('clarifyPanel')).display === 'block'", 3)
    p.click("#clarifyClose")
    check("Scope it closes with X", p.wait("getComputedStyle(document.getElementById('clarifyPanel')).display === 'none'", 3))
    p.type("#qbox", "")

    # ---------------------------------------------------------------- screen + boxes
    section("screen and answer boxes (a local test page, questions inside an iframe)")
    shot = bws.call("Target.createTarget", {"url": "data:text/html;charset=utf-8," + urllib.parse.quote(SCREEN_PAGE)})
    time.sleep(1.5)
    bws.call("Target.activateTarget", {"targetId": shot["targetId"]})
    p.clear_toast()
    n0 = c.js("document.querySelectorAll('#paneHistory .hitem').length")
    p.click("#screenBtn")
    read = p.toast_has("ia-qa-screen", 15)
    check("Screen reads the right tab", read, p.text("#toast"))
    # Wait for the stream to FINISH: the History row appears when the answer starts, and run 1 read
    # the text at that moment and failed a screen answer that was in fact correct.
    done = p.wait("(function(){return document.querySelectorAll('#paneHistory .hitem').length > %d"
                  " && !document.getElementById('answer').classList.contains('streaming')"
                  " && !document.getElementById('askBtn').disabled;})()" % n0, 90, 0.2)
    badge = c.js("(function(){const b=document.querySelector('#answer .badge'); return b ? b.textContent.trim() : '';})()")
    answer = (c.js("document.getElementById('answer').innerText") or "").lower()
    terms = [t for t in ("502", "upstream", "nginx", "deploy", "restart") if t in answer]
    check("Screen answer is about the page", done and "screen" in badge.lower() and terms,
          "%s | mentions %s" % (badge, terms))
    p.click("#boxesBtn")
    check("Boxes finds both answer boxes inside the iframe",
          p.wait("document.querySelectorAll('#boxesList .box-row').length === 2", 15),
          c.js("[...document.querySelectorAll('#boxesList .box-q span:not(.box-n)')].map(s => s.textContent.slice(0, 40))"))
    p.click("#boxTypeOff")
    p.click("#boxesList .box-row:nth-child(1) .box-actions button:nth-child(1)")
    check("Answer drafts box 1",
          p.wait("document.querySelector('#boxesList .box-row:nth-child(1) .box-a').value.trim().length > 20", 90, 0.3))
    p.click("#boxesList .box-row:nth-child(1) .box-actions button:nth-child(2)")
    check("Fill writes box 1 and verifies it",
          p.wait("!!document.querySelector('#boxesList .box-row:nth-child(1) .box-status.ok')", 30),
          p.text("#boxesList .box-row:nth-child(1) .box-status"))
    shot_ws = next(x["webSocketDebuggerUrl"] for x in http_json("http://127.0.0.1:%d/json/list" % cdp_port)
                   if x.get("id") == shot["targetId"])
    sc = Cdp(shot_ws)
    in_page = sc.js("document.querySelector('iframe').contentDocument.querySelector('textarea').value") or ""
    sc.close()
    check("the text is really in the page's box", len(in_page.strip()) > 20, "%d chars" % len(in_page))
    p.click("#boxesClose")
    check("Boxes panel closes", p.wait("getComputedStyle(document.getElementById('boxesPanel')).display === 'none'", 3))

    if args.listen:
        section("listening")
        p.clear_toast()
        p.click("#listenBtn")
        on = p.wait("document.getElementById('listenBtn').classList.contains('on')", 10)
        time.sleep(3)
        p.click("#listenBtn")
        off = p.wait("!document.getElementById('listenBtn').classList.contains('on')", 10)
        check("Start and Stop listening", on and off, p.text("#toast"))

    phone_checks(p, c)


def phone_checks(p, c):
    # ---------------------------------------------------------------- console + memory
    section("console and memory")
    errors = [e for e in c.events if e.get("method") == "Runtime.exceptionThrown"
              or (e.get("method") == "Log.entryAdded" and e["params"]["entry"].get("level") == "error"
                  and "favicon" not in e["params"]["entry"].get("url", ""))]
    check("no JavaScript errors during the run", not errors,
          [str(e["params"])[:160] for e in errors[:3]])
    c.call("Performance.enable")
    metrics = {m["name"]: m["value"] for m in c.call("Performance.getMetrics")["metrics"]}
    heap_mb = metrics.get("JSHeapUsedSize", 0) / 1e6
    check("page memory stays small after the whole run", heap_mb < 80,
          "heap %.1f MB, %d DOM nodes" % (heap_mb, metrics.get("Nodes", 0)))

    # ---------------------------------------------------------------- phone width
    section("phone width (375 px)")
    # The screen test brings its own tab to the front, and Chrome does not advance CSS transitions in
    # a background tab: run 3 saw the drawer marked open but frozen at its start position.
    c.call("Page.bringToFront")
    c.call("Emulation.setDeviceMetricsOverride", {"width": 375, "height": 812, "deviceScaleFactor": 2, "mobile": True})
    c.call("Page.reload")
    p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 20)
    check("no horizontal scroll", c.js("document.documentElement.scrollWidth <= 376"),
          c.js("document.documentElement.scrollWidth"))
    outside = c.js("""[...document.querySelectorAll('header button, #ctrlStrip button, #ctrlStrip select, #composer button')]
        .filter(e => e.offsetParent !== null)
        .map(e => [e.id || e.textContent.trim().slice(0, 12), e.getBoundingClientRect()])
        .filter(([n, r]) => r.left < -1 || r.right > 376).map(([n]) => n)""")
    check("every header, strip and composer control is inside the screen", not outside, outside)
    p.click("#settingsBtn")
    p.wait("document.getElementById('settingsPanel').classList.contains('open')", 3)
    pr = c.js("(function(){const r=document.getElementById('settingsPanel').getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)];})()")
    check("Settings fits the phone", pr and pr[0] >= 0 and pr[1] <= 376, pr)
    sizes = c.js("[...document.querySelectorAll('#settingsPanel .switch')].map(s => Math.round(s.getBoundingClientRect().width))")
    check("toggles stay 40 px on the phone", sizes and all(s == 40 for s in sizes), sizes)
    p.click('button[aria-controls="more-grounding"]')
    box_ = p.wait("(function(){const e=document.getElementById('more-grounding'); if (getComputedStyle(e).display !== 'block') return null;"
                  "const r=e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.right)];})()", 2)
    check("an (i) detail fits inside the phone screen", box_ and box_[0] >= 0 and box_[1] <= 376, box_)
    p.click("#settingsPanel h2")
    p.click("#settingsBtn")
    state = "(function(){const r=document.getElementById('sidebar').getBoundingClientRect();"             "return {collapsed: document.getElementById('shell').classList.contains('collapsed'), left: Math.round(r.left), right: Math.round(r.right)};})()"
    start = c.js(state)
    check("on a phone the drawer starts closed", start and start["collapsed"] and start["right"] <= 1, start)
    p.click("#sidebarToggle")
    opened = p.wait("(function(){const s=%s; return !s.collapsed && s.left >= -1 && s.right > 300 ? s : null;})()" % state, 3)
    check("the sidebar button opens the drawer", opened, opened or c.js(state))
    # Tap the backdrop where a person would: in the strip the drawer does not cover. Its centre is
    # under the 330px drawer, and a centre click there would really land on the drawer.
    x, y = 365, 400
    target = c.js("(function(){const e=document.elementFromPoint(%d,%d); return e ? e.id || e.className : '';})()" % (x, y))
    c.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
    for kind in ("mousePressed", "mouseReleased"):
        c.call("Input.dispatchMouseEvent", {"type": kind, "x": x, "y": y, "button": "left", "clickCount": 1})
    closed = p.wait("(function(){const s=%s; return s.collapsed && s.right <= 1 ? s : null;})()" % state, 3)
    check("tapping the backdrop beside the drawer closes it", closed, "tapped %s | %s" % (target, closed or c.js(state)))
    c.call("Emulation.clearDeviceMetricsOverride")


def folder_switch_checks(p, c, base):
    # Last on purpose: building a different folder replaces the index every earlier check answered from.
    section("switching to a new notes folder")
    c.call("Page.reload")
    p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 20)
    p.click("#settingsBtn")
    p.wait("document.getElementById('settingsPanel').classList.contains('open')", 3)
    p.click("#vaultChange")
    p.type("#vaultPath", "demo-vault/Production")
    p.wait("!document.getElementById('vaultSave').hidden", 3)
    p.clear_toast()
    p.click("#vaultSave")
    check("Use this folder saves it", p.toast_has("Folder saved", 10), p.text("#toast"))
    v = http_json(base + "/vault")
    check("a new, unindexed folder offers Build and says answers still use the old index",
          p.wait("!document.getElementById('vaultBuild').hidden", 5) and not p.visible("#vaultCurrent")
          and "previous folder" in (p.text("#buildMsg") or "") and not v["index"]["folder_match"],
          p.text("#buildMsg"))
    p.clear_toast()
    p.click("#vaultBuild")
    check("Build index finishes", p.toast_has("Index ready", 300), p.text("#toast"))
    check("after the build the new folder shows as indexed, with Refresh",
          p.wait("!document.getElementById('vaultCurrent').hidden", 10)
          and p.text("#vaultNowPath") == "demo-vault/Production" and p.visible("#reindexBtn")
          and http_json(base + "/vault")["index"]["folder_match"], p.text("#indexMsg"))


QA_BLOCK_WRAPPER = '''"""QA only: run the app with the packages named in QA_BLOCK made uninstallable."""
import importlib.abc, os, runpy, sys
BLOCK = {b for b in os.environ.get("QA_BLOCK", "").split(",") if b}
class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in BLOCK:
            raise ModuleNotFoundError("blocked for QA: " + name)
        return None
sys.meta_path.insert(0, _Block())
sys.argv = ["interview_assistant.py"] + sys.argv[1:]
runpy.run_path("interview_assistant.py", run_name="__main__")
'''


def features_off_checks(p, c, box):
    # Someone who did not install everything: the console and Settings name what is off and give the
    # one command. Two packages are hidden from a second copy of the app; nothing here is billed.
    section("missing optional packages")
    (box / "qa_block.py").write_text(QA_BLOCK_WRAPPER, encoding="utf-8")
    fport = free_port()
    fbase = "http://127.0.0.1:%d" % fport
    env = dict(os.environ, PYTHONIOENCODING="utf-8", QA_BLOCK="qrcode,docx")
    flog = box / "features-server.log"
    proc = subprocess.Popen([PY, "-u", "qa_block.py", "--serve", "--port", str(fport)], cwd=str(box),
                            env=env, stdout=open(flog, "w", encoding="utf-8"), stderr=subprocess.STDOUT)
    try:
        up = False
        for _ in range(120):
            try:
                http_json(fbase + "/settings", timeout=2)
                up = True
                break
            except Exception:
                time.sleep(0.5)
        check("the app starts with two optional packages missing", up, fbase)
        off = [f["package"] for f in http_json(fbase + "/settings").get("features_off", [])]
        check("server: /settings names exactly the missing packages", sorted(off) == ["python-docx", "qrcode"], off)
        log = flog.read_text(encoding="utf-8", errors="replace")
        check("the console names what is off and the command",
              "2 features are off" in log and "pip install -r requirements.txt" in log,
              next((l.strip() for l in log.splitlines() if "features are off" in l), "")[:100])
        c.call("Page.navigate", {"url": fbase + "/"})
        p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 20)
        if not c.js("document.getElementById('settingsPanel').classList.contains('open')"):
            p.click("#settingsBtn")
        note = p.text("#featuresOff") or ""
        check("Settings shows what is off and how to turn it on",
              p.visible("#featuresOff") and "2 features are off" in note and "CV import from Word" in note
              and "pip install -r requirements.txt" in note, note[:90])
    except Exception as e:
        check("missing-package checks ran to the end", False, "%s: %s" % (type(e).__name__, e))
    finally:
        proc.terminate()


def first_run_checks(p, c, box):
    # A first run with NO Gemini key anywhere: the environment variable removed, and the sandbox's
    # api_keys.json holds only the fake Claude/OpenAI keys. Nothing here is billed: the only API call
    # is the key check for a made-up key, which Google refuses.
    section("first run with no Gemini key")
    kport = free_port()
    kbase = "http://127.0.0.1:%d" % kport
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("INTERVIEW_ASSISTANT_GEMINI_KEY", None)
    klog = box / "nokey-server.log"
    proc = subprocess.Popen([PY, "-u", "interview_assistant.py", "--serve", "--port", str(kport)],
                            cwd=str(box), env=env, stdout=open(klog, "w", encoding="utf-8"),
                            stderr=subprocess.STDOUT)
    try:
        up = False
        for _ in range(120):
            try:
                http_json(kbase + "/settings", timeout=2)
                up = True
                break
            except Exception:
                time.sleep(0.5)
        check("the app starts with no Gemini key", up, kbase)
        log = klog.read_text(encoding="utf-8", errors="replace")
        check("the console says where to add the key, not that something failed",
              "No Gemini key yet" in log and "Warm-up failed" not in log and "Traceback" not in log)
        c.call("Page.navigate", {"url": kbase + "/"})
        check("Settings opens by itself at the Gemini key box", p.wait(
            "document.getElementById('settingsPanel').classList.contains('open')"
            " && !!document.querySelector('#provList .provRow.open[data-prov=\"gemini\"]')", 10))
        check("the Gemini row says it is required",
              "Required" in (p.text('#provList .provRow[data-prov="gemini"]') or ""))
        check("the page says what to do", p.toast_has("Gemini API key", 5), p.text("#toast"))
        check("the Remember box says the key is kept as plain text",
              "plain text" in (p.text('#provList .provRow[data-prov="gemini"] .provActions') or ""))
        p.type('#provList .provRow[data-prov="gemini"] [data-role="key"]', "AIzaSyQA-made-up-key-0000000000000000")
        p.clear_toast()
        p.click('#provList .provRow[data-prov="gemini"] [data-act="save"]')
        check("a made-up key is refused with a reason", p.toast_has("Key rejected", 30), p.text("#toast"))
        g = next((x for x in http_json(kbase + "/providers")["providers"] if x["id"] == "gemini"), {})
        check("server: the refused key was not stored", not g.get("has_key") and not g.get("saved_copy"), g)
    except Exception as e:
        check("first-run checks ran to the end", False, "%s: %s" % (type(e).__name__, e))
    finally:
        proc.terminate()


def cv_only_checks(p, c, box):
    # CV-only mode: a second copy of the app with NO index, sharing the sandbox's profile store, where
    # the earlier checks left the demo CV active. Needs answers, so it is skipped with --skip-answers.
    section("CV-only mode (no notes indexed)")
    cport = free_port()
    cbase = "http://127.0.0.1:%d" % cport
    cfg = json.loads((box / "config.json").read_text(encoding="utf-8"))
    cfg["interview"]["index_path"] = "no-notes-index.json"      # never built, so the index is empty
    cfg["interview"]["port"] = cport
    (box / "config.cvonly.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([PY, "-u", "interview_assistant.py", "--serve", "--port", str(cport),
                             "--config", "config.cvonly.json"], cwd=str(box), env=env,
                            stdout=open(box / "cvonly-server.log", "w", encoding="utf-8"),
                            stderr=subprocess.STDOUT)
    try:
        up = False
        for _ in range(120):
            try:
                http_json(cbase + "/settings", timeout=2)
                up = True
                break
            except Exception:
                time.sleep(0.5)
        check("the app starts with no index", up, cbase)
        prof = http_json(cbase + "/profiles")
        cv = prof.get("active_resume") or next((r.get("id") for r in prof.get("resumes") or []), "")
        if cv and not prof.get("active_resume"):
            post_json(cbase + "/resume", {"action": "activate", "id": cv})
        check("the demo CV from the earlier checks is active", bool(cv), cv)
        post_json(cbase + "/settings", {"grounding": "strict"})
        c.call("Page.navigate", {"url": cbase + "/"})
        p.wait("!!document.getElementById('vaultChecking') && document.getElementById('vaultChecking').hidden", 20)
        p.click("#settingsBtn")
        check("Settings offers the CV route when there are no notes", p.wait(
            "getComputedStyle(document.getElementById('cvOnlyHint')).display !== 'none'", 5),
            (p.text("#cvOnlyHint") or "")[:60])
        p.click("#cvOnlyBtn")
        check("Import a CV opens the Profile tab and closes Settings",
              p.wait("document.getElementById('tab-profile').classList.contains('active')"
                     " && !document.getElementById('settingsPanel').classList.contains('open')", 3))
        p.clear_toast()
        _t, _d, badge, _x = ask_and_wait(p, "Tell me about yourself.")
        check("an identity question is badged From your CV", "From your CV" in badge, badge)
        check("the first CV-only answer says where answers come from",
              p.toast_has("No notes yet", 5), p.text("#toast"))
        _t, _d, badge, text = ask_and_wait(p, "How did you reduce alert noise in Prometheus?")
        check("past work the CV documents is answered from the CV",
              "From your CV" in badge and "symptom" in text.lower(), badge)
        _t, _d, badge, _x = ask_and_wait(p, "Have you worked with Splunk?")
        check("a tool the CV never names is not badged as CV evidence", "honest" in badge, badge)
        post_json(cbase + "/resume", {"action": "activate", "id": ""})
        p.type("#qbox", "How does DNS resolution work?")
        p.click("#askBtn")
        check("with no notes and no CV the answer pane says what to do",
              p.wait("document.getElementById('answer').innerText.indexOf('No notes or CV yet') >= 0", 10),
              (c.js("document.getElementById('answer').innerText") or "")[:80])
        post_json(cbase + "/resume", {"action": "activate", "id": cv})
    except Exception as e:
        check("CV-only checks ran to the end", False, "%s: %s" % (type(e).__name__, e))
    finally:
        proc.terminate()


def _unverified():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def https_and_port_checks(box, plain_port, plain_log):
    section("https redirect and ports")
    # 1. https:// typed for the plain-http run: fail fast, and the console names the right address.
    t = time.time()
    try:
        urllib.request.urlopen("https://127.0.0.1:%d/" % plain_port, timeout=10, context=_unverified())
    except Exception:
        pass
    elapsed = time.time() - t
    time.sleep(0.5)
    check("https:// on the plain-http port fails fast instead of hanging", elapsed < 5, "%.1fs" % elapsed)
    check("...and the console says which address to use",
          ("Use http://localhost:%d/" % plain_port) in plain_log.read_text(encoding="utf-8", errors="replace"))
    try:
        import cryptography  # noqa: F401
    except ImportError:
        check("https checks", True, "skipped: pip install cryptography")
        return
    # 2. An --https run redirects plain http:// on the same port.
    hport = free_port()
    hlog = box / "https-server.log"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([PY, "-u", "interview_assistant.py", "--serve", "--https", "--port", str(hport)],
                            cwd=str(box), env=env, stdout=open(hlog, "w", encoding="utf-8"),
                            stderr=subprocess.STDOUT)
    try:
        up = False
        for _ in range(120):
            try:
                urllib.request.urlopen("https://127.0.0.1:%d/settings" % hport, timeout=3, context=_unverified())
                up = True
                break
            except Exception:
                time.sleep(0.5)
        check("the app starts with --https", up)
        conn = http.client.HTTPConnection("127.0.0.1", hport, timeout=10)
        conn.request("GET", "/?k=abc123")
        r = conn.getresponse()
        loc = r.getheader("Location") or ""
        check("http:// on the https port redirects to https:// (307, token kept)",
              r.status == 307 and loc == "https://127.0.0.1:%d/?k=abc123" % hport, "%s %s" % (r.status, loc))
        conn.close()
        page = urllib.request.urlopen(loc, timeout=10, context=_unverified()).read().decode("utf-8", "replace")
        check("the redirect target loads over https", "<title>" in page)
        second = subprocess.run([PY, "interview_assistant.py", "--serve", "--https", "--port", str(hport)],
                                cwd=str(box), capture_output=True, text=True, timeout=90, env=env)
        out = (second.stdout or "") + (second.stderr or "")
        check("a second copy on the same port stops and says where the first is",
              second.returncode == 2 and "already running" in out and "Traceback" not in out,
              out.strip().splitlines()[-1] if out.strip() else "")
    finally:
        proc.terminate()
    # 3. Another program holds the port: the app moves to the next free one and says so.
    blocker = socket.socket()
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        blocker.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    bport = free_port()
    blocker.bind(("127.0.0.1", bport))
    blocker.listen(1)
    blog = box / "busy-port.log"
    proc = subprocess.Popen([PY, "-u", "interview_assistant.py", "--serve", "--port", str(bport)],
                            cwd=str(box), env=env, stdout=open(blog, "w", encoding="utf-8"),
                            stderr=subprocess.STDOUT)
    try:
        moved = None
        for _ in range(120):
            text = blog.read_text(encoding="utf-8", errors="replace")
            if "this run uses port" in text:
                moved = int(text.split("this run uses port")[1].split(".")[0])
                break
            if proc.poll() is not None:
                break
            time.sleep(0.5)
        answered = False
        if moved:
            for _ in range(60):
                try:
                    http_json("http://127.0.0.1:%d/settings" % moved, timeout=2)
                    answered = True
                    break
                except Exception:
                    time.sleep(0.5)
        check("a port held by another program: the app moves to the next and says so",
              moved and answered, "moved to %s" % moved)
    finally:
        proc.terminate()
        blocker.close()


if __name__ == "__main__":
    sys.exit(main())
