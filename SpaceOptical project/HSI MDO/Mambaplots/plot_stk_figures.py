#!/usr/bin/env python3
"""
plot_stk_figures.py
===================
Generates publication-ready figures from STK CSV exports for:

  "Lightweight Mamba-Transformer Hyperspectral Segmentation for
   Downlink-Constrained LEO Constellations Operations"

Figures produced
----------------
  histogram : Fig C  - access duration distribution
  gantt     : Fig D  - contact timeline across the constellation
  delivery  : Fig E  - cumulative delivered volume, P0 vs P3
  gaps      : Fig F  - inter-access gap (T_wait) distribution
  aer       : Fig G  - elevation / range profile for one pass
  link      : Fig H  - Eb/No and received power vs time

Usage
-----
  python plot_stk_figures.py --mode histogram --access-dir ./stk_out
  python plot_stk_figures.py --mode delivery  --access-dir ./stk_out --satellite Seed11
  python plot_stk_figures.py --mode all       --access-dir ./stk_out

Requires: numpy, pandas, matplotlib
"""

import argparse
import glob
import os
import re
import sys
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

# ─────────────────────────────────────────────────────────────
# Style: Elsevier CAS-DC compatible
# ─────────────────────────────────────────────────────────────
COL_SINGLE = 3.50   # inches, single column
COL_DOUBLE = 7.16   # inches, full text width

PALETTE = {
    "primary":   "#1f4e79",   # deep blue  - P3 / semantic alert
    "secondary": "#c0392b",   # red        - P0 / raw cube
    "accent":    "#27ae60",   # green      - thresholds
    "neutral":   "#7f8c8d",   # grey       - reference lines
    "fill":      "#5b9bd5",   # light blue - histogram bars
}


def apply_style():
    plt.rcParams.update({
        "font.family":       "serif",
        "font.serif":        ["Times New Roman", "DejaVu Serif", "STIXGeneral"],
        "mathtext.fontset":  "stix",
        "font.size":          8,
        "axes.labelsize":     8,
        "axes.titlesize":     9,
        "xtick.labelsize":    7,
        "ytick.labelsize":    7,
        "legend.fontsize":    7,
        "axes.linewidth":     0.6,
        "grid.linewidth":     0.4,
        "lines.linewidth":    1.1,
        "xtick.major.width":  0.6,
        "ytick.major.width":  0.6,
        "axes.grid":          True,
        "grid.alpha":         0.25,
        "grid.linestyle":     "--",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "figure.dpi":         160,
        "savefig.dpi":        600,
        "savefig.bbox":       "tight",
        "savefig.pad_inches": 0.02,
    })


# ─────────────────────────────────────────────────────────────
# STK CSV parsing
# ─────────────────────────────────────────────────────────────
UTCG_PATTERNS = [
    "%d %b %Y %H:%M:%S.%f",
    "%d %b %Y %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
]


def parse_utcg(s):
    """Parse an STK UTCG timestamp, e.g. '1 Jan 2026 00:42:11.284'."""
    if pd.isna(s):
        return pd.NaT
    s = str(s).strip().strip('"')
    for fmt in UTCG_PATTERNS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return pd.NaT


def load_access_csv(path):
    """
    Read one STK Access / Chain Access CSV export.

    Tolerates STK's quirks: a title line, blank separators, and a trailing
    'Global Statistics' block. Returns a DataFrame with columns
    [start, stop, duration, source].
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        raw = fh.readlines()

    # Locate the header row: contains both 'Start Time' and 'Stop Time'
    header_idx = None
    for i, line in enumerate(raw):
        low = line.lower()
        if "start time" in low and "stop time" in low:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(f"No access header row found in {path}")

    # Collect data rows until a blank line or a non-numeric first field
    rows = []
    header = [c.strip().strip('"') for c in raw[header_idx].split(",")]
    for line in raw[header_idx + 1:]:
        if not line.strip():
            break
        if "global statistics" in line.lower():
            break
        parts = [c.strip().strip('"') for c in line.split(",")]
        if len(parts) < len(header):
            continue
        rows.append(parts[:len(header)])

    if not rows:
        raise ValueError(f"No access data rows parsed from {path}")

    df = pd.DataFrame(rows, columns=header)

    def find_col(*keys):
        for c in df.columns:
            cl = c.lower()
            if all(k in cl for k in keys):
                return c
        return None

    c_start = find_col("start", "time")
    c_stop  = find_col("stop", "time")
    c_dur   = find_col("duration")

    out = pd.DataFrame()
    out["start"] = df[c_start].map(parse_utcg)
    out["stop"]  = df[c_stop].map(parse_utcg)

    if c_dur is not None:
        out["duration"] = pd.to_numeric(df[c_dur], errors="coerce")
    else:
        out["duration"] = (out["stop"] - out["start"]).dt.total_seconds()

    # Fall back to computed duration wherever the column was unparseable
    computed = (out["stop"] - out["start"]).dt.total_seconds()
    out["duration"] = out["duration"].fillna(computed)

    out = out.dropna(subset=["start", "stop", "duration"])
    out = out[out["duration"] > 0].reset_index(drop=True)

    # Tag with the satellite name inferred from the filename
    stem = os.path.splitext(os.path.basename(path))[0]
    m = re.search(r"(Seed\w+|Sat\w+)", stem, flags=re.IGNORECASE)
    out["source"] = m.group(1) if m else stem

    return out


def load_all_access(access_dir, pattern="*.csv", satellite=None):
    """Load and concatenate every access CSV in a directory."""
    files = sorted(glob.glob(os.path.join(access_dir, pattern)))
    files = [f for f in files
             if not any(k in os.path.basename(f).lower()
                        for k in ("aer", "link"))]
    if satellite:
        files = [f for f in files if satellite.lower() in os.path.basename(f).lower()]
    if not files:
        raise FileNotFoundError(
            f"No access CSVs matching '{pattern}' in {access_dir}"
            + (f" for satellite '{satellite}'" if satellite else "")
        )

    frames = []
    for f in files:
        try:
            frames.append(load_access_csv(f))
        except Exception as exc:                       # noqa: BLE001
            print(f"  [skip] {os.path.basename(f)}: {exc}", file=sys.stderr)

    if not frames:
        raise ValueError("No access files could be parsed.")

    df = pd.concat(frames, ignore_index=True).sort_values("start")
    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# Figure C — access duration histogram
# ─────────────────────────────────────────────────────────────
def fig_histogram(df, out, rate_mbps=1.0, product_mb=1.0):
    d = df["duration"].values
    fig, ax = plt.subplots(figsize=(COL_SINGLE, 2.5))

    ax.hist(d, bins=40, color=PALETTE["fill"], edgecolor="white",
            linewidth=0.4, alpha=0.9)

    stats = {
        "Min":  (np.min(d),  PALETTE["secondary"]),
        "Mean": (np.mean(d), PALETTE["primary"]),
        "Max":  (np.max(d),  PALETTE["neutral"]),
    }
    for label, (val, colour) in stats.items():
        ax.axvline(val, color=colour, linestyle="--", linewidth=0.9,
                   label=f"{label} = {val:.1f} s")

    # Shade the region too short to carry the given product
    t_need = product_mb * 8.0 / rate_mbps
    if t_need > np.min(d):
        ax.axvspan(0, t_need, color=PALETTE["secondary"], alpha=0.08)
        ax.text(t_need, ax.get_ylim()[1] * 0.92,
                f"  < {t_need:.1f} s:\n  {product_mb:g} MB won't fit",
                fontsize=6, va="top", color=PALETTE["secondary"])

    ax.set_xlabel("Access duration (s)")
    ax.set_ylabel("Number of contacts")
    ax.legend(frameon=False, loc="upper left")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    fig.savefig(out)
    plt.close(fig)

    frac = float(np.mean(d < t_need)) * 100.0
    print(f"[Fig C] {out}")
    print(f"        n = {len(d)} contacts | mean {np.mean(d):.1f} s | "
          f"std {np.std(d, ddof=1):.1f} s")
    print(f"        {frac:.2f}% of contacts are shorter than {t_need:.1f} s")


# ─────────────────────────────────────────────────────────────
# Figure D — contact timeline (Gantt)
# ─────────────────────────────────────────────────────────────
def fig_gantt(df, out, hours=24):
    t0 = df["start"].min()
    t_end = t0 + pd.Timedelta(hours=hours)
    sub = df[(df["start"] >= t0) & (df["start"] < t_end)].copy()
    sub["h_start"] = (sub["start"] - t0).dt.total_seconds() / 3600.0
    sub["h_dur"]   = sub["duration"] / 3600.0

    sats = sorted(sub["source"].unique())
    ymap = {s: i for i, s in enumerate(sats)}
    cmap = plt.get_cmap("viridis")

    height = max(2.2, 0.16 * len(sats) + 0.9)
    fig, ax = plt.subplots(figsize=(COL_DOUBLE, height))

    for s in sats:
        rows = sub[sub["source"] == s]
        colour = cmap(ymap[s] / max(1, len(sats) - 1))
        ax.barh(y=[ymap[s]] * len(rows), width=rows["h_dur"],
                left=rows["h_start"], height=0.62,
                color=colour, edgecolor="none")

    ax.set_yticks(range(len(sats)))
    ax.set_yticklabels(sats, fontsize=5.5)
    ax.set_xlabel(f"Elapsed time from {t0:%d %b %Y %H:%M} UTC (h)")
    ax.set_ylabel("Satellite")
    ax.set_xlim(0, hours)
    ax.set_ylim(-0.8, len(sats) - 0.2)
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", visible=False)

    fig.savefig(out)
    plt.close(fig)
    print(f"[Fig D] {out}")
    print(f"        {len(sub)} contacts across {len(sats)} satellites "
          f"in {hours} h")


# ─────────────────────────────────────────────────────────────
# Figure E — cumulative delivered volume, P0 vs P3
# ─────────────────────────────────────────────────────────────
def build_delivery_curve(access, t0, rate_mbps):
    """
    Piecewise-linear cumulative delivered volume (Mbit) vs elapsed hours.
    Ramps during each contact, flat between contacts. Implements Eq. (15).
    """
    usable = access[access["start"] >= t0].sort_values("start")
    t_h, cum_mbit = [0.0], [0.0]
    total = 0.0
    for _, r in usable.iterrows():
        h_start = (r["start"] - t0).total_seconds() / 3600.0
        h_stop  = (r["stop"]  - t0).total_seconds() / 3600.0
        t_h.append(h_start);  cum_mbit.append(total)          # flat until contact
        total += rate_mbps * r["duration"]
        t_h.append(h_stop);   cum_mbit.append(total)          # ramp through contact
    return np.array(t_h), np.array(cum_mbit)


def crossing_time(t_h, cum, threshold):
    """Elapsed hours at which the cumulative curve first reaches `threshold`."""
    idx = np.argmax(cum >= threshold)
    if cum[idx] < threshold:
        return None                                # never delivered in this window
    if idx == 0:
        return float(t_h[0])
    x0, x1 = t_h[idx - 1], t_h[idx]
    y0, y1 = cum[idx - 1], cum[idx]
    if y1 == y0:
        return float(x1)
    return float(x0 + (threshold - y0) * (x1 - x0) / (y1 - y0))


def fig_delivery(access, out, rate_mbps=1.0, tproc_s=1.698,
                 b0_mbit=13120.0, b3_mbit=0.80, acq_offset_h=0.0,
                 scenario_start=None):
    # The acquisition epoch is referenced to SCENARIO start, not to this
    # satellite's first contact — otherwise pass #1 is silently skipped.
    ref = scenario_start if scenario_start is not None else access["start"].min()
    t0 = ref + pd.Timedelta(hours=acq_offset_h) + pd.Timedelta(seconds=tproc_s)
    t_h, cum = build_delivery_curve(access, t0, rate_mbps)

    if len(t_h) < 3:
        raise ValueError("Not enough contacts after the acquisition epoch.")

    t3 = crossing_time(t_h, cum, b3_mbit)
    t0_cross = crossing_time(t_h, cum, b0_mbit)

    fig, ax = plt.subplots(figsize=(COL_DOUBLE, 3.0))
    ax.plot(t_h, cum, color=PALETTE["primary"], linewidth=1.2,
            label="Cumulative deliverable volume")

    ax.axhline(b3_mbit, color=PALETTE["accent"], linestyle="--", linewidth=0.9)
    ax.axhline(b0_mbit, color=PALETTE["secondary"], linestyle="--", linewidth=0.9)

    # Threshold labels: left-anchored, just above each line, to keep clear
    # of the curve and the legend
    x_lab = t_h[-1] * 0.015
    ax.text(x_lab, b3_mbit * 1.35,
            r"$B_3$ = %.2f Mbit  (semantic alert)" % b3_mbit,
            ha="left", va="bottom", fontsize=6.5, color=PALETTE["accent"])
    ax.text(x_lab, b0_mbit * 1.35,
            r"$B_0$ = %.0f Mbit  (raw cube)" % b0_mbit,
            ha="left", va="bottom", fontsize=6.5, color=PALETTE["secondary"])

    if t3 is not None:
        ax.plot([t3], [b3_mbit], "o", color=PALETTE["accent"], ms=4, zorder=5)
        ax.annotate(f"$L_{{post}}(P_3)$ = {t3:.2f} h",
                    xy=(t3, b3_mbit), xytext=(t3 + t_h[-1] * 0.08, b3_mbit * 25),
                    fontsize=6.5, color=PALETTE["accent"],
                    arrowprops=dict(arrowstyle="->", lw=0.6,
                                    color=PALETTE["accent"]))
    if t0_cross is not None:
        ax.plot([t0_cross], [b0_mbit], "o", color=PALETTE["secondary"],
                ms=4, zorder=5)
        ax.annotate(f"$L_{{post}}(P_0)$ = {t0_cross:.1f} h",
                    xy=(t0_cross, b0_mbit),
                    xytext=(t0_cross * 0.55, b0_mbit * 0.30),
                    fontsize=6.5, color=PALETTE["secondary"],
                    arrowprops=dict(arrowstyle="->", lw=0.6,
                                    color=PALETTE["secondary"]))

    ax.set_yscale("log")
    ax.set_xlabel("Elapsed time since acquisition (h)")
    ax.set_ylabel("Cumulative deliverable volume (Mbit)")
    ax.set_xlim(0, t_h[-1])
    # Headroom above B_0 so its label is not clipped by the axes frame
    ax.set_ylim(b3_mbit * 0.35, max(cum.max(), b0_mbit) * 6)
    ax.legend(frameon=False, loc="center right")

    fig.savefig(out)
    plt.close(fig)

    print(f"[Fig E] {out}")
    print(f"        R_eff = {rate_mbps} Mbit/s | T_proc = {tproc_s} s")
    if t3 is not None:
        print(f"        L_post(P3) = {t3:.3f} h ({t3*60:.1f} min)")
    if t0_cross is not None:
        print(f"        L_post(P0) = {t0_cross:.2f} h ({t0_cross/24:.2f} days)")
    if t3 and t0_cross:
        print(f"        >>> End-to-end latency ratio = {t0_cross/t3:.1f}x")
    else:
        print("        NOTE: P0 not delivered within the scenario window - "
              "extend the STK analysis period.")


# ─────────────────────────────────────────────────────────────
# Figure F — inter-access gap distribution
# ─────────────────────────────────────────────────────────────
def fig_gaps(access, out):
    a = access.sort_values("start").reset_index(drop=True)
    gaps_min = (a["start"].shift(-1) - a["stop"]).dt.total_seconds()[:-1] / 60.0
    gaps_min = gaps_min[gaps_min > 0].values

    fig, ax = plt.subplots(figsize=(COL_SINGLE, 2.5))
    ax.hist(gaps_min, bins=35, color=PALETTE["fill"],
            edgecolor="white", linewidth=0.4, alpha=0.9)

    med = float(np.median(gaps_min))
    p95 = float(np.percentile(gaps_min, 95))
    ax.axvline(med, color=PALETTE["primary"], linestyle="--", linewidth=0.9,
               label=f"Median = {med:.1f} min")
    ax.axvline(p95, color=PALETTE["secondary"], linestyle="--", linewidth=0.9,
               label=f"95th pct = {p95:.1f} min")

    ax.set_xlabel(r"Inter-access gap $T_{wait,1}$ (min)")
    ax.set_ylabel("Count")
    ax.legend(frameon=False)

    fig.savefig(out)
    plt.close(fig)
    print(f"[Fig F] {out}")
    print(f"        median {med:.1f} min | mean {np.mean(gaps_min):.1f} min | "
          f"p95 {p95:.1f} min | max {np.max(gaps_min):.1f} min")


# ─────────────────────────────────────────────────────────────
# Timeseries readers (AER / Link) — skip STK's title preamble
# ─────────────────────────────────────────────────────────────
def load_timeseries_csv(path, required=("time",)):
    """
    Read an STK time-series export (AER, Link Information, etc.).

    STK prefixes these files with a quoted title line and a blank line
    before the real header, so locate the header by looking for the row
    that contains all `required` keywords.
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        raw = fh.readlines()

    header_idx = None
    for i, line in enumerate(raw):
        low = line.lower()
        if "," in line and all(k in low for k in required):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError(
            f"No header row containing {required} found in {path}")

    df = pd.read_csv(path, skiprows=header_idx, engine="python",
                     on_bad_lines="skip")
    df.columns = [str(c).strip().strip('"') for c in df.columns]
    return df


def fig_aer(path, out):
    df = load_timeseries_csv(path, required=("time", "elevation"))

    def col(*keys):
        for c in df.columns:
            if all(k in c.lower() for k in keys):
                return c
        return None

    c_time = col("time")
    c_el   = col("elevation")
    c_rng  = col("range")
    if c_time is None or c_el is None:
        raise ValueError(f"AER file missing Time/Elevation columns: {list(df.columns)}")

    t = df[c_time].map(parse_utcg)
    el = pd.to_numeric(df[c_el], errors="coerce")
    ok = t.notna() & el.notna()
    t, el = t[ok], el[ok]
    t_min = (t - t.iloc[0]).dt.total_seconds() / 60.0

    fig, ax = plt.subplots(figsize=(COL_SINGLE, 2.4))
    ax.plot(t_min, el, color=PALETTE["primary"], label="Elevation")
    ax.axhline(5, color=PALETTE["neutral"], linestyle=":", linewidth=0.8)
    ax.text(t_min.iloc[0], 6, "5° mask", fontsize=6,
            color=PALETTE["neutral"])
    ax.set_xlabel("Time from AOS (min)")
    ax.set_ylabel("Elevation (deg)", color=PALETTE["primary"])
    ax.tick_params(axis="y", labelcolor=PALETTE["primary"])

    if c_rng is not None:
        rng = pd.to_numeric(df[c_rng], errors="coerce")[ok]
        ax2 = ax.twinx()
        ax2.plot(t_min, rng, color=PALETTE["secondary"],
                 linestyle="--", linewidth=0.9, label="Slant range")
        ax2.set_ylabel("Slant range (km)", color=PALETTE["secondary"])
        ax2.tick_params(axis="y", labelcolor=PALETTE["secondary"])
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)

    fig.savefig(out)
    plt.close(fig)
    print(f"[Fig G] {out}")
    print(f"        peak elevation {el.max():.1f} deg | "
          f"pass length {t_min.iloc[-1]:.1f} min")


# ─────────────────────────────────────────────────────────────
# Figure H — link budget
# ─────────────────────────────────────────────────────────────
def fig_link(path, out):
    df = load_timeseries_csv(path, required=("time",))

    def col(*keys):
        for c in df.columns:
            if all(k in c.lower() for k in keys):
                return c
        return None

    c_time = col("time")
    c_ebno = col("eb/no") or col("ebno")
    c_pow  = col("rcvd", "power") or col("received", "power")
    if c_time is None:
        raise ValueError("Link file has no Time column.")

    t = df[c_time].map(parse_utcg)
    ok = t.notna()
    t_min = (t[ok] - t[ok].iloc[0]).dt.total_seconds() / 60.0

    fig, ax = plt.subplots(figsize=(COL_SINGLE, 2.4))

    if c_ebno is not None:
        ebno = pd.to_numeric(df[c_ebno], errors="coerce")[ok]
        ax.plot(t_min, ebno, color=PALETTE["primary"], label=r"$E_b/N_0$")
        ax.axhline(9.6, color=PALETTE["secondary"], linestyle=":",
                   linewidth=0.8)
        ax.text(t_min.iloc[0], 10.1, "BPSK BER $10^{-5}$ threshold",
                fontsize=5.5, color=PALETTE["secondary"])
        ax.set_ylabel(r"$E_b/N_0$ (dB)", color=PALETTE["primary"])
        ax.tick_params(axis="y", labelcolor=PALETTE["primary"])

    if c_pow is not None:
        p = pd.to_numeric(df[c_pow], errors="coerce")[ok]
        ax2 = ax.twinx()
        ax2.plot(t_min, p, color=PALETTE["neutral"], linestyle="--",
                 linewidth=0.9)
        ax2.set_ylabel("Rcvd. iso. power (dBW)", color=PALETTE["neutral"])
        ax2.tick_params(axis="y", labelcolor=PALETTE["neutral"])
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)

    ax.set_xlabel("Time from AOS (min)")
    fig.savefig(out)
    plt.close(fig)
    print(f"[Fig H] {out}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="Generate STK-derived figures for the Mamba-OpticSatNet paper.")
    p.add_argument("--mode", required=True,
                   choices=["histogram", "gantt", "delivery", "gaps",
                            "aer", "link", "all"])
    p.add_argument("--access-dir", default="./stk_out",
                   help="Directory holding the exported access CSVs")
    p.add_argument("--satellite", default=None,
                   help="Restrict to one satellite, e.g. Seed11 (required for delivery/gaps)")
    p.add_argument("--aer-file",  default=None)
    p.add_argument("--link-file", default=None)
    p.add_argument("--out", default=None, help="Output filename (PDF or PNG)")
    p.add_argument("--outdir", default="./figures")

    # Paper parameters
    p.add_argument("--rate",  type=float, default=1.0,     help="R_eff, Mbit/s")
    p.add_argument("--tproc", type=float, default=1.698,   help="T_proc, s")
    p.add_argument("--b0",    type=float, default=13120.0, help="B_0, Mbit")
    p.add_argument("--b3",    type=float, default=0.80,    help="B_3, Mbit")
    p.add_argument("--hours", type=float, default=24.0,    help="Gantt window, h")
    p.add_argument("--acq-offset", type=float, default=0.0,
                   help="Acquisition epoch offset from scenario start, h")
    p.add_argument("--product-mb", type=float, default=1.0,
                   help="Product size used for the histogram shading, MB")

    a = p.parse_args()
    apply_style()
    os.makedirs(a.outdir, exist_ok=True)

    def path_for(default_name):
        return a.out if a.out else os.path.join(a.outdir, default_name)

    modes = (["histogram", "gantt", "delivery", "gaps"]
             if a.mode == "all" else [a.mode])

    access_all = None
    if any(m in modes for m in ("histogram", "gantt", "delivery", "gaps")):
        access_all = load_all_access(a.access_dir)
        print(f"Loaded {len(access_all)} access windows from "
              f"{access_all['source'].nunique()} object(s)\n")

    for m in modes:
        try:
            if m == "histogram":
                fig_histogram(access_all, path_for("fig_C_duration_hist.pdf"),
                              rate_mbps=a.rate, product_mb=a.product_mb)
            elif m == "gantt":
                fig_gantt(access_all, path_for("fig_D_gantt.pdf"), hours=a.hours)
            elif m in ("delivery", "gaps"):
                sub = access_all
                if a.satellite:
                    sub = access_all[access_all["source"].str.lower()
                                     == a.satellite.lower()]
                    if sub.empty:
                        raise ValueError(
                            f"No contacts for satellite '{a.satellite}'. "
                            f"Available: {sorted(access_all['source'].unique())}")
                elif access_all["source"].nunique() > 1:
                    print(f"  [warn] --satellite not set; pooling all "
                          f"{access_all['source'].nunique()} objects. For "
                          f"Fig E this overstates a single spacecraft's capacity.",
                          file=sys.stderr)
                if m == "delivery":
                    fig_delivery(sub, path_for("fig_E_delivery.pdf"),
                                 rate_mbps=a.rate, tproc_s=a.tproc,
                                 b0_mbit=a.b0, b3_mbit=a.b3,
                                 acq_offset_h=a.acq_offset,
                                 scenario_start=access_all["start"].min())
                else:
                    fig_gaps(sub, path_for("fig_F_gaps.pdf"))
            elif m == "aer":
                if not a.aer_file:
                    raise ValueError("--aer-file is required for mode 'aer'")
                fig_aer(a.aer_file, path_for("fig_G_aer.pdf"))
            elif m == "link":
                if not a.link_file:
                    raise ValueError("--link-file is required for mode 'link'")
                fig_link(a.link_file, path_for("fig_H_link.pdf"))
        except Exception as exc:                        # noqa: BLE001
            print(f"[error] mode '{m}': {exc}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
