# Geometry optimization

Relax a structure to its nearest energy minimum (atoms and, optionally, cell). This is the starting point for almost everything else.

## Two accuracy tiers

Use **standard** tolerances for screening and intermediate work, and **strict** tolerances for the final structure you will report or feed into phonons/NEB.

Standard (`templates/geomopt.param`):

```
geom_force_tol  : 0.03 eV/Ang
geom_energy_tol : 1.0e-5 eV
geom_stress_tol : 0.05 GPa
geom_disp_tol   : 1.0e-3 Ang
elec_energy_tol : 1.0e-6 eV
opt_strategy    : speed
```

Strict (`templates/geomopt-strict.param`):

```
geom_force_tol  : 0.01 eV/Ang
geom_energy_tol : 1.0e-6 eV
geom_stress_tol : 0.02 GPa
geom_disp_tol   : 5.0e-4 Ang
elec_energy_tol : 1.0e-8 eV
opt_strategy    : default
```

A geometry optimization is converged only when **all** of force, energy, stress, and displacement tolerances are simultaneously satisfied. Check the output for `Geometry optimization completed successfully`.

## Cell relaxation

By default `GeometryOptimization` relaxes atomic positions only. To relax the cell as well, the optimizer also uses stress; make sure `geom_stress_tol` is set. To constrain the cell shape (e.g. fix it cubic), use a `%BLOCK CELL_CONSTRAINTS` block in the `.cell` file.

## Magnetic systems (transition metals)

For Fe, Co, Ni, Mn, Cr and other magnetic elements:

- `spin_polarized : true` is mandatory. Without it you converge to a non-magnetic state that is usually wrong.
- Set sensible **initial spins** in the `.cell` file, e.g. `Fe:SPIN=4.0`, otherwise the SCF may settle into the wrong magnetic state or fail to converge.
- For systems with multiple plausible magnetic orderings (antiferromagnetic candidates), you may need to test several orderings and take the lowest-energy one. This is essential for half-filled d-shells.
- See [troubleshooting.md](troubleshooting.md) for SCF convergence failures, which are most common in magnetic d-electron systems.

## PBE overestimates lattice constants

Plain PBE (GGA) typically overestimates lattice constants by ~1–2%. This is expected and usually acceptable for stability and migration studies. If you need accurate lattice parameters specifically, that is a separate methodological choice (e.g. a different functional), not a convergence problem.

## Practical notes

- `write_checkpoint : none` keeps directories clean for short runs; use `ALL` if you want restart capability for long jobs.
- Restarting: CASTEP can continue from a `.check` file. For a fresh start, remove old `.check`/`.castep_bin`.
- Always sanity-check the relaxed structure (bond lengths, symmetry) before using it downstream.
