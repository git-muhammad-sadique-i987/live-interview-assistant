# Demo vault - a fictional engineer's notes

This exists so you can run Live Interview Assistant **before** you have pointed it at your own notes.
Every note here is written for the demo. **Sam Rivera is not a real person**, the employers are
invented, and nothing here is drawn from anyone's course material or private notes.

## Why the folders are split this way

The folder names map to **provenance tiers** - how the (fictional) author actually knows the
content - and the mapping lives in `config.demo.json`:

| Folder | Tier | What it represents |
|---|---|---|
| `Production/` | `production` | Systems operated for real, under load, on call |
| `Projects/` | `project` | Labs, POCs, internal projects |
| `Study/` | `study` | Course notes - understood, never operated |
| `Reference/` | `reference` | Framework material, not personal history |

This is the mechanism worth seeing. The tier of the top-scoring chunk is a **hard ceiling in code**,
not a hint in a prompt: a hit in `Study/` produces a clean conceptual explanation and cannot be
narrated as hands-on experience however well it matches.

## Try these five questions

Run `--serve` (or `--ask`) and compare what comes back. The badge above each answer tells you which
kind of answer you are looking at.

| Ask | Badge | What to notice |
|---|---|---|
| *How do you troubleshoot a Linux service that will not start?* | **Production experience** | Lived detail and a specific incident, with the source note named |
| *How does Kubernetes decide where to schedule a pod?* | **Conceptual (study)** | Correct and confident, with no claim of having run it - and no "from my studies" either |
| *Do you have hands-on experience with Kubernetes in production?* | **Conceptual (study)** | *"I have not run Kubernetes in production"* comes first, then briefly what he does know. The disclosure appears because you asked directly, not as a running apology on every answer |
| *What is your experience with Salesforce Apex?* | **No experience** | Nothing is close enough, so it declines. It may still name what Apex *is* - category knowledge is allowed; claiming to have used it is not |
| *Do you have hands-on experience running PostgreSQL replication?* | **Production experience** | The same probe against something he really did: a plain yes, then the substance |

Questions three and four are the ones to sit with. Most tools answer all five the same way.

## Using it

```
copy demo-vault\config.demo.json config.json
python interview_assistant.py --build-index
python interview_assistant.py --ask "How do you troubleshoot a Linux service that will not start?"
```

The index is small - a few dozen chunks, a few seconds, well under a cent to embed.

To see the CV path as well, start the server and import `demo-vault/demo-cv.md` from the **Profile**
tab, then ask *"tell me about yourself"*.

## Two settings tuned for the demo, which you should not copy

`config.demo.json` differs from the shipped default in three places:

- **`vault_exclude` names two files.** `demo-cv.md` must never be indexed - a CV is injected verbatim
  at answer time, so an indexed second copy goes stale silently, which is a real bug this project
  once shipped. `README.md` is the vault's documentation, not anyone's experience, and it was
  outranking real notes before it was excluded.
- **`index_path` is `demo-index.json`.** This one you can safely keep the spirit of: it means trying the demo on an install that already has a real index cannot overwrite it. The per-chunk vector cache lives inside the index file, so losing it costs a full re-embed.
- **`adjacent_margin` is 0.03, not the default 0.08.** With ~100 chunks every unrelated question still
  scores around 0.60, so the default band swallowed them all and a genuine no-experience answer was
  unreachable. On a real vault, use 0.08.

## When you switch to your own notes

Change `vault_path`, and rewrite `vault_tiers` to name **your** folders. Tiering is the part that
needs your judgement: a folder you label `production` licenses the assistant to speak about it as
lived experience, so label conservatively. Anything unmapped falls to `_default`, which is `study` -
the safe direction to be wrong in.
