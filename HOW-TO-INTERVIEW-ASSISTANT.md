# How to use Live Interview Assistant

The [README](README.md) covers what the app is, how to install it and a walkthrough of a first
interview. This guide is the practical companion: how to organise your notes so the answers are
honest, how to set up your CV and the jobs you are applying for, how to get the sound right, how to
tune it, and what to do when something goes wrong.

---

## 1. Organise your notes

### Tell the app how you know each folder

This is the most important setting after the folder itself. Every note gets a **tier** that says how
you know its content, and the tier decides how an answer built on it may speak:

| Tier | Use it for | How answers speak |
|---|---|---|
| `production` | Work you did in a real job | As your experience, with the **Production experience** badge |
| `project` | Labs, side projects, proofs of concept | As your experience, with the **Project experience** badge, and "not in production" when asked |
| `study` | Courses, certifications, books | As knowledge, never as hands-on work, with the **Conceptual** badge |
| `reference` | Framework and reference material | As plain explanation, with the **Reference** badge |

Map your folders in `config.json` under `interview.vault_tiers`:

```json
"vault_tiers": {
  "_default": "study",
  "Work Notes": "production",
  "Labs": "project",
  "Courses": "study",
  "Reference": "reference"
}
```

- Keys are folder names, matched without regard to case, and the **deepest** matching folder wins.
  So `Courses/Kubernetes Lab` can be `project` while the rest of `Courses` stays `study`.
- `_default` applies to every note no folder rule covers. `study` is the safe choice: it can never
  claim experience you do not have.
- A single note can override its folder with a `tier:` line in its frontmatter:

  ```markdown
  ---
  tier: production
  ---
  ```

> [!IMPORTANT]
> Be honest with the map. If course material sits in a folder marked `production`, answers built on
> it will be spoken as your own work. When a folder mixes the two, mark it at the lower tier and
> raise the few notes that really are yours with a `tier:` line.

Before rebuilding, check what each note will get:

```bash
python interview_assistant.py --preview-tiers
```

> [!TIP]
> After editing the map, read the **TIER TOTALS** line in that output. The list of "files that
> changed tier" only notices files that moved to another folder, not files whose folder rule changed.

Changing the map costs nothing to apply: the next `--build-index` updates each note's tier without
embedding anything again. Editing a note's frontmatter re-embeds only the one chunk that holds it.

### Leave things out

List folder or file names under `interview.vault_exclude` to keep them out of the index entirely, for
example a journal, saved interview transcripts, or a folder of templates. Names match any part of a
path, without regard to case. `.obsidian`, `.trash`, `.git` and `templates` are always skipped.

### Optional: the reference notes

The `reference-notes/` folder holds framework notes for lead-level questions: incident command,
change management, severity and escalation, recovery objectives, architecture trade-offs, and a bank
of scoping questions. Read [its guide](reference-notes/README-BEFORE-YOU-ADD-THESE.md) before copying
any of them into your vault. Each already carries `tier: reference`.

---

## 2. Your CV and the jobs you apply for

Everything here lives in the **Profile** tab.

### Import your CV

PDF, Word, Markdown and plain text all work. The converted text opens full size for you to check,
with a toggle between the rendered view and the Markdown. Nothing becomes active until you press
**Save**, because a bad conversion would affect every answer.

- **A PDF with no real text inside** (for example one printed "as an image") is read by Gemini
  instead, for about two cents.
- **A conversion that comes out as one flat block of text** (two-column PDFs often do) can be fixed
  with **Reformat**, which restores headings and bullet points without changing the facts.

> [!NOTE]
> Your CV is not indexed like your notes. The whole CV is sent with every answer, so it can never go
> out of date and switching CVs takes effect at once. It costs about a twentieth of a cent per answer.

### Add the positions you are applying for

A position holds a label, the job title, the company, the job description and which CV to use.
Pressing **Use** switches all of them at once, so a job description from yesterday's interview cannot
quietly steer today's. The top of the pane always shows exactly what the next answer will use.

The job description **steers emphasis only**. It decides which of your real experiences come first
and flags questions outside the role. It never adds a fact that is not in your notes or CV.

> [!TIP]
> You can also paste a job description straight into the **JD** tab. It then overrides the active
> position, and the Profile pane says so in amber until you switch positions again.

---

## 3. Get the sound right (Windows)

Interviewer transcription records whatever is playing on your **default playback device** (WASAPI
loopback), so the one rule that makes it work is:

> **The call app's speaker = your Windows default output = the device the app records.**

Both of these setups work:

- **Speakers.** You hear the interviewer out loud and the app records the same sound. Your microphone
  may pick it up too, but the call app's echo cancellation usually removes that. Keep the volume
  moderate.
- **Earbuds or headphones.** The app still records, because it follows whatever the default device
  is, and nothing leaks back into your microphone. This is the cleanest option, as long as the call
  app really sends the interviewer's voice to the earbuds.

**To set it up:**

1. **Windows:** Settings → System → Sound → Output, and pick the device you listen on.
2. **Zoom:** Settings → Audio → Speaker, and pick the same device or "Same as System".
   **Google Meet:** More options → Settings → Audio → Speakers, and pick the same device.
3. **Press Start listening after** choosing the device. The app takes the default device at the
   moment you start and shows its name. If you change device mid-session, stop and start again.

**If the app hears nothing:** play any sound and confirm it comes out of the default device, then
press Start listening again.

**If one question gets split into two, or lines end too early:** raise **Interviewer pause (ms)** in
Settings. 2000 to 2500 suits someone who pauses to think. The words still appear as they are spoken,
so a longer pause costs you no speed.

**If silence is treated as speech, or quiet speech is missed:** adjust `interview.silence_threshold`
in `config.json`. Raise it if it triggers on silence, lower it if it misses quiet speech. It depends on
your system volume.

> [!NOTE]
> Each transcript line can be edited (to fix a misheard word) and copied, and has its own **Answer
> this** and **Scope it** buttons. The **🎤** button in the header is a different thing: it uses your
> browser's speech recognition for **your own** voice, and does not work in Firefox.

---

## 4. During the interview

### The controls strip

The row under the header holds the settings you might change between questions: **Level** (Lead or
Hands-On), **Detail** (To the point, Concise, Balanced), **Source** (Vault, Vault+AI, AI), **Role**
and **Model**. The README explains each. A fourth detail level, **Deep**, is in Settings only.

### Follow-up questions

The app keeps the last few questions and answers of the conversation, so "walk me through the steps"
is understood as a follow-up to what was just asked. It decides on its own whether a question is a
follow-up or a new topic, and starts fresh on a new topic. A **Context** chip above the question box
shows how many turns it is carrying. Press **New topic** to clear it yourself, or turn the feature off
with **Conversational context** in Settings. Follow-ups change only what a question means, never
where the facts come from.

### History

The **History** tab keeps every question and answer in your browser, with its badge and time. Click
one to open it again, or use **Copy Q** and **Copy A**. It lives only in that browser on that device.

### Asking again

Press **Space** (with nothing selected) to ask the last question again, or double-tap the answer on a
phone. Useful when an answer comes back at the wrong level or length.

### Settings at a glance

| Setting | What it does |
|---|---|
| Show sources | Lists the notes each answer used |
| Answer text size | Makes the answer larger or smaller on this device only |
| Answer model | The model that writes answers (the same list as on the strip) |
| AI providers & API keys | Keys for Gemini (required) and the optional providers |
| Humanize | Slightly more natural spoken phrasing |
| Conversational context | Follow-up awareness (see above) |
| Opener line | A short line to start saying while the answer loads |
| Scope cue | Marks questions worth scoping first with a purple ◆ |
| Detail level, Level, Role, Answer source | The same as the strip, plus Deep |
| Interviewer pause (ms) | How long a silence ends a spoken line |

Hover over or tap the ⓘ next to a setting for the full explanation.

---

## 5. Tune it

| If | Then |
|---|---|
| It says "no direct experience" on something you **have** written about | Check that the note is in the vault and indexed, then lower `min_score` a little (default 0.65) |
| It answers when your notes really do not cover the question | Raise `min_score` toward 0.70 or 0.72 |
| Answers miss detail that sits in a second note | Raise `top_k` (default 6). Balanced and Deep already search more notes |
| Your own note on a topic keeps losing narrowly to a course note | Raise `tier_ceiling_margin` slightly (0.02 worked on a large vault). It only lets a higher-tier note count when its title or headings name what was asked |
| Answers are too long or too short | Change **Detail** on the strip. To the point is a single sentence |
| Answers use exact commands when you wanted the approach | Switch **Level** to Lead |

After changing `config.json`, restart the app.

---

## 6. When something goes wrong

| What you see | What to do |
|---|---|
| "Setup needed: No config file" | `copy config.example.json config.json`, then set `vault_path` |
| "No Gemini API key" | Set `INTERVIEW_ASSISTANT_GEMINI_KEY`, or add the key in Settings → AI providers & API keys |
| "Your Google Cloud project has reached its monthly spending cap" | Raise the cap at <https://ai.studio/spend>, or wait for the new month |
| "Your Anthropic usage limit is used up until ..." | Switch the model to a Gemini one, or raise the limit in the Anthropic console |
| "No notes or CV yet" | Import your CV in the Profile tab, or build the index from Settings → Your notes |
| A model answers with an error about being unavailable | Pick another model. Google has retired whole model families before, and the app falls back to a working default at the next start |
| **Screen** finds nothing, or the wrong tab | Start the browser with `start-interview-chrome.bat` or `start-interview-firefox.bat`, use only one of them at a time, and keep the interview tab in front |
| **Screen** finds no tabs although the browser is open | Another program may already hold port 9223, often a browser started earlier with debugging on. Close it, then start the browser again with the batch file |
| Google refuses to sign you in to Firefox | Run `start-interview-firefox.bat login` once, sign in, close it, then start it normally |
| The first build stopped part way | Run `--build-index` again. It resumes from the last checkpoint |
| Settings says some features are off | `pip install -r requirements.txt`, then restart the app |

---

## 7. Costs and keeping them in check

On the default model, a 45-minute interview with 40 answers and listening on costs about 15 cents. The
one cost that grows while nobody is asking anything is **listening**: audio left playing with
listening on is transcribed continuously, at about 12 cents an hour. The app stops listening on its
own after 90 minutes, or after 10 minutes of silence, and the header shows a live cost meter.

> [!TIP]
> Give this app its own Google Cloud project and set a spending cap on it. Sharing one key between
> several tools makes it impossible to tell which one spent the money, and a cap at the provider is
> the one limit nothing can bypass.

---

## 8. Privacy and honest use

**What leaves your computer:** for each answer, the question, the few matching note chunks, your CV
and the job description go to the answer model you chose. While listening, the interviewer's audio
goes to Gemini. The optional 🎤 for your own voice uses your browser vendor's speech service. Typing
your questions avoids both audio paths.

**Your personal files** are git-ignored, so they never end up in a commit: `config.json`,
`api_keys.json` (if you chose to save a key), `profiles.json`, `resumes/`, `job_description.md`,
`ui_settings.json`, the index files and the generated TLS keys. Check before your first commit
anyway, and replace the key at once if it is ever exposed.

**Honest use.** The app only surfaces your own experience and refuses to invent any, so it keeps you
honest. It is clearly useful for preparation and for recalling your own work on the job. Interviews
differ in what they allow, and where an interview's rules prohibit assistance, the tool does not
exempt you from them. Whether to use it live, and whether to say so, is your decision.
