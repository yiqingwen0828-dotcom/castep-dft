---
name: castep-dft
description: Run and troubleshoot CASTEP DFT calculations — geometry optimization, convergence testing (cutoff + k-points), phonons, NEB diffusion barriers, and electronic structure (band/DOS/d-band). Use when the user works with .cell/.param files, CASTEP output (.castep), runs DFT on an HPC/SLURM cluster, or hits errors like SCF non-convergence or "Fixed coordinate mismatch".
when_to_use: Triggered by CASTEP .cell/.param/.castep files, requests to set up or debug a DFT calculation, convergence testing, phonon/NEB/band-structure workflows, or CASTEP errors on a SLURM cluster.
---

# CASTEP DFT Assistant

Practical, battle-tested guidance for running CASTEP DFT calculations on an HPC cluster. The body below is the quick reference; load a file from `references/` when a task needs depth.

## How CASTEP jobs are structured

A CASTEP run needs three files sharing one seedname (`<seed>.cell`, `<seed>.param`) plus a job script:

- **`<seed>.cell`** — structure: lattice, atomic positions, k-point grid, pseudopotentials, constraints.
- **`<seed>.param`** — calculation settings: task, XC functional, cutoff, SCF/geometry tolerances.
- **submit script** — SLURM batch script calling `mpirun -np $SLURM_NTASKS castep.mpi <seed>`.

Run with `castep.mpi <seed>` (no extension). Output lands in `<seed>.castep`.

## The golden rule: converge before you trust

**Never report a number from an unconverged calculation.** Two parameters must be converged first, against a target of **total energy within 1 meV/atom**:

1. `cut_off_energy` (plane-wave basis cutoff)
2. `kpoint_mp_grid` (Brillouin-zone sampling)

See [references/convergence.md](references/convergence.md) for the procedure. Skipping this is the most common source of wrong results.

## Core workflow

1. **Build / obtain the structure** → `.cell` file (lattice + positions).
2. **Converge cutoff and k-points** → see convergence reference.
3. **Geometry optimization** → relax to a minimum. Template: `templates/geomopt.param`.
4. **Property calculation** → phonons, NEB, bands/DOS, depending on the question.
5. **Post-process** → extract energies, plot.

## Quick reference: a minimal geometry optimization

`.param` (standard accuracy — see `templates/geomopt.param`):

```
task            : GeometryOptimization
xc_functional   : PBE
cut_off_energy  : 550 eV        # MUST be converged for your system
spin_polarized  : true          # required for magnetic systems (Fe, Co, Ni, Mn, Cr...)
fix_occupancy   : false
smearing_width  : 0.1 eV
max_scf_cycles  : 100
elec_energy_tol : 1.0e-6 eV
geom_max_iter   : 100
geom_force_tol  : 0.03 eV/Ang
geom_energy_tol : 1.0e-5 eV
geom_stress_tol : 0.05 GPa
geom_disp_tol   : 1.0e-3 Ang
mixing_scheme   : Pulay
```

`.cell` (essentials — see `templates/example.cell`):

```
%BLOCK LATTICE_CART
 5.419 0.0   0.0
 0.0   5.419 0.0
 0.0   0.0   5.419
%ENDBLOCK LATTICE_CART

%BLOCK POSITIONS_FRAC
Fe  0.0  0.0  0.0
...
%ENDBLOCK POSITIONS_FRAC

kpoint_mp_grid 5 5 5
```

Pseudopotentials default to CASTEP's on-the-fly (OTF) generation if no `SPECIES_POT` block is given — fine for most work and reproducible because the string is recorded in the output.

## Task-specific guidance

| Task | Reference | Key gotcha |
| :--- | :-------- | :--------- |
| Convergence testing | [references/convergence.md](references/convergence.md) | Converge cutoff and k-points **separately**; target 1 meV/atom |
| Geometry optimization | [references/geometry-optimization.md](references/geometry-optimization.md) | Magnetic systems need `spin_polarized: true` and good initial spins |
| Phonons | [references/phonons.md](references/phonons.md) | Imaginary (negative cm⁻¹) modes = dynamic instability, not a bug |
| NEB diffusion barriers | [references/neb.md](references/neb.md) | **`fix_com : F`** in `.cell` — default COM constraint breaks NEB |
| Band structure / DOS / d-band | [references/electronic-structure.md](references/electronic-structure.md) | PBE underestimates band gaps; fine for stability/migration |
| Anything failing | [references/troubleshooting.md](references/troubleshooting.md) | Read the error **literally** before theorizing |

## Templates and scripts

- `templates/geomopt.param` — standard-accuracy geometry optimization.
- `templates/geomopt-strict.param` — tight tolerances for final/publication runs.
- `templates/neb.param` — CI-NEB transition-state search.
- `templates/example.cell` — annotated cell file.
- `templates/submit.sh` — SLURM batch script.
- `scripts/parse_energies.py` — extract final energies from many `.castep` files and compute substitution/formation energies. Run: `python3 scripts/parse_energies.py <root_dir>`.

## Working method (important)

When a calculation fails, **read the actual error text and the relevant section of the `.castep` output before proposing a cause.** Do not pattern-match to a remembered theory. The classic trap: a CASTEP NEB run aborts with `Fixed coordinate mismatch`, and it is tempting to blame the migration setup — but the real cause is the default centre-of-mass constraint (`Number of ionic constraints = 3` / `Centre of mass is constrained` in the output). The fix is one line: `fix_com : F`. See [references/neb.md](references/neb.md) and [references/troubleshooting.md](references/troubleshooting.md).
