# Convergence testing

Before any production calculation, converge the two numerical knobs that control accuracy: the plane-wave cutoff energy and the k-point sampling. **Target: total energy converged to within 1 meV/atom.** Report this in your methods section.

## Why it matters

CASTEP results are only meaningful relative to a converged basis and BZ sampling. An unconverged cutoff or k-grid can shift energies, lattice constants, and barriers enough to flip a conclusion. Convergence is cheap insurance — a handful of short single-point runs.

## Procedure

Converge the two parameters **separately**, one at a time, on a fixed structure (a single-point energy, `task: SinglePoint`).

### 1. Cutoff energy

Hold k-points at a reasonable fixed grid (e.g. dense enough that it is not the bottleneck). Run single-points sweeping `cut_off_energy`:

```
300, 350, 400, 450, 500, 550, 600, 650, 700 eV
```

Plot total energy per atom vs cutoff. Pick the lowest cutoff where successive energies differ by < 1 meV/atom. For sulfides/oxides with transition metals, this is often 500–600 eV.

### 2. k-point grid

Fix the cutoff at the converged value. Sweep `kpoint_mp_grid`:

```
2 2 2, 3 3 3, 4 4 4, 5 5 5, 6 6 6, 7 7 7 ...
```

Plot total energy per atom vs grid density. Pick the coarsest grid converged to < 1 meV/atom. Larger cells need fewer k-points (BZ is smaller); a 2×2×2 supercell of a cell that needed 6×6×6 may only need 3×3×3.

## Tips

- Compare **energy per atom**, not total energy, so cells of different size are comparable.
- For metals/small-gap systems, k-point convergence is slower — be generous.
- Use the same `smearing_width` throughout the sweep.
- Keep a CSV of (parameter, energy/atom) and the convergence plot; it goes straight into your thesis methods chapter.
- Once converged, reuse the same cutoff and k-point density for every related system in a study, for internal consistency.

## Minimal single-point .param for testing

```
task            : SinglePoint
xc_functional   : PBE
cut_off_energy  : 550 eV      # the variable being swept
spin_polarized  : true
fix_occupancy   : false
smearing_width  : 0.1 eV
max_scf_cycles  : 100
elec_energy_tol : 1.0e-6 eV
```
