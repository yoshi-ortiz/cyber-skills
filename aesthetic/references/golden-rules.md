# Golden rules

Source: `Knowledge/design/fundamentals.md` and `history_and_aesthetics.md`. These are the domain foundations the skill designs *from*. A move that cannot cite one of them is improvisation — label it, 1 star.

The rules split in two, and the split is the whole point:

- **Checkable** — decided by `scripts/golden_rules.py`. A design that declares these produces the same answer on every run.
- **Directed** — needs judgement. You read them; nothing enforces them. This is where output legitimately varies, and it should be a deliberate choice, not an accident of what the model felt like.

## Checkable

| Rule | Constraint | Source |
| --- | --- | --- |
| `measure` | 45–75 characters per line of body text | Bringhurst, *Elements of Typographic Style* — fundamentals §4 |
| `contrast` | body text ≥ 4.5:1 value contrast | value contrast "maximizes boundary edge detection … UI text legibility" — fundamentals §2 |
| `grid` | one of `manuscript` \| `column` \| `modular` | Müller-Brockmann, *Grid Systems* — fundamentals §3 |
| `gestalt` | name the law doing the grouping: `proximity`, `similarity`, `closure`, `continuity`, `figure-ground` | Koffka — fundamentals §5 |
| `register` | every mark declares `icon` \| `index` \| `symbol` | Peirce's triad — fundamentals §5 |

```bash
python3 scripts/golden_rules.py --design spec/design-harness/candidate.json --min-coverage 0.8
```

**Coverage is the determinism metric, and it is not a quality score.** A decision the spec declares is one a rule can decide, so it lands identically on every run — *even when the rule says it is wrong*. A decision left undeclared is free to vary, and that variance is exactly why output has been unrepeatable. Raise coverage to make runs agree; fix failures to make them good. They are different jobs.

## Directed

These carry the design and cannot be automated. State which one you are working in, in the ledger `--evidence`, before you draw.

**Elements** — point (focal anchor), line (horizontal = calm, vertical = authority, diagonal = kinetic tension, curved = organic), shape (geometric / organic / abstract), form, positive vs. negative space, texture, value.

**Colour** — Albers' optical relativity: a hue shifts with what surrounds it, so judge colour in place, never on a swatch. Itten's contrasts (hue, light-dark, cold-warm, complementary, simultaneous, saturation, extension). Harmony choice — monochromatic, analogous, complementary, triadic — is a stated decision, not a default.

**Composition** — balance (symmetrical = formal/institutional, asymmetrical = dynamic equilibrium, radial), visual hierarchy primary → secondary → tertiary, proportional systems (φ ≈ 1.618, rule of thirds).

**Typography** — classification carries meaning before a word is read: Old Style (Garamond), Transitional (Baskerville), Didone (Bodoni), Slab (Clarendon), Grotesque (Helvetica), Geometric (Futura), Humanist (Gill Sans). Kerning is per-pair; tracking is per-run; leading is baseline-to-baseline.

**Movement** — name the lineage the work sits in, because "no movement" defaults to the homogeneous corporate flat design that reads as slop:

| Movement | Philosophy |
| --- | --- |
| Bauhaus / Swiss | objective layout, functional hierarchy, form follows function |
| Constructivism / Dada | diagonal axis, photomontage, rejection of classical symmetry |
| New Wave / Punk | photocopier texture, raw type, intentional imperfection |
| Post-Digital Brutalism | stark borders, system fonts, anti-polish, exposed structure |

**Aesthetic stance** — the beautiful (harmony, Kant) and the sublime (overwhelming magnitude, Burke) are different targets and cannot both be hit at once. Pick one per artefact.

See [anti-slop.md](anti-slop.md) for what happens when none of this is declared.
