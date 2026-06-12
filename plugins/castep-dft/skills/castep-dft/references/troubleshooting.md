# Troubleshooting CASTEP

## Working principle: read the error literally

Before proposing a cause, **read the actual error text and the relevant section of the `.castep` output.** Do not pattern-match to a remembered theory. An explanation that "just fits" is a signal to stop and verify, not a signal you found the answer — the convenient story is often wrong. Every line CASTEP prints (e.g. `Number of ionic constraints = 3`) means something specific; understand it rather than skimming past it. A wrong diagnosis that goes unchallenged propagates into your methods chapter.

---

## SCF does not converge

**Symptom.** The SCF loop runs to `max_scf_cycles` without satisfying `elec_energy_tol`; energy oscillates instead of settling.

**Most common cause: magnetic d-electron systems.** Half-filled or near-degenerate d-shells (Mn d⁵ is the classic offender) have many close-lying magnetic states the SCF bounces between.

Things to try, roughly in order:
- Set explicit, sensible **initial spins** in the `.cell` (`Mn:SPIN=5.0` etc.). A good starting guess often fixes it outright.
- Adjust mixing: `mixing_scheme : Pulay` with a smaller charge/spin mixing amplitude, or try density mixing parameters.
- Increase `smearing_width` slightly to ease metallic/degenerate occupation.
- Raise `max_scf_cycles` (e.g. 250+) for genuinely hard cases.
- **PBE+U.** For strongly-correlated 3d states, a Hubbard U (e.g. U ≈ 4 eV on Mn d) localizes the electrons and stabilizes the SCF. Add a `%BLOCK HUBBARD_U` block. This is often the real fix for Mn and other late/mid 3d metals, and is also a methodological choice you should justify.

If only one element in a series fails to converge while the rest are fine, suspect that element's d-occupation specifically, not your global settings.

---

## "Fixed coordinate mismatch" in NEB

**Cause.** The default centre-of-mass constraint (`fix_com : T`), not a missing `IONIC_CONSTRAINTS` block. The migrating ion makes the COM differ between endpoints.

**Fix.** Add `fix_com : F` to the `.cell` file. Full explanation in [neb.md](neb.md).

This is the canonical example of the "read the error literally" principle: the convenient theory (NEB needs ionic constraints) is wrong; the output's `Centre of mass is constrained` line is the real clue.

---

## "*** stars ***" instead of numbers in output

Numeric overflow — a value exceeded its print format. Almost always a symptom of something diverging (bad geometry, runaway SCF, wrong units). Don't treat the formatting as the problem; find what blew up.

---

## Geometry optimization won't converge

- Check **which** tolerance is failing (force / energy / stress / displacement) in the output — only that one needs attention.
- Loosen unrealistic tolerances, or increase `geom_max_iter`.
- A structure that keeps moving may be near an instability (do a phonon check) or starting too far from a minimum (pre-relax loosely first).
- For magnetic systems, an unconverged SCF at each step poisons the forces — fix SCF convergence first (above).

---

## Phonopy "force constants not found"

You passed `FORCE_CONSTANTS` when you actually generated `FORCE_SETS`. Load with:

```python
phonopy.load("phonopy_disp.yaml", force_sets_filename="FORCE_SETS")
```

---

## Pseudopotential / SPECIES_POT issues

- With no `SPECIES_POT` block, CASTEP generates on-the-fly (OTF) pseudopotentials and records the generation string in the output — reproducible. This is fine for most work.
- If you do specify `.usp`/`.upf` files, make sure they (or symlinks) exist in the run directory and cover **every** species in the cell.

---

## Cluster / scheduling (SLURM)

- A job stuck `PENDING` for a long time is often **over-requesting walltime**. Short jobs backfill into gaps between large jobs; a 4-day request on a 30-minute test will wait far longer than necessary. Right-size `--time`.
- Match `--mem` and `--ntasks` to the job. Check a completed similar run's actual peak memory before requesting hundreds of GB.
- `mpirun -np $SLURM_NTASKS castep.mpi <seed>` — make sure `<seed>` has no extension and matches your `.cell`/`.param` names. A double suffix (`castep.mpi seed_seed`) silently fails.
- Confirm the right CASTEP module is loaded (`module load apps/.../castep/<version>`).
