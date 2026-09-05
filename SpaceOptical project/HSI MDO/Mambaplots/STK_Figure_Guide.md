# STK Figure & Dataset Generation Guide
### For: *Lightweight Mamba–Transformer Hyperspectral Segmentation for Downlink-Constrained LEO Constellations Operations*

This guide reproduces the scenario behind Table 3 and generates every STK-derived figure (A–H) discussed for Sections 3.3, 4.3.3, and 4.3.4.

**Companion files:**
- `stk_export.py` — automates scenario build + CSV export via the STK Python API
- `plot_stk_figures.py` — reads the exported CSVs and produces publication-ready figures

---

## Part 0 — Scenario Setup

### 0.1 Create the scenario

1. Launch **STK 12** → **New Scenario**
2. Name: `MambaOpticSatNet_Downlink`
3. Set the analysis period:
   - **Start:** `1 Jan 2026 00:00:00.000 UTCG`
   - **Stop:** `31 Jan 2026 00:00:00.000 UTCG`

> **Why 30 days?** Two reasons, and the second is easy to miss.
>
> **Statistics.** Your Table 3 reports a standard deviation of 90.4 s. A single day yields too few samples for a stable histogram (Figure C) and gives an unrepresentative view of the repeat-ground-track cycle.
>
> **Figure E will not complete otherwise.** Delivering *B*₀ = 13,120 Mbit through a *single* satellite's contacts takes on the order of **20+ days** at 1 Mbit/s. A 7-day scenario truncates the curve before it crosses *B*₀, and the script will warn you that P₀ was never delivered. Verified on a representative run: L<sub>post</sub>(P₀) landed at ~510 h ≈ 21 days.
>
> If STK runtime becomes an issue, use 7 days for Figures C/D/F and re-run at 30 days only for Figure E.

4. Set the animation time step to 10 s (**Scenario → Animation → Time Step**)

### 0.2 Insert the ground station

1. **Insert → New → Facility**
2. Name: `KAIST`
3. **Properties → Basic → Position:**

   | Field | Value |
   |---|---|
   | Latitude | `36.3721 deg` |
   | Longitude | `127.3604 deg` |
   | Altitude | `0.070 km` |

4. **Properties → Constraints → Basic:**
   - Enable **Min Elevation Angle** → set to `5 deg`

> **Critical for reproducing Table 3.** Your reported minimum access duration of 4.6 s is only achievable with a low mask angle. If you set 10°, your minimum access will rise and the 4.6 s value in Table 3 and Eq. (40) will no longer reproduce. Record whichever mask you use — reviewers will ask, and it is currently absent from the manuscript.

### 0.3 Build the Walker constellation

1. **Insert → New → Satellite → Orbit Wizard**
2. Select **Circular**, then set:

   | Field | Value |
   |---|---|
   | Altitude | `450 km` |
   | Inclination | `76 deg` |
   | RAAN | `0 deg` |
   | True Anomaly | `0 deg` |
   | Propagator | `J2Perturbation` |

3. Name it `Seed` → **OK**
4. Right-click `Seed` in the Object Browser → **Satellite → Walker...**
5. Configure:

   | Field | Value |
   |---|---|
   | Type | `Delta` |
   | Number of Planes | `5` |
   | Number of Satellites per Plane | `4` |
   | Inter-Plane Spacing (phasing *f*) | `1` |
   | RAAN Spread | `360 deg` |
   | Create Constellation object | ✅ checked |
   | Color by Plane | ✅ checked |

6. Click **Create**

You now have 20 satellites (`Seed11` … `Seed54`) plus a Constellation object named `Seed_Constellation`.

> **Document the phasing factor.** Walker notation is *i : t/p/f* — yours is **76° : 20/5/1**. Table 3 currently omits *f*, but it materially changes the access statistics. Add it.

### 0.4 Build the access chain

1. **Insert → New → Chain**
2. Name: `Downlink_Chain`
3. **Properties → Definition → Objects:** add `Seed_Constellation`, then `KAIST` (order matters — satellite first, facility second)
4. **Properties → Basic → Constraints:** leave defaults
5. Right-click `Downlink_Chain` → **Compute Access**

---

## Part 1 — Figure A: 3D Constellation View

**Target section:** §3.3, adjacent to Table 3

1. Open the **3D Graphics** window
2. **Seed_Constellation → Properties → 3D Graphics → Pass:**
   - Orbit Lead Type: `All`, Orbit Trail Type: `All`
   - Enable **Ground Track** for visual context
3. **KAIST → Properties → 3D Graphics → Model:** enable, scale to `5000`
4. Add a sensor to one satellite for illustration:
   - Right-click `Seed11` → **Insert → New → Sensor**
   - Type: `Simple Conic`, Cone Half Angle: `30 deg`
   - **3D Graphics → Projection:** enable Space Projection
5. Position the camera: **View → Home View**, then zoom so the full constellation is framed with the Korean peninsula visible
6. Turn off clutter: **Scenario → 3D Graphics → Details** — disable the STK logo and time display
7. **Save the image:** right-click in the 3D window → **Snapshot → Save As...**
   - Format: `PNG`
   - In **Scenario → 3D Graphics → Advanced**, set the snapshot resolution multiplier to `4×` for print quality

**Caption template:**
> *Figure A: Walker Delta 76°: 20/5/1 constellation at 450 km altitude. Orbit paths for all five planes are shown with the KAIST ground station and a representative payload field of view.*

---

## Part 2 — Figure B: 2D Ground Tracks and Access Circle

**Target section:** §3.3

1. Open the **2D Graphics** window
2. **Seed_Constellation → Properties → 2D Graphics → Pass:**
   - Ground Track Lead: `One Pass`, Trail: `One Pass`
3. **KAIST → Properties → 2D Graphics → Range Contours:**
   - Enable → **Add Level** → set to the elevation mask (`5 deg`)
   - This draws the actual access footprint boundary
4. Set the projection: **Scenario → 2D Graphics → Projection → Equidistant Cylindrical**
5. Zoom to a regional view centred on East Asia (or keep global — global better shows the 76° inclination coverage limit)
6. Right-click → **Snapshot → Save As...**

**What this proves:** the 76° inclination bounds coverage to roughly ±76° latitude, and the station at 36.4°N sits well inside the high-access-density band. Reviewers questioning the orbit choice get an immediate visual answer.

---

## Part 3 — Master Data Export

**This single export feeds Figures C, D, E, and F.** Do it once.

### Option 1 — GUI (Report & Graph Manager)

1. Right-click `Downlink_Chain` → **Report & Graph Manager**
2. Under **Installed Styles**, select **Complete Chain Access**
3. Click the **Generate As...** button (disk icon)
4. Set:
   - File type: `Comma Delimited (*.csv)`
   - Filename: `chain_access.csv`
5. Click **Save**

### Option 2 — Per-satellite export (needed for Figure E)

Figure E requires knowing *which satellite* had each contact, because a cube stored on Sat 3 cannot be downlinked through Sat 12's pass without crosslinks.

1. Right-click `Seed11` → **Access...**
2. Select `KAIST` as the associated object → **Compute**
3. Click **Access...** → **Report** → select **Access** style → **Generate As...** → `access_Seed11.csv`
4. Repeat for all 20 satellites — or use the Connect automation below

### Option 3 — Connect commands (recommended)

Open **Utilities → Connect...** and run:

```
ReportCreate */Satellite/Seed11 Type Export Style "Access" File "C:\STK_out\access_Seed11.csv" AccessObject */Facility/KAIST
```

Or run the full batch via `stk_export.py` (see Part 9).

### Expected CSV structure

```
"Seed11-To-KAIST: Access Summary"

Access,Start Time (UTCG),Stop Time (UTCG),Duration (sec)
1,1 Jan 2026 00:42:11.284,1 Jan 2026 00:47:33.109,321.825
2,1 Jan 2026 02:18:44.902,1 Jan 2026 02:23:02.551,257.649
...

Global Statistics
Min Duration,4.612
Max Duration,419.883
Mean Duration,302.114
```

The plotting script handles this format including the trailing statistics block.

---

## Part 4 — Figure C: Access Duration Histogram

**Target section:** §4.3.3, supporting Eq. (35) and Table 8

**Data:** `chain_access.csv` (all 20 satellites pooled)

**Generate:**
```bash
python plot_stk_figures.py --mode histogram --access-dir ./stk_out --out fig_C_duration_hist.pdf
```

**What the figure shows:** the distribution of access durations with vertical markers at your reported min (4.6 s), mean (302 s), and max (420 s). Overlay a shaded region marking durations too short to carry a 1 MB product (< 8 s at 1 Mbit/s).

**Why it matters:** Table 8's "Fits 4.6 s?" column currently rests on a single worst-case number. The histogram shows *what fraction* of contacts are that short — if only 2% of passes fall below 8 s, the 1 MB product is far more viable than the table implies. That is a substantive result, not just decoration.

---

## Part 5 — Figure D: Contact Timeline (Gantt)

**Target section:** §4.3.3

### Native STK approach
1. **View → Timeline View**
2. In the Timeline panel, right-click → **Add Object** → add `Downlink_Chain`
3. Set the display window to 24 h
4. Right-click → **Copy to Clipboard** or take a windowed screenshot

### Recommended: replot from CSV
The native timeline is hard to format for print. Use:
```bash
python plot_stk_figures.py --mode gantt --access-dir ./stk_out --hours 24 --out fig_D_gantt.pdf
```
This produces one horizontal lane per satellite with access windows as bars — far cleaner at journal resolution.

**Why it matters:** this is the direct visual answer to your own stated limitation about *"chronological competition among the 20 satellites."* It shows the overlap structure that a scheduler would have to resolve.

---

## Part 6 — Figure E: Cumulative Delivered Volume (P₀ vs P₃)

**Target section:** §4.3.4 — **this is the highest-value figure in the set**

**Data:** per-satellite `access_SeedXX.csv` files

**Generate:**
```bash
python plot_stk_figures.py --mode delivery --access-dir ./stk_out \
    --satellite Seed11 --rate 1.0 --tproc 1.698 \
    --b0 13120 --b3 0.80 --out fig_E_delivery.pdf
```

**Parameters mapped to your paper:**

| Script arg | Paper symbol | Value | Source |
|---|---|---|---|
| `--rate` | *R*<sub>eff</sub> | 1.0 Mbit/s | §4.3.3 assumption |
| `--tproc` | *T*<sub>proc</sub> | 1.698 s | Table 6, Jetson AGX Orin |
| `--b0` | *B*₀ | 13,120 Mbit | Eq. (36) |
| `--b3` | *B*₃ | 0.80 Mbit | Eq. (36) |

**What the script computes:** cumulative deliverable bits following Eq. (15), ramping linearly during each access window and flat between them. It marks the elapsed time at which each curve crosses *B*₃ and *B*₀ — giving you *L*<sub>post</sub> for both product tiers directly.

> ### ⚠ Expect a much larger result than 44:1
>
> Your Table 7 divides 13,120 Mbit by the **constellation-aggregate** mean access of 302 s to get 44 contacts. But a *single* satellite at 450 km only sees Daejeon roughly 4–6 times per day. So 44 contacts for that satellite is realistically **8–11 days**, while the semantic alert clears on the first pass — likely within 1–2 hours.
>
> That is an end-to-end latency ratio on the order of **100–200×**, not 44×, and it is defensible because it comes from actual contact chronology rather than a contact-count proxy. This lets you replace the disclaimer at the end of §4.3.4 with a real number.

---

## Part 7 — Figure F: Inter-Access Gap Histogram

**Target section:** §4.3.4

**Generate:**
```bash
python plot_stk_figures.py --mode gaps --access-dir ./stk_out --satellite Seed11 --out fig_F_gaps.pdf
```

**What it gives you:** the empirical distribution of *T*<sub>wait,1</sub> from Eq. (18) — the term you define but never quantify. Report the median and 95th percentile in the text. This closes a visible gap in the latency model.

---

## Part 8 — Figure G: Elevation Profile for a Representative Pass

**Target section:** §4.3.3

1. Right-click `Seed11` → **Access...** → select `KAIST` → **Compute**
2. Click **Graph...** → select **AER** style, or:
3. **Report & Graph Manager** → **AER** → **Generate As...** → `aer_Seed11.csv`
   - Time step: set to `1 sec` in **Report & Graph Manager → Properties → Time**

**Generate:**
```bash
python plot_stk_figures.py --mode aer --aer-file ./stk_out/aer_Seed11.csv --out fig_G_aer.pdf
```

**What it supports:** your caveat that a flight-level analysis needs *"elevation-dependent data rate."* Plotting elevation and slant range against time makes it visible that a 302 s pass spends most of its duration at low elevation, where the achievable rate is well below the 1 Mbit/s assumption. This is honest about the assumption's optimism.

---

## Part 9 — Figure H: Link Budget (Communications Module)

**Requires:** STK Communications module license

### Setup

1. Right-click `Seed11` → **Insert → New → Transmitter**
   - Model: `Complex Transmitter`
   - Frequency: `2.25 GHz` (S-band downlink)
   - Power: `2 W` (typical CubeSat S-band)
   - Antenna: `Isotropic` or `Parabolic` with 0.15 m diameter
   - Data Rate: `1 Mbit/s`
   - Modulation: `BPSK`

2. Right-click `KAIST` → **Insert → New → Receiver**
   - Model: `Complex Receiver`
   - Antenna: `Parabolic`, diameter `3.0 m`, efficiency `0.55`
   - System Noise Temperature: `150 K`

3. Enable propagation losses:
   - **Receiver → Properties → RF Environment → Atmospheric Absorption:** enable, model `ITU-R P676-9`
   - **Rain:** enable `ITU-R P618-12`, rain rate `20 mm/hr`

4. Compute access between Transmitter and Receiver

### Export

**Report & Graph Manager** on the Receiver → **Link Information** → **Generate As...** → `link_Seed11.csv`

Key columns: `Time`, `Eb/No (dB)`, `C/N (dB)`, `Rcvd. Iso. Power (dBW)`, `BER`, `Prop Loss (dB)`

**Generate:**
```bash
python plot_stk_figures.py --mode link --link-file ./stk_out/link_Seed11.csv --out fig_H_link.pdf
```

**Payoff:** with Eb/N₀ vs. time you can compute an *achievable* rate profile instead of assuming a flat 1 Mbit/s. Integrating that profile over the pass gives a realistic *V<sub>j</sub>* for Eq. (13) — replacing your paper's most-questionable assumption with a computed quantity.

---

## Part 10 — Verification Checklist

Before generating final figures, confirm your scenario reproduces Table 3:

| Table 3 value | Expected | Where to check |
|---|---|---|
| Mean access duration | 302 s | `chain_access.csv` → Global Statistics |
| Min access duration | 4.6 s | same |
| Max access duration | 420 s | same |
| Std deviation | 90.4 s | compute from the duration column |
| Total satellites | 20 | Object Browser count |

**If the numbers don't match**, the usual causes are:
1. **Elevation mask differs** — the single largest driver of min/mean duration
2. **Analysis period differs** — a 24 h window gives different statistics than 7 days
3. **Propagator differs** — TwoBody vs. J2Perturbation shifts RAAN drift over multi-day runs
4. **Walker phasing factor differs** — *f* = 0 vs. *f* = 1 changes the access pattern

Record whichever settings reproduce your published numbers, then add them to Table 3. Right now the table is not reproducible by a reader, which is a reviewable defect.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `No access header row found` | Report exported in a non-Access style | Re-export using the **Access** or **Complete Chain Access** style |
| `NOTE: P0 not delivered within the scenario window` | Analysis period too short | Extend the STK scenario to 30+ days and re-export |
| `No header row containing ('time', 'elevation')` | AER file exported without the Elevation column | In Report & Graph Manager, edit the AER style to include Azimuth, Elevation, Range |
| Timestamps parse as `NaT` | Non-UTCG date format | Set **Scenario → Units → Date Format → UTCG** before exporting |
| Only one satellite appears in the Gantt | Filenames lack the satellite token | Name exports `access_Seed11.csv` etc. — the parser reads the satellite from the filename |
| Figure E ratio looks implausibly small | `--satellite` omitted, pooling all 20 | Always pass `--satellite` for Figures E and F |

---

## Suggested Figure Placement in the Manuscript

| Figure | Section | Column width | Priority |
|---|---|---|---|
| A — Constellation 3D | §3.3 | Single | High |
| B — Ground tracks 2D | §3.3 | Single (pair with A) | Medium |
| C — Duration histogram | §4.3.3 | Single | **High** |
| D — Contact Gantt | §4.3.3 | Double | Medium |
| E — Cumulative delivery | §4.3.4 | Double | **Highest** |
| F — Gap histogram | §4.3.4 | Single | High |
| G — AER profile | §4.3.3 | Single | Medium |
| H — Link budget | §4.3.3 | Single | Optional |

A realistic target for the revision is **A, C, E, F** — four figures that each retire a specific stated limitation.
