# NEB diffusion barriers

Nudged Elastic Band (NEB) finds the minimum-energy path and barrier between two endpoint structures — e.g. an ion hopping between two sites. The barrier height controls the diffusion coefficient and thus rate capability, so it is a key quantity for battery and ionic-conductor work.

## Setup

NEB in CASTEP is a transition-state search task. Minimal `.param` (see `templates/neb.param`):

```
task                         : TransitionStateSearch
tssearch_method              : NEB
tssearch_max_path_points     : 7         # number of images along the path
tssearch_neb_max_iter        : 200
tssearch_neb_climbing        : TRUE      # CI-NEB: drives the top image to the true saddle
tssearch_neb_spring_constant : 5.0 eV/Ang**2
xc_functional                : PBE
cut_off_energy               : 550 eV
spin_polarized               : true
```

Always use **climbing-image NEB** (`tssearch_neb_climbing : TRUE`). Without it, the highest image need not sit exactly at the saddle, so the barrier is underestimated.

The `.cell` file defines the endpoints with three position blocks:

```
%BLOCK POSITIONS_FRAC            ... reactant (initial)
%BLOCK POSITIONS_FRAC_PRODUCT    ... product  (final)
%BLOCK POSITIONS_FRAC_INTERMEDIATE  (optional, seeds the path)
```

The migrating ion sits at a different position in reactant vs product. Whether the framework moves depends on your endpoints and constraints: if only the migrating ion differs between endpoints, the framework path starts out fixed — allow it to relax during the NEB unless you are intentionally computing a frozen-framework **upper bound** on the barrier (and say which one you did when reporting).

## ⚠️ The fix_com trap — read this before you run NEB

**Symptom.** The job starts, completes the first endpoint's SCF, then aborts with:

```
Error: Fixed coordinate mismatch
Fixed Reactant Atom:   3.8244  3.8311  3.8218
Fixed Product Atom:    3.8262  4.3202  1.1167
Fixed coordinates should match in both structures to within  0.0010 A
```

**Wrong diagnosis (tempting but false).** "CASTEP NEB needs an IONIC_CONSTRAINTS block to identify the migrating atom; without it, all atoms are treated as fixed." This sounds self-consistent and will send you down a dead end.

**Actual cause.** CASTEP applies **one constraint by default even if you specify none: it fixes the centre of mass.** Check the `Symmetry and Constraints` section of the `.castep` output:

```
Number of ionic constraints     =           3
Centre of mass is constrained
```

Those 3 constraints are the COM's x, y, z. Because the migrating ion sits at different coordinates in the reactant and product, the system's centre of mass differs between the two endpoints. CASTEP checks that constrained quantities match across endpoints, the COM does not, and the run aborts. It has nothing to do with `IONIC_CONSTRAINTS`.

**Fix.** Add one line to the `.cell` file:

```
fix_com : F
```

After this, the output shows:

```
There are no ionic constraints specified or generated for this cell
Centre of mass is NOT constrained
```

and the NEB proceeds normally.

**Why turning it off is safe for NEB.** The COM constraint exists to remove the meaningless rigid-translation degree of freedom in ordinary geometry optimization, where it helps. NEB intentionally has endpoints whose COM differs, so the constraint is actively wrong here. NEB barriers depend on energy differences along the path, which are invariant to rigid translation — there is no downside to `fix_com : F` for NEB. (Keep the default `fix_com : T` for ordinary single-structure relaxations, where switching it off only adds a useless drift direction.)

## Interpreting the barrier

- The barrier is the energy of the highest (climbing) image relative to the reactant.
- A **frozen-framework** NEB (only the ion moves, lattice fixed) gives an **upper bound** on the true barrier; allowing local framework relaxation lowers it. State which you computed.
- Sanity-check against literature for similar materials; a barrier far outside the expected range (e.g. > ~2 eV when the literature is 0.5–1.5 eV) usually signals a frozen framework, a bad path, or an unconverged setup.

## Practical notes

- Generate a sensible initial path (linear interpolation between endpoints, or seed with `POSITIONS_FRAC_INTERMEDIATE`). A bad initial path wastes many iterations.
- More images resolve the saddle better but cost proportionally more; 5–9 is typical.
- NEB is expensive (every image is a full SCF every iteration). Use a generous walltime, but right-size memory and cores — over-requesting walltime delays scheduling on busy clusters (short jobs backfill sooner).
