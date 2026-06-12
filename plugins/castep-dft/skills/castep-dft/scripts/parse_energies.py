#!/usr/bin/env python3
"""
Parse CASTEP .castep files, extract final energies, and compute substitution energies.

Directory conventions (all configurable via CLI flags):
- parent/host directories named like FeS2, FeS2_parent, or parent   (--parent-names)
- substitution directories named like Co_sub, Ni_sub, Cr_sub, Mn_sub (--sub-elements)
- elemental reference directories in singlepoint/<Element>           (--reference-root)
- host element being substituted out                                  (--host-element)

Substitution energy formula:
    E_sub(M) = E(sub_M) - E(parent) - mu_M + mu_host

where mu_X = E(reference bulk X) / N_X_in_reference_cell.

A negative E_sub means substitution is favourable *relative to the chosen
reference chemical potentials* (elemental bulk by default); compare trends
across M, not absolute stability.

Examples:
    # FeS2 host, Mn/Co/Ni/Cr substitutions (the defaults)
    python3 parse_energies.py ./work

    # NiO host with Co/Zn substitutions, references under refs/<Element>
    python3 parse_energies.py ./work --parent-names NiO,parent \\
        --host-element Ni --sub-elements Co,Zn --reference-root refs
"""
from __future__ import annotations
import argparse
import csv
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

FINAL_ENERGY_RE = re.compile(r"Final energy,\s*E\s*=\s*([-\d\.Ee+]+)")
GEOM_DONE_RE = re.compile(r"Geometry optimization completed successfully", re.I)
RUN_STARTED_RE = re.compile(r"Run started:", re.I)

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_last_final_energy(castep_path: str) -> Optional[float]:
    vals = FINAL_ENERGY_RE.findall(read_text(castep_path))
    return float(vals[-1]) if vals else None

def geometry_completed(castep_path: str) -> bool:
    return bool(GEOM_DONE_RE.search(read_text(castep_path)))

def run_started(castep_path: str) -> bool:
    return bool(RUN_STARTED_RE.search(read_text(castep_path)))

def parse_species_counts_from_cell(cell_path: str) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    if not os.path.exists(cell_path):
        return {}
    in_block = False
    for raw in open(cell_path, "r", encoding="utf-8", errors="ignore"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Exact block-name match: startswith would also swallow
        # POSITIONS_FRAC_PRODUCT / _INTERMEDIATE (NEB cells) and double-count.
        tokens = line.upper().split()
        if len(tokens) >= 2 and tokens[1] in ("POSITIONS_FRAC", "POSITIONS_ABS"):
            if tokens[0] == "%BLOCK":
                in_block = True
                continue
            if tokens[0] == "%ENDBLOCK":
                in_block = False
                continue
        if in_block:
            parts = line.split()
            if parts:
                counts[parts[0]] += 1
    return dict(counts)

EXCLUDE_DIR_PATTERNS = ("phonon", "disp-", "ase_env", "backup")

def find_castep_files(root: str) -> List[str]:
    out = []
    for dp, dirs, files in os.walk(root):
        # prune excluded subtrees in-place so os.walk skips them
        dirs[:] = [d for d in dirs
                   if not any(pat in d.lower() for pat in EXCLUDE_DIR_PATTERNS)]
        for fn in files:
            if fn.endswith(".castep"):
                out.append(os.path.join(dp, fn))
    return sorted(out)

def classify_system(dir_name: str, cast_name: str, full_dir: str,
                    parent_names: List[str], host_element: str,
                    sub_elements: List[str], reference_root: str,
                    ) -> Tuple[str, Optional[str]]:
    d = dir_name.lower()
    c = cast_name.lower()
    parent_l = [p.lower() for p in parent_names]
    ref_elements = sub_elements + [host_element]
    # substitution systems: <El>_sub in directory or seedname
    for el in sub_elements:
        if el.lower() + "_sub" in d or el.lower() + "_sub" in c:
            return ("substitution", el)
    # parent / host
    if d in parent_l or any(p + "_parent" in d for p in parent_l) \
            or any(c.startswith(p) for p in parent_l):
        return ("parent", None)
    # elemental references under <reference_root>/<Element>
    for el in ref_elements:
        marker = os.sep + reference_root + os.sep + el
        if marker.lower() in (full_dir + os.sep).lower():
            return ("reference", el)
        if d == el.lower():
            return ("reference", el)
    # fallback by exact seedname
    for el in ref_elements:
        if c == el.lower():
            return ("reference", el)
    return ("other", None)

def main():
    ap = argparse.ArgumentParser(
        description="Extract CASTEP final energies and compute substitution energies.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="E_sub(M) = E(sub_M) - E(parent) - mu_M + mu_host")
    ap.add_argument("root", nargs="?", default=".",
                    help="directory tree to scan (default: .)")
    ap.add_argument("--parent-names", default="FeS2,FeS2_parent,parent",
                    help="comma-separated directory/seedname markers for the host "
                         "(default: FeS2,FeS2_parent,parent)")
    ap.add_argument("--host-element", default="Fe",
                    help="element substituted out of the host (default: Fe)")
    ap.add_argument("--sub-elements", default="Mn,Co,Ni,Cr",
                    help="comma-separated substituting elements; directories must be "
                         "named <El>_sub (default: Mn,Co,Ni,Cr)")
    ap.add_argument("--reference-root", default="singlepoint",
                    help="directory containing elemental references as "
                         "<reference-root>/<Element> (default: singlepoint)")
    args = ap.parse_args()

    parent_names = [s.strip() for s in args.parent_names.split(",") if s.strip()]
    sub_elements = [s.strip().capitalize() for s in args.sub_elements.split(",") if s.strip()]
    host = args.host_element.strip().capitalize()

    cast_files = find_castep_files(args.root)
    if not cast_files:
        print("No .castep files found.")
        raise SystemExit(1)

    records = []
    parent_energy = None
    mu: Dict[str, float] = {}

    # pass 1: collect
    for cp in cast_files:
        dp = os.path.dirname(cp)
        dir_name = os.path.basename(dp)
        cast_name = os.path.splitext(os.path.basename(cp))[0]
        system_type, element = classify_system(
            dir_name, cast_name, dp, parent_names, host, sub_elements,
            args.reference_root)
        energy = extract_last_final_energy(cp)
        rec = {
            "directory": dp,
            "castep_file": cp,
            "basename": cast_name,
            "system_type": system_type,
            "element": element or "",
            "final_energy_eV": energy,
            "geometry_completed": geometry_completed(cp),
            "run_started": run_started(cp),
            "species_counts": parse_species_counts_from_cell(
                os.path.join(dp, f"{cast_name}.cell")),
        }
        records.append(rec)
        if system_type == "parent" and energy is not None:
            parent_energy = energy

    # pass 2: reference chemical potentials
    for rec in records:
        if rec["system_type"] != "reference":
            continue
        element, energy = rec["element"], rec["final_energy_eV"]
        if energy is None or not element:
            continue
        n = rec["species_counts"].get(element, 0)
        if n:
            mu[element] = energy / n

    # pass 3: substitution energies
    for rec in records:
        e_sub = None
        if rec["system_type"] == "substitution" and parent_energy is not None \
                and rec["final_energy_eV"] is not None:
            M = rec["element"]
            if M in mu and host in mu:
                e_sub = rec["final_energy_eV"] - parent_energy - mu[M] + mu[host]
        rec["mu_eV_per_atom"] = mu.get(rec["element"]) if rec["system_type"] == "reference" else None
        rec["substitution_energy_eV"] = e_sub

    out_csv = os.path.join(args.root, "parsed_castep_summary.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "system_type","element","basename","directory","final_energy_eV",
            "mu_eV_per_atom","substitution_energy_eV","geometry_completed",
            "run_started","species_counts"
        ])
        for rec in records:
            w.writerow([
                rec["system_type"], rec["element"], rec["basename"], rec["directory"],
                rec["final_energy_eV"], rec["mu_eV_per_atom"], rec["substitution_energy_eV"],
                rec["geometry_completed"], rec["run_started"], str(rec["species_counts"])
            ])

    print(f"Saved summary to: {out_csv}")
    print()
    print("Reference chemical potentials (eV/atom):")
    if mu:
        for k in sorted(mu):
            print(f"  {k}: {mu[k]:.12f}")
    else:
        print("  None found")
    print()
    print("Substitution energies (eV):")
    found = False
    for rec in records:
        if rec["system_type"] == "substitution":
            found = True
            print(f"  {rec['element'] or rec['basename']}: {rec['substitution_energy_eV']}")
    if not found:
        print("  No substitution systems found")

if __name__ == "__main__":
    main()
