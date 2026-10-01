# Reference notes: read this before you add them to your vault

These notes are **framework and reference material**, not a record of anyone's experience. They
cover the things interviewers probe at lead level: incident command, change management, severity and
escalation, recovery objectives, architecture trade-offs, and how to scope a vague question. Copy the
ones you want into your vault. Keeping that distinction intact is what keeps your answers honest.

## Why the distinction matters

The app speaks in the first person from whatever it finds in your notes. A reference note saying
"immutable backups cannot be altered even by an administrator" is general knowledge, and saying it
in an interview is fine. The risk is the follow-up: "so how did your immutable backup setup work at
your last job?" You need to know instantly whether you are standing on your own experience or on a
reference note.

Three things keep that safe:

1. **The `tier: reference` line in each note's frontmatter.** It tells the app this is reference
   knowledge, so an answer built on it is badged **Reference** and is never framed as hands-on work.
2. **The `REF-` filename prefix.** With **Show sources** turned on, a cited `REF-` note tells you at a
   glance that the answer came from framework knowledge.
3. **The empty "My experience" section** at the bottom of each note. Fill it in yourself, in your own
   words, with things you actually did. That is where real grounding comes from.

> [!IMPORTANT]
> If you have no real experience on a topic, **delete the "My experience" section** rather than
> writing something thin. The app is built to say "I haven't done that" honestly, and that answer
> is survivable in an interview. A made-up one is not.

## The retrieval risk to watch

These notes are dense and well structured, so they score **high** on similarity for scenario
questions. That is the intent, but it also means they can outrank your own experience notes.

After you rebuild the index, watch the **Sources** line on a few answers. If scenario answers start
citing only `REF-` notes and never your own, fill in the "My experience" sections, which pulls your
real material up alongside them. Deleting the reference notes is not the fix.

## Suggested order

1. Read each note once. If anything contradicts how your own environment worked, **your experience
   wins**, so edit the note.
2. Fill in the "My experience" section of the two or three notes closest to the role you are
   interviewing for.
3. Rebuild the index: `python interview_assistant.py --build-index`
4. Ask two or three scenario questions you expect, and check the answers and their sources.

> [!TIP]
> `REF-Scoping-Questions-Bank` is written for **you** more than for retrieval. The **Scope it**
> button uses it (through `interview.scoping_bank_path`) to suggest the clarifying questions to ask
> the interviewer, whether or not it is in your vault. If you do add it to the vault and answers start
> reading as all questions and no substance, take it back out.

## Accuracy

The content follows widely published practice: ITIL 4 practice guidance, Google's SRE incident
management material, and common vendor and practitioner documentation on backup and disaster
recovery. It is standard industry framing, written in our own words. Where your own environment did
things differently, your version is the one to say out loud.
