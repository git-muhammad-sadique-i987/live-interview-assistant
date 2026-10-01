# How to use Live Interview Assistant

A grounded, self-hosted recall aid over **your own** Obsidian vault + resume. It listens to a
question (spoken or typed), finds the relevant material **from your notes**, and shows a tight
**first-person** answer you can narrate — with the source note named.

**The one rule that makes this legitimate:** it answers *only* from your notes/resume. When nothing
relevant is found, it gives an honest, professional *"I don't have direct hands-on experience with X"*
instead of inventing anything. It is a memory jog for things you have actually done — not a fabrication
engine.

Files:
- [interview_assistant.py](interview_assistant.py) — index builder, CLI, and the local web server.
- [interview_overlay.html](interview_overlay.html) — the live voice overlay page.

---

## 1. One-time setup

### a. Dependencies
One command installs everything every feature uses:
```
pip install -r requirements.txt
```
Only `requests` is strictly required. If anything else is missing, the app still starts, and the
console and the top of **Settings** name the features that are off and give the command above.
`webrtcvad` is not in the file: it is optional and unused by default (the built-in energy-based
silence detection is the default).

### b. Give the app your Gemini key
There are two ways, and you only need one.

**An environment variable (recommended).** Nothing is written to disk. Set it once:
```
setx INTERVIEW_ASSISTANT_GEMINI_KEY "your-key-here"
```
then open a **new** terminal (`setx` only affects shells started after it).

**In the app.** Start it and open **Settings → AI providers & API keys**. On a first run with no key
the app opens that box for you. The key is checked before it is kept. Left as is, it lasts until the
app stops. Tick **Remember on this machine** to keep it in `api_keys.json`.

> [!WARNING]
> `api_keys.json` holds the key as **plain text**. It is git-ignored, but anyone who can read files
> on your computer can read it. The environment variable is the safer choice, and it wins when both
> are set.

A leftover `gemini.api_key` in `config.json` is ignored with a warning.

Use a Google Cloud project of its **own** for this key, so this app's spend is visible and capped
independently of anything else you run.

### c. Point it at your vault
Your vault is the folder that holds your notes: an Obsidian vault or any other folder of notes.

> [!IMPORTANT]
> Only Markdown files (`.md`) are read. PDFs, Word documents and other files in the folder are
> skipped, so convert anything you want the app to know into Markdown first.

Copy the documented template and edit one line:
```
copy config.example.json config.json
```
```json
"interview": {
  "vault_path": "C:/Users/you/Documents/ObsidianVault",
  "embed_model": "gemini-embedding-001",
  "embed_dim": 768,
  "answer_provider": "gemini",
  "answer_model": "gemini-3.1-flash-lite",
  "top_k": 6,
  "min_score": 0.65,
  "adjacent_margin": 0.08,
  "jd_path": "job_description.md",
  "stt_model": "gemini-3.1-flash-lite",
  "stt_sample_rate": 16000,
  "silence_threshold": 0.012,
  "silence_hangover_ms": 1500,
  "port": 8765
}
```
`vault_path` is the only value you must set; every other key has a working default and is documented
inline in [config.example.json](config.example.json). Optional ones worth knowing: `adjacent_margin`
(how far below `min_score` still gets a brief honest bridging answer instead of a flat refusal),
`jd_path` (where the saved job description lives), and the `stt_*` / `silence_*` keys for interviewer
transcription. `silence_threshold` is an RMS level that may need per-machine tuning depending on your
system volume.
- `vault_path` — your Obsidian vault folder (all `*.md` inside are indexed recursively; `.obsidian/`,
  `.trash/`, and `templates/` are skipped).
- `answer_model` / `stt_model` — **do not use the `gemini-2.5-*` family.** Google retired it for
  projects created after mid-2026, and a retired model 404s every answer. `gemini-3.1-flash-lite` is
  both the cheapest and the fastest tier measured; escalate to `gemini-3.5-flash` for a hard
  question, not to a pro tier (pro costs ~5s to first token for no measured quality gain here).
- `answer_provider` — **`gemini` is the default and the recommendation.** It reuses the one Gemini
  key, needs no other account, and costs roughly **$0.001 per answer**. The alternative is
  `openrouter` (uses the OpenRouter key/model) — capable but far pricier, and the thing that "burned $5
  in seconds" before, so it stays off by default.
  > Note: **Claude Pro is not the Claude API.** A Pro subscription does not grant API access; the
  > Anthropic API is separate pay-as-you-go credits. Sonnet via API is ~10× the cost of Gemini Flash for
  > this task, which is why Gemini is the default.
- `min_score` — the grounding threshold (cosine similarity). Below it, the assistant gives the honest
  "no experience" answer. Raise it to be stricter, lower it if it declines on topics you *have* noted.

### Spend control
There is no in-app budget anymore — no ledger, no pill, no hard-stop. Cap spend where it actually lives:
set a **quota / budget alert on your key in Google Cloud**. Answers are ~$0.001 each, but an hour of leaving listening on is ~$0.23 - transcription, not answering, is the line item that matters. A small monthly
cap there is plenty of headroom. (The `openrouter` provider stays off by default for the same
runaway-cost reason it always has — see below.)

### d. Add your CV — in the app, not in config.json
Open the **Profile** tab and import it. PDF, Word, Markdown and plain text all work; a PDF whose text
was flattened to outlines (printed "as image") is read by sight instead, since there is no text layer
to extract. The conversion is shown to you full-size for review and only becomes active when you save
it — a bad conversion that reached the answer path would poison every answer.

**The CV is injected verbatim into every answer, not indexed.** That is deliberate: there is no second
copy to go stale, switching CVs is instant, and "tell me about yourself" always has it. It costs about
$0.0005 per answer.

The same pane manages **positions** — each one pairing a job description with a CV, so activating a
position switches both at once and a JD from a previous interview cannot silently steer this one. The
top of the pane always states what the next answer will actually use.

`interview.resume_path` in `config.json` is unused for answering; import the CV instead.

Both embeddings **and** answers use the single **Gemini** key, so no other account is needed. (OpenRouter is only involved if you deliberately switch `answer_provider` to
`openrouter`.)

---

## 2. Build the index
```
python interview_assistant.py --build-index
```
This embeds every chunk of your vault and writes `interview_index.json` plus its `.vectors.npy` sidecar next to the script. Your CV is NOT indexed - it is injected verbatim at answer time.
Re-run it after you add/edit notes — it only re-embeds what changed. Use `--rebuild` to force a full
re-embed (e.g. after changing `embed_model` or `embed_dim`).

---

## 3. Try it in the terminal (prep / sanity check)
```
python interview_assistant.py --ask "How do you troubleshoot OSPF neighbors stuck in EXSTART?"
```
You'll see whether it was **Grounded** (with the match score and sources) and the first-person answer.
Ask about something you *haven't* documented to confirm it declines honestly.

---

## 4. Run the live voice overlay
```
python interview_assistant.py --serve
```
Then open **http://localhost:8765** in Firefox, Edge, or Chrome:
1. Type a question in the box (always works) and press Enter — the answer streams in, rendered as
   **Markdown**.
2. Optionally click **Start listening** for your *own* voice via the browser mic
   (`webkitSpeechRecognition`). This is an optional extra; where the browser doesn't support it (e.g.
   Firefox) you get a helpful message rather than a dead end, and the typed box still works.
3. Press **Space** (when not typing in the box) to re-ask the last heard sentence.

Each answer is tagged with its **mode** badge:
- **Grounded** — top match ≥ `min_score`; answered from your notes, with the source note named.
- **Adjacent** — the closest match sits within `adjacent_margin` below `min_score`; you get a brief,
  honest *bridging* answer from your nearest real experience (sources still shown) instead of a flat
  refusal.
- **No match / ungrounded** — nothing close enough; the honest "no direct hands-on experience" response.
  Its wording is varied every time so it never sounds canned.

### The Job description panel
Open the collapsible **Job description** panel and paste the JD you're interviewing for. It's saved to
`job_description.md` (git-ignored) and applied automatically to every answer. It is **focus-steering
only**: it shapes *which* of your real, note-backed experiences get emphasized and flags out-of-scope
questions — it never licenses inventing anything. The grounding rule above is unchanged.

### Interviewer transcription (Windows)
The overlay can transcribe the **interviewer's** voice, not just yours:
1. With `soundcard` installed (Windows / WASAPI **loopback**), click **Start listening** for the
   transcript.
2. The server captures whatever plays through your speakers — the interviewer on the call (or your own
   TTS while testing) — splits it on silence, and transcribes each utterance by sending the audio to the
   same **Gemini** key (`gemini-3.1-flash-lite` transcribes audio natively; set via `interview.stt_model`).
3. Lines appear in the left **Interviewer transcript** sidebar. Each is **editable** (fix a misheard
   word), **copyable**, and has an **Answer this** button that runs it through the normal grounded
   pipeline.

This path is fully decoupled from typing — the typed box always works even if listening is off or
unsupported. If `soundcard`/loopback isn't available, listening just reports an error and the server
keeps running. A quick way to test it without a real call is to play your own text-to-speech and watch it
transcribe.

### Sound setup — so BOTH you and the app hear the interviewer
The capture is a Windows **WASAPI loopback**, which records whatever is playing on your **current
default playback device**. The single rule that makes everything work:

> **Meet/Zoom "Speaker" = your Windows default output device = the device the app loops back.**

So the interviewer's audio must play through your Windows *default* output, and the app captures that
same device. Two setups both work:

- **Speakers (what you use):** Set Windows default output to your speakers. You hear the interviewer out
  loud and the app's loopback captures the same audio. *Trade-off:* your microphone can pick up the
  speaker sound, so the interviewer may hear a faint echo of themselves — the call app's echo
  cancellation usually removes it; keep the volume moderate to be safe.
- **Earbuds / headphones (no echo):** The app **still** captures, because loopback follows whatever the
  default device is — including earbuds. Nothing leaks back into your mic, so there's no echo. This is
  the cleanest option *as long as the call app actually routes the interviewer's voice to the earbuds*
  (some headsets/apps route call audio oddly — if the transcript goes quiet after plugging in earbuds,
  it's a routing problem, not the app).

**Set it up (Windows 10/11):**
1. **Windows:** Settings → System → Sound → **Output** → pick the device you're listening on (speakers
   or earbuds). Or click the volume icon in the tray and choose the output there.
2. **Zoom:** Settings → Audio → **Speaker** → set to the same device, or **"Same as System."**
   **Google Meet:** ⋮ → Settings → Audio → **Speakers** → pick the same device.
3. **Click Start listening AFTER** you've selected/switched the output device — the app grabs the current
   default device at the moment you start, and its name shows in the button tooltip/toast so you can
   confirm it grabbed the right one. If you change devices mid-session, click Stop then Start again.

**If the app hears nothing:** (a) play any sound and confirm it comes out of the *default* device;
(b) re-click Start listening after switching devices; (c) if quiet speech is missed or silence is
treated as speech, tune the **Interviewer pause (ms)** in Settings and `interview.silence_threshold`
in `config.json` (raise the threshold if it triggers on silence, lower it if it misses quiet speech —
it's relative to your system volume).

### Follow-up questions (conversational context)
The overlay is **stateful within a session**, so a bare follow-up like *"walk me through the
implementation steps"* is understood in the context of what was just asked instead of being treated as a
brand-new question. It sends the last few Q&A turns with each question; the server rewrites the follow-up
into a standalone search query (shown under the answer as *"↳ read as follow-up: …"*) so retrieval stays
on topic, then answers with the conversation in mind. A **🔗 Context: N turns** chip appears above the
composer; click **New topic** to clear it when a genuinely new subject starts, or turn the whole thing off
with **Conversational context** in Settings. It's grounding-safe — continuity only; new facts still come
from your notes.

### Conversation history
A right-hand **History** panel keeps your past Q&A in the browser (`localStorage`): question, mode badge,
timestamp, and sources, with per-item copy, click to reopen, and clear-all.

---

## Two honest notes (please read)

- **Privacy of audio.** Two paths send audio off your machine. The optional browser mic
  (`webkitSpeechRecognition`, your own voice) sends microphone audio to the browser vendor's cloud in
  Chrome/Edge. The interviewer-transcription path sends the captured speaker audio to **Gemini** (the
  same key) for transcription. If either matters to you, use the typed box — it's fully offline-friendly
  and always works; the `/ask` endpoint is engine-agnostic, so a local STT (e.g. Whisper) could replace
  the cloud paths later.
- **Live use in interviews is your call.** This tool is unambiguously useful for **preparation** and for
  **on-the-job / client recall**. Using it live during a synchronous interview is a judgment call — some
  interviewers would object to undisclosed real-time assistance. Because it only surfaces *your own*
  documented experience and refuses to invent anything, it keeps you honest either way, but the decision
  to use it live (and whether to disclose) is yours.

---

## Tuning
- Answers feel off-topic or it declines too often → your notes may not cover it (good!), or lower
  `min_score` / raise `top_k`.
- It answers when it shouldn't → raise `min_score` (e.g. 0.70–0.72).
- Answers too long/short → adjust the `max_tokens` default in the generation functions (`gemini_chat` /
  `gemini_chat_stream`), or the length guidance in `SYSTEM_GROUNDED` inside
  [interview_assistant.py](interview_assistant.py).

## Security / secrets reminder
With the key in the `INTERVIEW_ASSISTANT_GEMINI_KEY` environment variable, no file in this folder
holds a credential. If you ticked **Remember on this machine**, `api_keys.json` does, as plain text.
What else is personal: `profiles.json` and `resumes/` (your CVs),
`job_description.md`, `interview_index.json` (chunks of your notes verbatim), and the generated
`ia-*.key` TLS material. The included [.gitignore](.gitignore) already excludes all of these — but
double-check before your first commit, and rotate the key if it ever gets pushed.

**One app, one key, one project.** Sharing a key across projects makes spend impossible to attribute:
a month of this app's cost here turned out to belong mostly to an unrelated pipeline on the same key.
Give this app its own Google Cloud project and cap it there.
