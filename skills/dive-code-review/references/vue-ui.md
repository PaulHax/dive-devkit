# Vue & Vuetify

## Dialog row layout — conditional content between sibling rows

**The recurring one.** Vuetify spaces stacked rows with the adjacency selector `.row + .row`, and a
`v-row` ends on a negative bottom margin (base −12px). The moment anything conditional renders
*between* two rows — an error alert, a warning list, a progress line — the rows are no longer
adjacent siblings, the rule stops matching, and the following row rides **up over** the thing that
just appeared. The layout looks fine until the error path fires, which is exactly when the user is
already unhappy.

`Upload.vue` has three separate band-aids for this, each with its own in-tree comment:

```
<!--
  mt-3 states the gap outright instead of relying on Vuetify's `.row + .row` rule: the
  error alert and the ignored-file list sit between these rows, and when either renders
  the row falls back to the base -12px and rides up over it.
-->
```

and, on the ignored-file block and the uploading-progress block:

```
<!-- mt-3 clears the negative bottom margin the row above ends on. -->
```

Review checks whenever a diff adds anything conditional to a dialog body:

- Does a new `v-if` block sit between two `v-row`s? If so, both it and the row after it need an
  explicit top margin — never inherit the adjacency rule.
- Was the layout viewed with the conditional content **rendered**? A screenshot of the happy path
  proves nothing. Force the error state.
- New rows appended to an existing stack inherit the same trap; check the row above ends where you
  think it does.

A screenshot review caught the visible version of this: "the 17 file remaning in the updlaod layout
is wrong". Three more reports traced to the same mechanism — "the help text is overlfowing", "the
ouline is runing through the details text", "overlap problems again" — so treat a new overlap bug in
a dialog as this trap until proven otherwise.

The values themselves keep drifting: post-review, `046a1315` bumped the same file's error alert
`mt-2`→`mt-4` and its ignored-file block `mt-3`→`mt-6`. Each ad-hoc bump is a signal the component
still lacks a systematic fix, and that the margin was guessed rather than measured against the
rendered error state.

## Long text in dialog rows

Filenames, server error strings, and ignored-file reasons are all unbounded and all user-supplied.
Several Vuetify surfaces default to `nowrap` and need an explicit override — the established idiom in
the tree is `white-space: normal !important` (`DatasetConfigEditorDialog.vue:104`,
`DatasetInfo.vue:315`) or `text-truncate` with a `min-width-0` flex parent
(`DatasetInfo.vue:233`, `JobConfigFilterTranscodeDialog.vue:315`).

Check any new row that renders a filename or a server message: long value, does it wrap, truncate, or
blow out the row? Truncation without a tooltip hides information the user needs to act on — an error
row exists so the user can re-pick the file.

## Other Vuetify gotchas

- Bare text placed after a `v-row` gets pulled up by the same negative margins — wrap it in
  `v-row`/`v-col`.
- A **disabled** `v-btn` swallows hover, so tooltip and menu activators need a `span` wrapper.
- Tooltip content is teleported: style it unscoped, or via `content-class`.
- Fixed menu widths must fit new labels — compute the width, don't hard-code a literal.

Kitware/dive@60b5ddf1, @b868b2fe, @968cebfe.

## Vue 2 reactivity

- **Never `ref(injectedRef)`** — it aliases shared state, and the `||` fallback never applies because
  the ref object is always truthy. Copy `.value`: `ref(defaultSet.value || 'default')`
  (Kitware/dive@966895a7).
- Recover state by mutating tracked objects **in place** (`12be12a4`).
- Computeds reading Track data must touch `track.revision.value` — Kitware/dive@fc6e7541:
  `// Depend on revision so UI updates when notes change`.

## Panel and component structure

- Sibling sections in a panel get identical treatment — chevrons on all or none. `50e60cd0` widened
  `openInfoPanels` to `[0,1,2]` when a third panel arrived.
  > "make the custom metdata section consitatn by addin the up down arrow there"
- The DIVE sidebar idiom is flat multi-open `v-expansion-panels`, compact 32px headers, `::v-deep`
  padding reset (`d60a923d`). Survey existing DIVE components before reaching for stock Vuetify — and
  treat needed CSS overrides as a smell that the component choice is wrong.
  > "these CSS rules are key. I wonder why we need them now. Maybe we're doing the layout wrong or using the wrong components?"
- Secondary/provenance info goes behind an `mdi-information-outline` tooltip in the section header,
  right-aligned via `v-spacer`, tooltip text mirrored into `aria-label` — never a body caption row
  (`420ad398`). Expect precise placement feedback: "the icon should be On the right side".
- Split ~500-line SFCs into a directory named for the component: presentational children (props in,
  `emit('change', next)` out), parent owns fetching, persistence, and panel state; specs move too;
  module clusters get a README. `964b6aa6` (DatasetInfo/, 5 files), `f7889bb` (551 lines out of
  LayerManager.vue into 7 composables), `600cf3b3` (806 lines out of common.ts).
- Extend the existing `MediaController` surface instead of minting provide/inject symbols — a comment
  justifying the workaround is the signal to extend the controller instead. `a7a228d8` deleted
  `CameraMediaNamesSymbol` and added `filenames` to `MediaControllerReactiveData`.
- Point-free handlers: `@event="handler"`, not `"handler($event)"`; method references passed to
  `.map`, no one-arg arrow wrappers (`889ba328`).
  > "can we not jsut pass the fucntion handle directly here? no need for arrow fucntion i think?"
- Bind persisted `clientSettings` directly with `v-model` at the point of use — no local ref
  snapshot, one surface per toggle (Kitware/dive@6d71863).

## Loading and busy state

All async loading routes through the single in-flight counter (`beginWork`/`endWork`) — `d6622c04`
switched `runDesktop` off direct `loading.value` writes. Busy buttons use the `v-btn` `:loading`
prop, not a spinning `mdi` icon. "N remaining" status lines get a spinner (Kitware/dive@2c276073).

---

Related: [correctness.md](correctness.md) for the error-path state machine behind these dialogs.
