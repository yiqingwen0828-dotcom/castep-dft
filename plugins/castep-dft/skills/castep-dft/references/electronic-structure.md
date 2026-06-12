# Electronic structure: bands, DOS, d-band centre

After a converged geometry, the electronic structure explains *why* a material behaves as it does: band gap, conductivity, and (for transition-metal chemistry) the d-band centre that correlates with bonding and catalytic/redox behaviour.

## Band structure

A band-structure run is a non-self-consistent calculation along a k-path through high-symmetry points, using the converged density.

- Define the k-path with a `%BLOCK BS_KPOINT_PATH` (or `SPECTRAL_KPOINT_PATH`) in the `.cell`.
- In `.param`: add a spectral/bandstructure task or `task : BandStructure`.
- Plot with a tool like **sumo** (`sumo-bandplot`) or your own matplotlib script reading the `.bands` file.

### Making a readable band plot

Raw band plots of spin-polarized magnetic systems are often unreadable — two spin channels overlap into a mess. To get a clean figure:

- Plot **one spin channel** at a time (`--spin 1`).
- Restrict the energy window around the Fermi level (e.g. `--ymin -2.5 --ymax 2.5`), so the relevant valence/conduction bands fill the plot instead of a dense tangle.
- Colour valence vs conduction distinctly and mark the gap.

Example with sumo:

```
sumo-bandplot -c castep -f <seed>.bands --ymin -2.5 --ymax 2.5 --spin 1 --width 5 --height 4
```

## Density of states (DOS) and projected DOS (PDOS)

- DOS shows the distribution of states in energy; PDOS decomposes it by element and orbital (s/p/d).
- Requires a dense k-grid for a smooth DOS — denser than the SCF grid.
- PDOS is how you see, e.g., the transition-metal d-states near the Fermi level.

## d-band centre

The d-band centre is the first moment (energy-weighted average) of the projected d-DOS relative to the Fermi level:

```
ε_d = ∫ E · ρ_d(E) dE  /  ∫ ρ_d(E) dE
```

It is a compact descriptor: a deeper (more negative) d-band centre generally means stronger metal–ligand bonding and different redox behaviour. When comparing a substituted/alloyed system to a parent, shifts in each element's d-band centre quantify how the local electronic environment changed.

## PBE underestimates band gaps — and that's usually fine

Plain PBE (GGA) systematically **underestimates** band gaps, often by a large fraction (a PBE gap of ~0.4 eV can correspond to an experimental ~0.9 eV). This is a well-known functional limitation, not an error in your run.

Crucially: if your scientific targets are **stability and ion migration**, the underestimated gap does not affect those conclusions. Only switch to an expensive hybrid (e.g. HSE, 10–100× the cost) if the gap value itself is your deliverable. State this trade-off explicitly in your methods.

## Disordered systems: band unfolding

For a supercell with substitutional disorder (e.g. a special quasirandom structure, SQS), translational symmetry is broken and the supercell band structure is "folded" — uninterpretable directly. **Band unfolding** maps it back onto the primitive Brillouin zone to recover an effective band structure. Tools such as **easyunfold** do this from CASTEP output. Expect these spectral runs to be long (many k-points).
