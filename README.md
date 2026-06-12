# CASTEP DFT Assistant

[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-plugin-6800AB)](https://code.claude.com/docs/en/skills)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills standard](https://img.shields.io/badge/Agent%20Skills-compatible-blue)](https://agentskills.io)

A [Claude Code](https://code.claude.com) skill that turns Claude into a practical **CASTEP** DFT assistant — geometry optimization, convergence testing, phonons, NEB diffusion barriers, and electronic structure.

Built from a real HPC battery-materials workflow, not textbook generalities. The troubleshooting guide documents mistakes that actually cost days of compute time — including the **`fix_com` NEB trap** that aborts every CASTEP NEB run with a misleading `Fixed coordinate mismatch` error, and whose obvious diagnosis is wrong.

## Install

In Claude Code:

```
/plugin marketplace add yiqingwen0828-dotcom/castep-dft
/plugin install castep-dft@castep-dft
```

That's it. Talk to Claude about your CASTEP work and the skill activates automatically, or invoke it directly with `/castep-dft:castep-dft`.

Update later with `/plugin marketplace update castep-dft`.

<details>
<summary>Alternative: install without the marketplace</summary>

Clone the skill straight into your personal skills folder:

```bash
git clone https://github.com/yiqingwen0828-dotcom/castep-dft
cp -r castep-dft/plugins/castep-dft/skills/castep-dft ~/.claude/skills/
```

The references also read fine as plain documentation if you don't use Claude Code at all.

</details>

## What it does

Ask Claude things like:

> *"Set up a geometry optimization for my FeS₂ cell on SLURM"*
> *"My CASTEP SCF won't converge for the Mn-substituted cell — why?"*
> *"My NEB run died with 'Fixed coordinate mismatch'"*
> *"Walk me through converging cutoff and k-points before I trust this energy"*
> *"How do I get a readable band structure for a spin-polarized system?"*

and Claude answers with working templates, the right CASTEP keywords, and the known pitfalls for that task.

### Coverage

| Area | What you get |
| :--- | :--- |
| **Convergence testing** | Cutoff + k-point procedure to 1 meV/atom — the step everyone skips and shouldn't |
| **Geometry optimization** | Standard & strict tolerance tiers; magnetic transition-metal handling (initial spins, spin polarization) |
| **Phonons** | DFPT vs finite displacement, phonopy integration, how to read soft modes / dynamic instability |
| **NEB barriers** | CI-NEB setup, the `fix_com : F` fix explained in depth, frozen-framework vs relaxed interpretation |
| **Electronic structure** | Clean band plots for spin-polarized systems, DOS/PDOS, d-band centre, band unfolding for disordered (SQS) supercells |
| **Troubleshooting** | SCF non-convergence in d-electron systems (PBE+U), overflow output, SLURM scheduling (backfill-friendly requests) |

### The `fix_com` trap (a taste of what's inside)

Every CASTEP NEB run aborts with:

```
Error: Fixed coordinate mismatch
Fixed coordinates should match in both structures to within 0.0010 A
```

The tempting diagnosis — "NEB needs an `IONIC_CONSTRAINTS` block to identify the migrating atom" — is **wrong**, and self-consistent enough to send you down a dead end for days. The real cause: CASTEP constrains the **centre of mass** by default (`Number of ionic constraints = 3` in your output), and a migrating ion makes the COM differ between endpoints. The fix is one line in the `.cell`:

```
fix_com : F
```

[references/neb.md](plugins/castep-dft/skills/castep-dft/references/neb.md) explains why this is safe for NEB and why the default exists at all. The [troubleshooting guide](plugins/castep-dft/skills/castep-dft/references/troubleshooting.md) generalizes the lesson: *read the error literally before theorizing.*

## What's inside

```
plugins/castep-dft/skills/castep-dft/
├── SKILL.md                 # entry point: quick reference + 2 end-to-end workflows
├── references/
│   ├── convergence.md       # cutoff + k-point testing (1 meV/atom)
│   ├── geometry-optimization.md
│   ├── phonons.md
│   ├── neb.md               # NEB + the fix_com trap, explained
│   ├── electronic-structure.md
│   └── troubleshooting.md   # SCF, PBE+U, scheduling, read-the-error-literally
├── templates/
│   ├── geomopt.param        # standard accuracy
│   ├── geomopt-strict.param # tight tolerances for final/publication runs
│   ├── neb.param            # CI-NEB
│   ├── example.cell         # annotated structure file
│   └── submit.sh            # SLURM batch script
└── scripts/
    └── parse_energies.py    # walk a tree of .castep files → CSV of energies + substitution energies
```

## Why this exists

Existing DFT-adjacent skills wrap Python libraries (pymatgen, ASE). Nothing targeted **CASTEP specifically**, and nothing was written from the perspective of *what actually goes wrong* on a real cluster. This skill is the documentation I wished existed when my NEB run died at 6am.

## Scope and caveats

- **CASTEP-focused.** VASP/Quantum ESPRESSO follow similar physics but different keywords; the troubleshooting *methodology* transfers, the syntax doesn't.
- Template settings (cutoff, k-points, smearing) are **starting points** — always converge them for your own system.
- Grown out of a transition-metal sulfide / battery-materials workflow; physics guidance is general, examples lean that way.

## Contributing

Corrections and additional war stories welcome — especially CASTEP errors whose first plausible explanation turned out to be wrong. Open an issue or PR.

## License

MIT © Qingwen Yi
