"""Release check: what a stranger experiences the first time they download this project.

It makes a clean copy of the last commit, which is exactly what someone downloading the repo gets,
with no personal files, index or keys. Then it checks that setup explains itself, the server starts,
the demo notes build into an index, and answers come back with the right label.

Run from anywhere inside the repo:   python qa/release_check.py

Needs git, Python and INTERVIEW_ASSISTANT_GEMINI_KEY. Building the small demo vault costs well under
one cent. It tests the last COMMIT, so commit first. It never touches your own config, notes, index
or saved keys.
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parent.parent   # the repo root, wherever it was cloned
PY = sys.executable
RESULTS = []


def check(name, ok, note=""):
    RESULTS.append((bool(ok), name))
    print("  %-5s %-46s %s" % ("PASS" if ok else "FAIL", name, str(note)[:70]))


def clean_clone():
    """git archive HEAD -> exactly what someone downloading the repo gets."""
    box = Path(tempfile.mkdtemp(prefix="ia-rel-"))
    tar = box / "src.tar"
    subprocess.run(["git", "archive", "-o", str(tar), "HEAD"], cwd=str(APP), check=True)
    shutil.unpack_archive(str(tar), str(box), "tar")
    tar.unlink()
    return box


def get(port, path, timeout=10):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post(port, path, payload, timeout=60):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def serve(box, port):
    p = subprocess.Popen([PY, "-u", "interview_assistant.py", "--serve", "--port", str(port)],
                         cwd=str(box), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/settings", timeout=3).read(10)
            return p
        except Exception:
            if p.poll() is not None:
                return p
            time.sleep(0.5)
    return p


print("RELEASE SMOKE TEST -- clean clone of HEAD")
box = clean_clone()
print("  clone:", box.name)
try:
    # ---------- what actually ships ----------
    shipped = sorted(p.name for p in box.iterdir())
    check("clone contains config.example.json", "config.example.json" in shipped)
    check("clone contains demo-vault/", "demo-vault" in shipped)
    check("NO config.json in the clone", "config.json" not in shipped)
    check("NO api_keys.json in the clone", "api_keys.json" not in shipped)
    check("NO profiles.json / resumes/ in the clone",
          "profiles.json" not in shipped and "resumes" not in shipped)
    check("NO index in the clone", not any(n.startswith("interview_index") for n in shipped))
    check("LICENSE present", "LICENSE" in shipped or "LICENSE.md" in shipped,
          "" if ("LICENSE" in shipped or "LICENSE.md" in shipped) else "no licence file -> not usable as OSS")
    req = (box / "requirements.txt").read_text(encoding="utf-8") if (box / "requirements.txt").exists() else ""
    check("requirements.txt present and covers every optional feature",
          bool(req) and all(pkg.lower() in req.lower() for pkg in
                            ("requests", "numpy", "SoundCard", "websocket-client", "pillow", "pynput",
                             "pypdf", "python-docx", "qrcode", "cryptography", "anthropic")),
          "" if req else "missing")

    # ---------- first run with no config at all ----------
    r = subprocess.run([PY, "interview_assistant.py", "--serve", "--port", "8931"],
                       cwd=str(box), capture_output=True, text=True, timeout=45)
    out = (r.stdout or "") + (r.stderr or "")
    check("no config -> actionable message, no traceback",
          "Setup needed" in out and "Traceback" not in out, out.strip().splitlines()[-1] if out else "")

    # ---------- v3.16: boot with a config but NO index ----------
    shutil.copy(box / "config.example.json", box / "config.json")
    cfg = json.loads((box / "config.json").read_text(encoding="utf-8"))
    cfg["interview"]["vault_path"] = "demo-vault"
    cfg["interview"]["vault_tiers"] = {"_default": "study", "Production": "production",
                                       "Projects": "project", "Study": "study",
                                       "Reference": "reference"}
    cfg["interview"]["vault_exclude"] = ["README.md", "demo-cv.md"]
    cfg["interview"]["index_path"] = "rel-index.json"
    (box / "config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    srv = serve(box, 8932)
    booted = srv.poll() is None
    check("serve() boots with NO index built yet (v3.16)", booted,
          "" if booted else "server exited")

    if booted:
        # /ask must refuse clearly, NOT answer "no experience" from an empty index
        code = None
        try:
            post(8932, "/ask", {"question": "what is OSPF"}, timeout=20)
        except urllib.error.HTTPError as e:
            code = e.code
        check("empty index -> /ask returns 409, not a false refusal", code == 409, f"HTTP {code}")

        v = get(8932, "/vault")
        check("/vault reports the configured folder", bool((v.get("vault") or {}).get("files")),
              str((v.get("vault") or {}).get("files")) + " notes")

        ins = post(8932, "/vault", {"action": "inspect", "path": "demo-vault"})
        check("/vault inspect counts notes + estimates cost",
              ins.get("ok") and (ins.get("vault") or {}).get("files", 0) > 0,
              "%s notes, %s chars" % ((ins.get("vault") or {}).get("files"),
                                      (ins.get("vault") or {}).get("chars")))

        bad = post(8932, "/vault", {"action": "save", "path": "no/such/folder"})
        check("/vault save refuses a folder with no notes", not bad.get("ok"),
              str(bad.get("error", ""))[:60])

        pr = get(8932, "/providers")["providers"]
        check("/providers lists every vendor, no key leaked",
              len(pr) >= 4 and all("api_key" not in p for p in pr),
              ", ".join(p["id"] for p in pr))

        st = get(8932, "/settings")
        cat = st.get("model_catalog") or []
        gem = [m["label"] for m in cat if m["provider"] == "gemini"]
        ant = [m["label"] for m in cat if m["provider"] == "anthropic"]
        check("model groups both run cheapest-first",
              bool(gem) and bool(ant)
              and "cheapest" in gem[0].lower() and "cheapest" in ant[0].lower()
              and "most capable" in gem[-1].lower() and "most capable" in ant[-1].lower(),
              f"{gem[0][:22] if gem else '-'} / {ant[0][:18] if ant else '-'}")
        srv.kill()

    # ---------- build + answer ----------
    t0 = time.perf_counter()
    r = subprocess.run([PY, "-u", "interview_assistant.py", "--build-index"],
                       cwd=str(box), capture_output=True, text=True, timeout=900)
    built = r.returncode == 0 and "Index written" in (r.stdout or "")
    check("--build-index from the clean clone", built, "%.0fs" % (time.perf_counter() - t0))
    check("progress lines carry rate/ETA/cost", "/s, ~" in (r.stdout or ""),
          [l for l in (r.stdout or "").splitlines() if "embedded" in l][:1])

    r = subprocess.run([PY, "interview_assistant.py", "--ask",
                        "How do you troubleshoot a Linux service that will not start?"],
                       cwd=str(box), capture_output=True, text=True, timeout=120)
    o = (r.stdout or "") + (r.stderr or "")
    check("grounded answer with the production tier", "Mode: grounded" in o,
          [l for l in o.splitlines() if l.startswith("Mode:")][:1])

    r = subprocess.run([PY, "interview_assistant.py", "--ask",
                        "How does Kubernetes decide where to schedule a pod?"],
                       cwd=str(box), capture_output=True, text=True, timeout=120)
    o = (r.stdout or "") + (r.stderr or "")
    check("study-tier question is capped at conceptual", "Mode: study" in o,
          [l for l in o.splitlines() if l.startswith("Mode:")][:1])

finally:
    shutil.rmtree(box, ignore_errors=True)

print()
bad = [n for ok, n in RESULTS if not ok]
print("summary: %d/%d passed" % (len(RESULTS) - len(bad), len(RESULTS)))
for n in bad:
    print("   FAILED:", n)
