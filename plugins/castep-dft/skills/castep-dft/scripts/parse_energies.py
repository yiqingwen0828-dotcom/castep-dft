#!/usr/bin/env python3
"""
Parse CASTEP .castep files, extract final energies, and compute substitution energies.

Default assumptions:
- parent directory name: FeS2 or FeS2_parent or parent
- substitution directories named like Co_sub, Ni_sub, Cr_sub, Mn_sub
- reference metal directories in singlepoint/<Element>, e.g. singlepoint/Fe

Substitution energy formula:
E_sub(M) = E(sub_M) - E(parent) - mu_M + mu_Fe

where mu_X = E(reference bulk X) / N_X_in_reference_cell
"""
from __future__ import annotations
import csv
import os
import re
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

FINAL_ENERGY_RE = re.compile(r"Final energy,\s*E\s*=\s*([-\d\.Ee+]+)")
GEOM_DONE_RE = re.compile(r"Geometry optimization completed successfully", re.I)
RUN_STARTED_RE = re.compile(r"Run started:", re.I)

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def extract_last_final_energy(castep_path: str) -> Optional[float]:
    text = read_text(castep_path)
    vals = FINAL_ENERGY_RE.findall(text)
    if not vals:
        return None
    return float(vals[-1])

def geometry_completed(castep_path: str) -> bool:
    text = read_text(castep_path)
    return bool(GEOM_DONE_RE.search(text))

def run_started(castep_path: str) -> bool:
    text = read_text(castep_path)
    return bool(RUN_STARTED_RE.search(text))

def parse_species_counts_from_cell(cell_path: str) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    if not os.path.exists(cell_path):
        return {}
    in_block = False
    for raw in open(cell_path, "r", encoding="utf-8", errors="ignore"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        u = line.upper()
        if u.startswith("%BLOCK POSITIONS_FRAC") or u.startswith("%BLOCK POSITIONS_ABS"):
            in_block = True
            continue
        if u.startswith("%ENDBLOCK POSITIONS_FRAC") or u.startswith("%ENDBLOCK POSITIONS_ABS"):
            in_block = False
            continue
        if in_block:
            parts = line.split()
            if parts:
                elem = parts[0]
                counts[elem] += 1
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

def classify_system(dir_name: str, cast_name: str) -> Tuple[str, Optional[str]]:
    d = dir_name.lower()
    c = cast_name.lower()
    # substitution systems
    for el in ["mn", "co", "ni", "cr"]:
        if el + "_sub" in d or el + "_sub" in c:
            return ("substitution", el.capitalize())
    # parent
    if d in {"fes2", "fes2_parent", "parent"} or "fes2_parent" in d or cast_name.lower().startswith("fes2"):
        return ("parent", None)
    # singlepoint references
    for el in ["fe", "co", "ni", "cr", "mn"]:
        if os.sep + "singlepoint" + os.sep + el.capitalize() in (os.path.join("", dir_name) + os.sep):
            return ("reference", el.capitalize())
        if d == el:
            return ("reference", el.capitalize())
    # fallback by exact basename
    for el in ["fe", "co", "ni", "cr", "mn"]:
        if cast_name.lower() == el:
            return ("reference", el.capitalize())
    return ("other", None)

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    cast_files = find_castep_files(root)
    if not cast_files:
        print("No .castep files found.")
        sys.exit(1)

    records = []
    parent_energy = None
    mu = {}

    # pass 1: collect
    for cp in cast_files:
        dp = os.path.dirname(cp)
        dir_name = os.path.basename(dp)
        cast_name = os.path.splitext(os.path.basename(cp))[0]
        system_type, element = classify_system(dir_name, cast_name)
        energy = extract_last_final_energy(cp)
        geom_ok = geometry_completed(cp)
        started = run_started(cp)
        cell_path = os.path.join(dp, f"{cast_name}.cell")
        counts = parse_species_counts_from_cell(cell_path)
        rec = {
            "directory": dp,
            "castep_file": cp,
            "basename": cast_name,
            "system_type": system_type,
            "element": element or "",
            "final_energy_eV": energy,
            "geometry_completed": geom_ok,
            "run_started": started,
            "species_counts": counts,
        }
        records.append(rec)

        if system_type == "parent" and energy is not None:
            parent_energy = energy

    # pass 2: reference chemical potentials
    for rec in records:
        if rec["system_type"] != "reference":
            continue
        element = rec["element"]
        energy = rec["final_energy_eV"]
        counts = rec["species_counts"]
        if energy is None or not element:
            continue
        n = counts.get(element, 0)
        if n:
            mu[element] = energy / n

    # pass 3: substitution energies
    for rec in records:
        e_sub = None
        if rec["system_type"] == "substitution" and parent_energy is not None and rec["final_energy_eV"] is not None:
            M = rec["element"]
            if M in mu and "Fe" in mu:
                e_sub = rec["final_energy_eV"] - parent_energy - mu[M] + mu["Fe"]
        rec["mu_eV_per_atom"] = mu.get(rec["element"], None) if rec["system_type"] == "reference" else None
        rec["substitution_energy_eV"] = e_sub

    out_csv = os.path.join(root, "parsed_castep_summary.csv")
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

    # concise terminal summary
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
