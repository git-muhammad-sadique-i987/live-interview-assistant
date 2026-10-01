# CLAUDE.md: Live Interview Assistant

Context for anyone, human or Claude Code, changing this codebase. Read it before you change
anything. The README covers how to use the app. This file covers how it works and what not to break.

## What this is

A grounded recall aid for technical interviews. It hears or reads the question, retrieves the most
relevant chunks of the candidate's own Markdown notes, and shows a short first-person answer they
can say out loud. It is a memory jog for things the candidate has actually done, not a content
generator. Everything lives in two files: `interview_assistant.py` (index builder, CLI and web
server, standard library HTTP plus SSE) and `interview_overlay.html` (the whole UI).

## The design contract

These rules are what make the tool legitimate. Do not weaken them, in prompts or in code.

- **Answer only from what the candidate wrote.** In the default `strict` mode an answer may use the
  retrieved notes and the active CV, nothing else. No tools, versions, numbers or employers that are
  not there.
- **Never claim experience the evidence does not show.** When nothing relevant is found, the answer
  is an honest "I haven't worked hands-on with that", worded differently every time.
- **Provenance is decided in code, not in prompts.** Each note has a tier (`production`, `project`,
  `study`, `reference`). The tier of the top hit caps how the answer may speak: study and reference
  notes produce a plain explanation and can never be framed as hands-on work. Long prompt rules lose
  to retrieval gravity (a confidently relevant chunk pulls the model along), which is why the hard
  limits are deterministic.
- **Disclose when asked, never volunteer.** Provenance is carried by the badge. The answer says "I
  haven't done this hands-on" only when the interviewer asks directly (`asks_about_experience`), and
  it never names the source ("from my notes", "I studied").
- **The badge must never contradict the answer.** It shows where the answer came from: Production or
  Project experience, Conceptual (study), Reference, From your CV, No direct experience, or an orange
  "AI answer" badge whenever general model knowledge was used.
- **Source settings beyond `strict` are opt-in.** `assist` (Vault+AI) answers from general knowledge
  only when the notes have nothing. `open` (AI) answers everything from general knowledge, preferring
  the notes. Neither may ever claim personal experience, and both render the orange badge.

## How an answer is made

1. **Index.** Every `*.md` under `interview.vault_path` is read (Markdown only, never PDFs or Word
   files), split by headings with the heading trail kept, and embedded with `gemini-embedding-001`
   (768 dimensions). Vectors are cached per chunk by content hash, so `--build-index` only embeds
   what changed, and a long build checkpoints every 250 chunks and resumes after an interruption.
2. **Retrieve.** Cosine similarity over an L2-normalised float32 matrix built once at load
   (`VectorIndex`), top `top_k` (6). A pure-Python fallback works without numpy.
3. **Gate.** The top score picks `grounded` (at or above `min_score`, 0.65), `adjacent` (within
   `adjacent_margin`, 0.08, below it: an honest bridge from the closest real experience) or
   `ungrounded`. `experience_ceiling` then caps the framing at the top hit's tier.
4. **Frame.** `resolve_framing` and `apply_grounding` pick the system prompt. Identity questions
   ("tell me about yourself") go to the CV (`profile`). Screen questions go to `screen`.
5. **Shape.** Detail level (`terse`, `concise`, `balanced`, `deep`), question class (local regex:
   `direct_factual`, `behavioural`, `ambiguous`, `design`, `scenario`), level (`lead` or `doer`), an
   optional role lens (`architect`, `security`, `grc`) and the job description steer length, voice
   and emphasis. None of them may license a fact the evidence does not contain.
6. **Stream.** The answer streams over SSE. `ProseDashFilter` removes em and en dashes as it streams,
   on every provider.

**CV-only mode.** With no index but an active CV, retrieval is skipped and `cv_only_framing` routes
the question: background and the candidate's own past work to the CV, experience probes to the
disclosure rules judged from the CV, everything else to the Source setting unchanged.

## Live interview features

- **Interviewer transcription** (Windows): WASAPI loopback capture via `soundcard`, energy-based
  silence detection, and Gemini transcription. Partial transcripts send only the new audio (a delta),
  a tail flush transcribes the last words as soon as the speaker pauses, and a final pass
  re-transcribes the whole utterance for accuracy. A session cap and an idle cap stop runaway cost.
- **Scope it**: 2 to 3 clarifying questions to ask the interviewer, then **Answer with this**
  re-answers the original question with the replies the candidate typed or captured (**Capture**
  routes the interviewer's next words into that box instead of the transcript).
- **Screen questions**: the page text is read over the browser's debugging protocol (CDP for Chrome,
  WebDriver BiDi for Firefox), across iframes and shadow roots. A screenshot is the fallback.
  **Boxes** drafts an answer per answer field and fills it only after the candidate reviews it.
- **Phone mirror**: `--serve --lan` (token-guarded) and `--https` (for install and wake lock).
  `SessionBus` fans every event out to every connected device.
- **Global hotkeys** (`pynput`): Ctrl+Alt+A answers, Ctrl+Alt+S reads the screen, Ctrl+Alt+D adds a
  screenshot frame.

## Keys and providers

- Gemini is required (embeddings, transcription, default answers). Claude, OpenAI, DeepSeek,
  Moonshot and OpenRouter are optional answer providers.
- A key resolves as: the environment variable `INTERVIEW_ASSISTANT_<PROVIDER>_KEY`, then a key typed
  in Settings for this run, then one saved with "Remember on this machine" (`api_keys.json`, plain
  text, git-ignored, opt-in).
- **The variable names are namespaced on purpose.** Never read `GEMINI_API_KEY`, `OPENAI_API_KEY` or
  `ANTHROPIC_BASE_URL`: another tool on the same machine may own them, and silently spending another
  project's key is the failure this design prevents. `_anthropic_client` passes `base_url` explicitly
  for the same reason.
- A key is verified against the provider's model list before it is stored. The UI never receives a
  key back, only whether one exists and a masked preview.

## Files

| File | Role |
|---|---|
| `interview_assistant.py` | Index, retrieval, prompts, CLI and the local server |
| `interview_overlay.html` | The UI: answer pane, controls strip, sidebar tabs, Settings |
| `config.example.json` | Documented template for `config.json` (git-ignored) |
| `requirements.txt` | Every package any feature uses |
| `demo-vault/` | A fictional engineer's notes across all four tiers, a CV and a demo config |
| `reference-notes/` | Optional framework notes (`tier: reference`) and the scoping question bank |
| `qa/` | `frontend_check.py` (real-browser click test) and `release_check.py` (clean-clone test) |
| `docs/images/` | README screenshots, all from the demo vault |
| `tools/readme_screenshots.py` | Regenerates those screenshots after a visible UI change (about two cents) |
| `start-interview-*.bat` | Launch Chrome or Firefox with the debugging port the screen reader uses |

Personal and generated files, all git-ignored: `config.json`, `api_keys.json`, `ui_settings.json`,
`profiles.json`, `resumes/`, `job_description.md`, the index files and the TLS keys.

## Commands

```
python interview_assistant.py --build-index      # build or refresh the index (embeds only changes)
python interview_assistant.py --rebuild          # full re-embed (only after changing the embed model)
python interview_assistant.py --ask "question"   # one answer in the terminal
python interview_assistant.py --serve            # the UI at http://localhost:8765
python interview_assistant.py --serve --lan --https   # plus the phone mirror
python interview_assistant.py --benchmark        # latency baseline, run after answer-path changes
python interview_assistant.py --preview-tiers    # dry run of tier assignment and exclusions
```

## Testing

- **`qa/frontend_check.py` after any change to the overlay or an endpoint it calls.** It copies the
  working tree into a sandbox, builds the demo index, drives headless Chrome with real mouse clicks,
  and refuses to click anything hidden or covered. About two cents.
- **`qa/release_check.py` before a release.** It clones HEAD and checks that a first-time user gets
  working setup messages, an index and grounded answers.
- **QA must never change real state.** Anything that writes (settings, profiles, keys) runs against a
  sandbox copy. One early fuzz run wrote junk profiles into the live store.
- **Measure, do not assume.** When a benchmark reads slow after a change, run the old and new code
  back to back before blaming the change: Gemini latency varies on its own, and more than once a
  "regression" was the provider.

## Conventions and gotchas

- **Keep it two files.** No cross-script imports, no framework.
- **One warm HTTP session** (`shared_session()`). A session per call paid a full TLS handshake every
  time. `serve()` warms the connection at startup and a keepalive holds it during listening.
- **The index is two files**, metadata JSON plus a `.npy` vector sidecar, written together via
  temp file and `os.replace`. Serving never materialises the vectors as Python lists.
- **`chunk_id` excludes the tier**, so changing a tier (folder map or file move) is a metadata refresh,
  not a re-embed. A cache hit refreshes `path` and `tier` from the fresh chunk.
- **Everything that produces an answer goes through `generate_answer` or `generate_answer_stream`.**
  Calling `_answer_raw` or `_answer_stream_raw` directly skips the dash clean-up.
- **Publish every client action to the `SessionBus`**, or the laptop and the phone drift apart.
  SSE liveness is a real `ping` event plus a client watchdog, not an SSE comment.
- **`ui_settings.json` is written via temp file and `os.replace` under a lock.** A plain write let a
  concurrent read see an empty file and reset every setting.
- **The controls strip mirrors the Settings selects.** A strip control sets its select and dispatches
  `change`, and never posts on its own. On a phone the strip and the composer wrap, never scroll.
- **Gemini thinking tokens count against `maxOutputTokens`.** `_thinking_and_output` decides per model
  and both request paths retry once without `thinkingConfig` on a thinking-related 400.
- **Pick models by price and measured latency, not recency.** Retired models can still be listed by
  `ListModels`, and only a real call reveals a 404. `effective_answer_model` scrubs retired or keyless
  choices back to a working default.
- **A spending cap is not a rate limit.** Both arrive as errors, and `_api_error` and `_anthropic_error`
  name the cap and what to do instead of "wait a moment".
- **On Windows, `SO_EXCLUSIVEADDRUSE`.** `http.server` sets `SO_REUSEADDR`, which on Windows lets two
  servers share a port. `choose_port()` stops if this app already runs there and moves on if another
  program holds it.
- **`--https` peeks the first byte per connection.** A TLS hello is wrapped on its own thread, plain
  http gets a 307 (never 301) to https, so one stalled handshake cannot block every request.
- **A page shell is not a successful screen read.** Below `screen_min_chars` (80) the read fails so the
  screenshot fallback runs. Frames and shadow roots are walked because `innerText` crosses neither.
- **Filling a React input needs the native value setter and an `input` event** (or CDP
  `Input.insertText`). `el.value = text` looks filled and submits empty. Every fill is read back.
- **Never patch a platform's automation signals.** Firefox sets `navigator.webdriver` whenever its
  remote agent is on, so `start-interview-firefox.bat login` exists to sign in without it.
- **Optional packages degrade with a message.** `features_off()` checks them without importing, and
  the console and Settings name what is off and the `pip install -r requirements.txt` that fixes it.
- **Count `div`, `aside` and `main` tags after any markup change.** Browsers silently repair bad
  nesting, so a stray closing tag breaks the layout with no console error.
- **Public docs**: measured, human tone, and no em dashes, en dashes or semicolons in prose.
