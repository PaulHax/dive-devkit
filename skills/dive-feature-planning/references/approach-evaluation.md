# Approach evaluation

## Force the persist question for any derived artifact

> "Anything inferable is re-inferable, so there is no decision worth storing… a derived copy would only create a second thing that can disagree with the source."

This one question killed cut 1. Ask it of every piece of state a design proposes to write down.

## Price approaches with cheap throwaway strawmen

The metadata-as-annotations prototype was 2 files with zero core changes, 'built to surface the
special-case cost so the data-model fork can be weighed'. It was never meant to ship.

Compare options in **one table**, name the decision axes explicitly, and name the decision **owner**
per open question. A late-surfacing axis is what killed cut 1: 'This axis was not considered before;
it materially affects the other two'.

> "Two axes, not one"

## Verify "current behavior" against `main`, not the draft

A design that extends existing behavior has to establish that the behavior exists. A per-run
attachment picker was proposed as a generalization of something `main` never did:

> "is this a feature of the code on main? ... i wnat to keep things simple"

The honest answer, once checked: 'No. I introduced an unnecessary capability in the draft.'

## Let the consumer infer the role; don't tag it at write time

Two branches each gave the same attachment a purpose, and the draft persisted
`frameMetadata` / `pipelineInput` tags to tell them apart. The tags stored a decision the reader can
make for itself:

> "why do we need to tag them 'frameMetadata, pipelineInput' can we not jsut infer at pileine or frame metadata loading time?"

The same question as the persist question above, one level down: not "must we store this value" but
"must we store this *classification*".

## Root-cause over point-patches

When findings pile up, propose the design change that retires the whole failure class, not N fixes.
Content-sniffing → declared-by-name made the failure class 'unanswerable-wrong' instead of producing
a list of patches.

## Pause and re-evaluate a branch that has grown large

A rewrite plan is an acceptable outcome. Core-code refactors outside nominal scope are on the table
if they simplify ingestion.

> "given its goals… can you evalute its approach. perhaps their is a simipler way"
> "if small changes to dive code outside of the PR will simplify ingestion… we shoudl consiter it"

## PR-splitting criteria that were actually used

| Criterion | What it looked like |
|---|---|
| (a) main-line bugs found en route | standalone PRs — bidi fix, `event.py` regex |
| (b) a refactor the feature depends on for its only user-feedback surface | **prerequisite** PR — "closes the one silent-loss path… that nothing downstream can detect" |
| (c) the feature itself | ONE branch of bottom-up, green, topical commits — "no need to stack the PR B, C or D. jsut make the commits layer them up" |
| (d) refactor PRs must be feature-agnostic | "coudl PR B be done wihtout intoruding frame-metadata conecpet at atll?" — a 15-line feature predicate leaking in is a scope smell |
| (e) follow-ups | scoped minimal and forward-compatible — "let's look for something minimal follow-up that we can get in soon" |

Layering is for reviewability, not for separate PRs.

## Rebuild a long branch's stack from its final tree, not its chronology

68 commits contained several designs that were added and later removed — post-creation import,
`mediaFiles` associations, multi-source column merging, timestamp alignment. Replaying that history
as review layers shows reviewers work that no longer exists. Reconstruct each layer from the final
tree instead.

## Ship the whole media contract in the first layer

Do not stage image sequences first and bolt video on at the end because an existing commit happens to
be clean there. That optimizes for commit reuse, not for review.

> "why video at the end? does it not make senes to include video from the beining?"

Scan the proposed stack for any layer that introduces a restriction a later layer removes — those two
layers are one layer.

## Audit "standalone" before writing it down

A prerequisite branch labelled independently-mergeable was in fact required by the rest of the stack:
without it the attachment could be silently dropped before ingestion. The label survived until the
user asked directly.

> "does the feature stack not depend on upalt p[ackage ahotrity chagnes?"

Criterion (d) has a second half: a feature-agnostic branch must carry no feature vocabulary **and**
its independence claim must be traced, not assumed.

## Every not-now item gets three checks

1. The current interface/storage shape survives the extension **additively** — same locations, no
   migration.
2. An escape hatch is named for the deferred case (e.g. 'advanced users run a one-line API call'
   was accepted as the v1 answer).
3. The deferral and its rationale are written down so it reads as a signed decision, not an
   oversight.

> "would this leave the path forward for a better full ipmmentation?"
> "We don't want to support videos yet, but I'm just saying for future proofing... Does this change any other thing about this design?"

## PR topology is user-owned and changes late

Report any topology change — and any demoted recommendation — as an explicit delta. Silent drift
gets caught and costs trust:

> "what happend to the refacto of core code that simplifid our work?"
> "why did we demote the web uplaod refactor demoted?"

Planned prerequisite PR B shipped inside the feature PR without announcement. Separately, the PR
count stayed the user's call throughout: "we are not doing the other 2 prs, we will jsut open pr for
… sidecars".

And: never open the PR yourself.

> "but don't oepn a pr jsut update markdown"

---

Related: [plan-omissions.md](plan-omissions.md).
