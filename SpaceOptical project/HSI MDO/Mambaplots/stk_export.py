#!/usr/bin/env python3
"""
stk_export.py
=============
Builds the constellation scenario and exports every dataset needed by
`plot_stk_figures.py`, using the STK 12 Python API.

Reproduces Table 3 of:
  "Lightweight Mamba-Transformer Hyperspectral Segmentation for
   Downlink-Constrained LEO Constellations Operations"

Prerequisites
-------------
  * STK 12 installed (Windows, or Linux with STK Engine)
  * pip install agi.stk12

Usage
-----
  python stk_export.py --outdir C:\\STK_out --days 30
  python stk_export.py --outdir ./stk_out --days 7 --no-gui

Notes
-----
Run this ONCE, then use plot_stk_figures.py on the resulting CSVs.
Nothing here depends on the STK GUI being visible; --no-gui uses STK
Engine, which is faster for batch work.
"""

import argparse
import os
import sys

# ─────────────────────────────────────────────────────────────
# Scenario constants — edit these to match your Table 3
# ─────────────────────────────────────────────────────────────
FACILITY_NAME = "KAIST"
FACILITY_LAT  = 36.3721      # deg N
FACILITY_LON  = 127.3604     # deg E
FACILITY_ALT  = 0.070        # km

ALTITUDE_KM   = 450.0
INCLINATION   = 76.0         # deg
N_PLANES      = 5
N_PER_PLANE   = 4
PHASING_F     = 1            # Walker 76 deg : 20/5/1
MIN_ELEV_DEG  = 5.0          # <-- drives min access duration; document it

SCENARIO_START = "1 Jan 2026 00:00:00.000"


def build_and_export(outdir, days, use_gui=True):
    try:
        from agi.stk12.stkobjects import (
            AgEVePropagatorType, AgESTKObjectType, AgEClassicalSizeShape,
            AgEClassicalLocation, AgEOrientationAscNode, AgEAccessConstraints,
        )
        if use_gui:
            from agi.stk12.stkdesktop import STKDesktop
            stk = STKDesktop.StartApplication(visible=True, userControl=True)
            root = stk.Root
        else:
            from agi.stk12.stkengine import STKEngine
            stk = STKEngine.StartApplication(noGraphics=True)
            root = stk.NewObjectRoot()
    except ImportError:
        sys.exit("ERROR: agi.stk12 not found.  Install with:  pip install agi.stk12")

    os.makedirs(outdir, exist_ok=True)

    # ── Scenario ────────────────────────────────────────────
    root.NewScenario("MambaOpticSatNet_Downlink")
    sc = root.CurrentScenario
    sc.SetTimePeriod(SCENARIO_START, f"+{days} days")
    root.UnitPreferences.SetCurrentUnit("DateFormat", "UTCG")
    root.UnitPreferences.SetCurrentUnit("Distance", "km")
    root.Rewind()
    print(f"Scenario created: {days}-day analysis period")

    # ── Ground station ──────────────────────────────────────
    fac = sc.Children.New(AgESTKObjectType.eFacility, FACILITY_NAME)
    fac.Position.AssignGeodetic(FACILITY_LAT, FACILITY_LON, FACILITY_ALT)
    elev = fac.AccessConstraints.AddConstraint(AgEAccessConstraints.eCstrElevationAngle)
    elev.EnableMin = True
    elev.Min = MIN_ELEV_DEG
    print(f"Facility {FACILITY_NAME} at ({FACILITY_LAT}, {FACILITY_LON}), "
          f"{MIN_ELEV_DEG} deg mask")

    # ── Seed satellite ──────────────────────────────────────
    seed = sc.Children.New(AgESTKObjectType.eSatellite, "Seed")
    seed.SetPropagatorType(AgEVePropagatorType.ePropagatorTwoBody)
    prop = seed.Propagator
    prop.Step = 60.0

    orb = prop.InitialState.Representation.ConvertTo(1)   # Classical
    orb.SizeShapeType = AgEClassicalSizeShape.eSizeShapeAltitude
    orb.SizeShape.PerigeeAltitude = ALTITUDE_KM
    orb.SizeShape.ApogeeAltitude  = ALTITUDE_KM
    orb.Orientation.Inclination   = INCLINATION
    orb.Orientation.ArgOfPerigee  = 0.0
    orb.Orientation.AscNodeType   = AgEOrientationAscNode.eAscNodeRAAN
    orb.Orientation.AscNode.Value = 0.0
    orb.LocationType              = AgEClassicalLocation.eLocationTrueAnomaly
    orb.Location.Value            = 0.0

    prop.InitialState.Representation.Assign(orb)
    prop.Propagate()
    print(f"Seed satellite: {ALTITUDE_KM} km circular, {INCLINATION} deg inc")

    # ── Walker constellation ────────────────────────────────
    # Connect is the reliable route for Walker generation.
    root.ExecuteCommand(
        f"Walker */Satellite/Seed Type Delta "
        f"NumPlanes {N_PLANES} NumSatsPerPlane {N_PER_PLANE} "
        f"InterPlanePhaseIncrement {PHASING_F} "
        f"ColorByPlane Yes ConstellationName Seed_Constellation"
    )
    n_total = N_PLANES * N_PER_PLANE
    print(f"Walker {INCLINATION:.0f} deg : {n_total}/{N_PLANES}/{PHASING_F} created")

    # ── Per-satellite access exports (Figures C-F) ──────────
    sat_names = [obj.InstanceName for obj in sc.Children
                 if obj.ClassName == "Satellite" and obj.InstanceName != "Seed"]
    if not sat_names:                       # some STK builds keep the seed name
        sat_names = [obj.InstanceName for obj in sc.Children
                     if obj.ClassName == "Satellite"]

    print(f"\nExporting access reports for {len(sat_names)} satellites...")
    for name in sat_names:
        path = os.path.join(outdir, f"access_{name}.csv")
        root.ExecuteCommand(
            f'ReportCreate */Satellite/{name} Type Export Style "Access" '
            f'File "{path}" AccessObject */Facility/{FACILITY_NAME}'
        )
        print(f"  {os.path.basename(path)}")

    # ── AER export for one representative pass (Figure G) ───
    rep = sat_names[0]
    aer_path = os.path.join(outdir, f"aer_{rep}.csv")
    root.ExecuteCommand(
        f'ReportCreate */Satellite/{rep} Type Export Style "AER" '
        f'File "{aer_path}" AccessObject */Facility/{FACILITY_NAME} '
        f'TimeStep 1.0'
    )
    print(f"\nAER export: {os.path.basename(aer_path)}")

    # ── Chain-level aggregate (optional cross-check) ────────
    try:
        chain = sc.Children.New(AgESTKObjectType.eChain, "Downlink_Chain")
        chain.Objects.Add("*/Constellation/Seed_Constellation")
        chain.Objects.Add(f"*/Facility/{FACILITY_NAME}")
        chain.ComputeAccess()
        chain_path = os.path.join(outdir, "chain_access.csv")
        root.ExecuteCommand(
            f'ReportCreate */Chain/Downlink_Chain Type Export '
            f'Style "Complete Chain Access" File "{chain_path}"'
        )
        print(f"Chain export: {os.path.basename(chain_path)}")
    except Exception as exc:                            # noqa: BLE001
        print(f"  [skip] chain export: {exc}")

    print(f"\nAll exports written to: {os.path.abspath(outdir)}")
    print("\nNext step:")
    print(f"  python plot_stk_figures.py --mode all "
          f"--access-dir {outdir} --satellite {rep}")

    return root


def main():
    p = argparse.ArgumentParser(description="Build STK scenario and export datasets.")
    p.add_argument("--outdir", default="./stk_out")
    p.add_argument("--days", type=int, default=30,
                   help="Analysis period; use 30+ so Figure E completes")
    p.add_argument("--no-gui", action="store_true",
                   help="Use STK Engine headless instead of STK Desktop")
    a = p.parse_args()

    build_and_export(a.outdir, a.days, use_gui=not a.no_gui)


if __name__ == "__main__":
    main()
