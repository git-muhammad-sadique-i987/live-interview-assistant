# Frontend check

`frontend_check.py` uses the app the way a person does. It opens the real page in a private,
invisible Chrome, clicks the real buttons, and checks both what the page shows and what the server
saved. Run it after any change to the page or to anything the page talks to:

```
python qa/frontend_check.py
```

It covers Settings (the notes folder, every toggle and dropdown, API keys), the controls strip,
answers and their labels, History, Copy, Clear, Scope it, the JD and Profile tabs, reading a test
page with Screen, drafting and filling answer boxes, a phone-width layout pass, and switching to a new
notes folder. A click fails if the button is hidden or covered, because a person could not click it
either.

It works on a temporary copy of this folder with the demo notes and fake keys, so your own config,
notes, CVs and saved keys are never touched. It needs Chrome or Edge, `pip install websocket-client`,
and `INTERVIEW_ASSISTANT_GEMINI_KEY`, and costs about two cents. It tests your uncommitted changes.
Add `--listen` to also click Start listening (it records about three seconds of whatever your
speakers are playing), or `--skip-answers` to run without calling a model.

# Release check

`release_check.py` does what a stranger does the first time they download this project. It makes a
clean copy of the last commit (no personal files, no index, no keys) and then checks that:

- setup explains itself when something is missing
- the server starts even before any notes are indexed
- the demo notes build into an index
- answers come back with the right label (real experience versus study material)

Run it from anywhere inside the repo:

```
python qa/release_check.py
```

It needs git, Python and the `INTERVIEW_ASSISTANT_GEMINI_KEY` environment variable. It builds the
small demo vault, which costs well under one cent. It tests the last commit rather than uncommitted
changes, so commit first. It never touches your own config, notes, index or saved keys.
