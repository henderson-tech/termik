# lupa eval packs: termik

Frozen gold for Výbava's lupa (`docs/lupa.md`, `docs/lupa-evals.md` there),
pinned to the commit each `pack.json` names. `lupa eval .testing/lupa/<pack>`
checks that commit out in a scratch worktree, so main moving on never drifts
the gold.

- `rust/`: `lupa refs` on 250 module-level declarations and 150 inherent
  methods under `cmux-tui/crates`, with every reference rust-analyzer finds
  there (aliased `use … as` occurrences kept when its goto-definition lands
  on the declaration).
- `swift/`: `lupa refs` on top-level declarations and members of
  `Packages/macOS/CmuxFoundation`, with every reference sourcekit-lsp (the
  Swift index store) finds there.

Regenerate (new sample, new pin) from a vybava checkout, against a clean
checkout of the commit to pin:

```sh
go run ./crates/lupa/evals/gold/lsp-gold --lang rust --root <termik> \
  --scope cmux-tui/crates --sample 250 --prefix termik \
  --out <termik>/.testing/lupa/rust/cases/refs.json
go run ./crates/lupa/evals/gold/lsp-gold --lang swift --root <termik> \
  --project Packages/macOS/CmuxFoundation --scope Packages/macOS/CmuxFoundation \
  --sample 200 --prefix termik --out <termik>/.testing/lupa/swift/cases/refs.json
```

and the member cases with `--members --sample 150 --out …/members.json`; then
set `sha` in each `pack.json` to the commit the gold was generated at.
