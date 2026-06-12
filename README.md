# CASTEP DFT Assistant

A [Claude Code](https://code.claude.com) skill that helps you run and troubleshoot **CASTEP** DFT calculations: geometry optimization, convergence testing, phonons, NEB diffusion barriers, and electronic structure — plus a troubleshooting checklist built from real mistakes (including the `fix_com` NEB trap that costs people days).

It is grounded in an actual HPC/SLURM CASTEP workflow, not generic textbook advice.

## What you get

When this skill is active, Claude can help you:

- **Set up calculations** from working `.cell` / `.param` / submit-script templates.
- **Converge** cutoff energy and k-points to 1 meV/atom before trusting any number.
- **Run geometry optimization** at standard or strict accuracy, including magnetic transition-metal systems.
- **Compute phonons** and read soft modes / dynamic instability correctly.
- **Run NEB** diffusion barriers — and avoid the `Fixed coordinate mismatch` abort.
- **Analyse electronic structure**: clean band plots, DOS/PDOS, d-band centre, band unfolding for disordered supercells.
- **Debug failures**: SCF non-convergence in d-electron systems (PBE+U), overflow output, scheduling issues.

## Install

In Claude Code:

```
/plugin marketplace add yiqingwen0828-dotcom/castep-dft
/plugin install castep-dft@castep-dft
```

Then just talk to Claude about your CASTEP work, or invoke the skill directly:

```
/castep-dft:castep-dft
```

To update later:

```
/plugin marketplace update castep-dft
```

### Alternative: use without the marketplace

Clone the skill straight into your personal skills folder:

```bash
git clone https://github.com/yiqingwen0828-dotcom/castep-dft
cp -r castep-dft/plugins/castep-dft/skills/castep-dft ~/.claude/skills/
```

## What's inside

```
plugins/castep-dft/skills/castep-dft/
├── SKILL.md                 # entry point + quick reference
├── references/
│   ├── convergence.md       # cutoff + k-point testing (1 meV/atom)
│   ├── geometry-optimization.md
│   ├── phonons.md
│   ├── neb.md               # NEB + the fix_com trap, explained
│   ├── electronic-structure.md
│   └── troubleshooting.md   # SCF, PBE+U, scheduling, read-the-error-literally
├── templates/
│   ├── geomopt.param        # standard accuracy
│   ├── geomopt-strict.param # tight tolerances for final runs
│   ├── neb.param            # CI-NEB
│   ├── example.cell         # annotated structure file
│   └── submit.sh            # SLURM batch script
└── scripts/
    └── parse_energies.py    # extract final energies, compute substitution energies
```

## Scope and caveats

- Focused on **CASTEP** specifically. Other DFT codes (VASP, Quantum ESPRESSO) follow similar principles but different syntax and keywords.
- Numerical settings in the templates (cutoff, k-points, smearing) are **starting points** — always converge them for your own system.
- Built from a transition-metal sulfide / battery-materials workflow; the physics guidance is general, but examples lean that way.

## License

MIT. Contributions and corrections welcome.
