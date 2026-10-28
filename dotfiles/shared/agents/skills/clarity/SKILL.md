---
name: clarity
description: "Give a non-technical decision maker a clear, committed technical answer: what they can safely change, what it costs, and the one or two risks that matter. Use when a product manager, designer, manager, VP, or other leader asks whether a change is possible, safe, reversible, or quick; when the user asks you to explain a technical tradeoff to leadership; or when you draft a Slack reply, Linear comment, or one-pager that answers a 'can we' or 'should we' question. Based on Sean Goedecke's 'Technical clarity' essay."
---

# Clarity

Turn a hard technical question into an answer a non-technical leader can act on.

Source: <https://www.seangoedecke.com/clarity/>. The essay argues that the main job of a senior technical advisor is to give leaders *technical clarity*: an accurate enough picture of the system that they know what they can safely change. Leaders make many decisions on that picture, so a clear answer has high leverage. A vague or hedged answer pushes the risk back onto the person least able to judge it.

## When to use

- Someone asks "Can we ship X by Friday?", "Is it safe to turn this off?", "Can we roll this out gradually?", or "Can we undo this if it breaks?"
- The user asks you to explain a technical tradeoff to a product, design, or leadership audience.
- You draft a message, ticket comment, or document where the reader decides based on your answer.

## When not to use

- The reader is an engineer who wants the full detail. Give them the detail.
- The question is a code review, a bug hunt, or an implementation task.
- You have not looked at the code and cannot look. Say so. Do not fake clarity.

## Step 1: Find out the real question

Name the decision the reader has to make. "Is the export job idempotent?" usually means "Can we re-run it after a failure without a support incident?" Answer the decision, not the literal words.

If the decision is not clear, ask one question to find it.

## Step 2: Check the code before you answer

Large systems surprise even the people who wrote them. A confident answer from memory is the most common way to give false clarity.

- Read the code paths the change touches.
- Check flags, config, migrations, background jobs, and callers in other services.
- If only a test or a trial run can tell you, say that, and say what the trial is and how long it takes.

Stay close to the code. An advisor who stops reading it loses the ability to give this answer.

## Step 3: Commit to a recommendation

Pick one answer. Lead with it.

- "Yes. We can roll this out to 10% first and turn it off with the existing flag."
- "No. This change cannot be undone after the data migration runs. Do it in two releases instead."
- "Yes, with one condition: we must pause the nightly sync while it deploys."

Do not wait for 100% certainty. You will rarely feel more than about 95% sure, and some background worry is normal. The reader needs your best judgment, not your full doubt.

## Step 4: Choose which risks to mention

A simplified answer is not a dishonest answer. Leave out risks that are both unlikely and small. Mention a risk only if one of these is true:

- It is likely to happen.
- It is severe if it happens: data loss, security exposure, a long outage, money, legal or compliance trouble.
- It changes the decision.

Mention at most two risks. For each one, say what happens and what we do about it. A list of ten caveats tells the reader nothing, and they will ignore all of it.

## Step 5: Write the answer

Use this shape:

1. **Answer** — one sentence: yes, no, or yes-if.
2. **Why** — one or two sentences in the reader's terms: users, time, money, reversibility.
3. **Risk** — zero to two risks that pass Step 4, each with its mitigation.
4. **Confidence** — only if it is low, or if a trial run would change the answer. Say what you would check next.

Avoid jargon. If a technical term is necessary, explain it in a few plain words the first time.

If the answer goes into a message the user sends to other people, apply the `humanizer` skill. Apply `write-as-nate` if it goes out in Nate's name.

## Example

Question from a product manager: "Can we turn on the new pricing page for only enterprise customers next week?"

Bad (hedged, no decision):

> It depends. The pricing page reads from the plans service, and there are some edge cases around legacy plans and the caching layer, and also the feature flag system has had issues with per-account targeting before, so it might be possible but we'd need to investigate further.

Good (committed, one risk):

> Yes. The pricing page already sits behind a feature flag, and that flag can target accounts by plan type. One risk: about 40 enterprise accounts are on legacy plans that the flag does not see. We can add them by hand in about an hour. I checked the flag rules and the page code; I have not tested the legacy accounts yet.
