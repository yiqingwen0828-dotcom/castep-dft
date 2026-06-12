# Phonons (dynamic stability)

Phonons test whether a relaxed structure is a true minimum or just a stationary point. A structure can sit at an energy minimum with respect to the relaxation steps you took, yet still be **dynamically unstable** — it would spontaneously distort if displaced. Phonons catch this; formation energy alone cannot.

## Why phonons, not just formation energy

Formation energy tells you a structure is thermodynamically favourable relative to references. It does **not** tell you the structure is mechanically stable. A negative formation energy with imaginary phonon modes means the structure will distort to something lower. For any stability claim, you need both.

## Reading the result

- Phonon frequencies are reported in cm⁻¹ (or THz).
- **All real (positive) frequencies → dynamically stable.**
- **Imaginary frequencies, conventionally printed as negative cm⁻¹ → a soft mode / instability** at that q-point. This is physics, not a numerical error. The eigenvector of the soft mode tells you the distortion direction.

A small imaginary mode (a few cm⁻¹) near Γ can be a numerical artifact of insufficient convergence or supercell size; a deep one (tens of cm⁻¹) at a zone-boundary point (X, M, ...) is a real instability worth investigating.

## Two methods

CASTEP supports DFPT (linear response) and finite displacement.

- **DFPT**: efficient, but not available for all functionals/setups (e.g. some metals, +U).
- **Finite displacement**: always works; build a supercell, displace atoms, compute forces. Often run via **phonopy** as a wrapper around CASTEP single-point force calculations.

### Finite displacement with phonopy

Typical loop:
1. Relax the primitive cell with **strict** tolerances.
2. Generate displaced supercells (e.g. 2×2×2) — `phonopy` produces them.
3. Run a CASTEP single-point force calculation for each displacement.
4. Collect forces into `FORCE_SETS` and post-process.

Load with the force sets, not force constants:

```python
import phonopy
ph = phonopy.load("phonopy_disp.yaml", force_sets_filename="FORCE_SETS")
```

(Using `FORCE_CONSTANTS` when you actually produced `FORCE_SETS` is a common "force constants not found" error.)

## Practical notes

- Use a relaxed structure converged with strict tolerances; loose forces contaminate the dynamical matrix.
- The supercell must be large enough that force constants decay within it. Test 2×2×2 vs 3×3×3 if a borderline soft mode appears.
- Phonon calculations are expensive (many force evaluations). Budget HPC time and use `write_checkpoint` appropriately.
