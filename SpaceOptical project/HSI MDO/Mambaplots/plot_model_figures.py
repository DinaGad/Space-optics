#!/usr/bin/env python3
"""
plot_model_figures.py
=====================
Model- and mission-side figures for:

  "Lightweight Mamba-Transformer Hyperspectral Segmentation for
   Downlink-Constrained LEO Constellations Operations"

Companion to plot_stk_figures.py (which covers the STK-derived figures).

Modes
-----
  ablation  : Fig I - component ablation, mIoU / C2 IoU with error bars
  confusion : Fig J - row-normalised confusion matrix
  alertsize : Fig K - empirical D_3 distribution, validates Eq. (11)
  gate      : Fig L - adaptive gate activation, validates Eq. (22)-(23)
  latency   : Fig M - L_post breakdown, visualises Eq. (18)
  energy    : Fig N - energy vs latency across Jetson platforms (Table 6)

Usage
-----
  python plot_model_figures.py --mode ablation  --ablation-csv ablation.csv
  python plot_model_figures.py --mode confusion --pred-dir ./preds --gt-dir ./gts
  python plot_model_figures.py --mode alertsize --pred-dir ./preds
  python plot_model_figures.py --mode energy          # uses Table 6 defaults
  python plot_model_figures.py --mode all --pred-dir ./preds --gt-dir ./gts \
                               --ablation-csv ablation.csv

Requires: numpy, pandas, matplotlib, scipy
"""

import argparse
import glob
import json
import os
import sys
import zlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy import ndimage

# ─────────────────────────────────────────────────────────────
# Style — matches plot_stk_figures.py
# ─────────────────────────────────────────────────────────────
COL_SINGLE = 3.50
COL_DOUBLE = 7.16

PALETTE = {
    "primary":   "#1f4e79",
    "secondary": "#c0392b",
    "accent":    "#27ae60",
    "neutral":   "#7f8c8d",
    "fill":      "#5b9bd5",
    "warm":      "#e67e22",
}

CLASS_NAMES = ["C0 Vegetation", "C1 Cropland", "C2 Urban", "C3 Water"]
CLASS_SHORT = ["C0", "C1", "C2", "C3"]
IGNORE_INDEX = 255


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


def load_raster_dir(path, pattern="*.npy"):
    """Load every .npy raster in a directory, sorted by filename."""
    files = sorted(glob.glob(os.path.join(path, pattern)))
    if not files:
        raise FileNotFoundError(f"No files matching '{pattern}' in {path}")
    return files, [np.load(f) for f in files]


# ─────────────────────────────────────────────────────────────
# Figure I — component ablation
# ─────────────────────────────────────────────────────────────
def fig_ablation(csv_path, out):
    """
    Expects a CSV with one row per (config, seed):

        config,seed,mIoU,C2_IoU,params_M,gmacs
        CNN stem only,1,0.812,0.402,0.121,0.031
        CNN + Transformer,1,0.861,0.598,0.455,0.171
        ...

    Only `config`, `seed`, `mIoU` and `C2_IoU` are required.
    """
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]

    required = {"config", "mIoU"}
    if not required.issubset(df.columns):
        raise ValueError(f"Ablation CSV needs columns {required}; got {list(df.columns)}")

    has_c2 = "C2_IoU" in df.columns
    order = list(dict.fromkeys(df["config"]))          # preserve file order

    g = df.groupby("config", sort=False)
    mean_miou = g["mIoU"].mean().reindex(order)
    std_miou  = g["mIoU"].std(ddof=1).reindex(order).fillna(0.0)
    n_seeds   = g["mIoU"].count().reindex(order)

    if has_c2:
        mean_c2 = g["C2_IoU"].mean().reindex(order)
        std_c2  = g["C2_IoU"].std(ddof=1).reindex(order).fillna(0.0)

    x = np.arange(len(order))
    w = 0.38 if has_c2 else 0.55

    fig, ax = plt.subplots(figsize=(COL_DOUBLE, 2.9))

    ax.bar(x - (w / 2 if has_c2 else 0), mean_miou, w,
           yerr=std_miou, capsize=2.5,
           color=PALETTE["primary"], edgecolor="white", linewidth=0.4,
           error_kw=dict(lw=0.7, ecolor="#333333"), label="mIoU")

    if has_c2:
        ax.bar(x + w / 2, mean_c2, w,
               yerr=std_c2, capsize=2.5,
               color=PALETTE["warm"], edgecolor="white", linewidth=0.4,
               error_kw=dict(lw=0.7, ecolor="#333333"), label="C2 Urban IoU")

    # Value labels above each bar
    for xi, (m, s) in enumerate(zip(mean_miou, std_miou)):
        ax.text(xi - (w / 2 if has_c2 else 0), m + s + 0.012, f"{m:.3f}",
                ha="center", fontsize=5.8, color=PALETTE["primary"])
    if has_c2:
        for xi, (m, s) in enumerate(zip(mean_c2, std_c2)):
            ax.text(xi + w / 2, m + s + 0.012, f"{m:.3f}",
                    ha="center", fontsize=5.8, color=PALETTE["warm"])

    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=14, ha="right", fontsize=6.5)
    ax.set_ylabel("IoU")
    ax.set_ylim(0, 1.06)
    ax.legend(frameon=False, loc="lower right", ncol=2)
    ax.grid(axis="x", visible=False)

    fig.savefig(out)
    plt.close(fig)

    print(f"[Fig I] {out}")
    print(f"        {len(order)} configurations, "
          f"{int(n_seeds.min())}-{int(n_seeds.max())} seeds each")
    base, best = mean_miou.iloc[0], mean_miou.iloc[-1]
    print(f"        mIoU gain, first -> last config: "
          f"{base:.3f} -> {best:.3f}  (+{best - base:.3f})")
    if has_c2:
        print(f"        C2 IoU gain: {mean_c2.iloc[0]:.3f} -> "
              f"{mean_c2.iloc[-1]:.3f}  (+{mean_c2.iloc[-1] - mean_c2.iloc[0]:.3f})")
    if int(n_seeds.min()) < 3:
        print("        [warn] fewer than 3 seeds - error bars are not meaningful",
              file=sys.stderr)


# ─────────────────────────────────────────────────────────────
# Figure J — confusion matrix
# ─────────────────────────────────────────────────────────────
def fig_confusion(pred_dir, gt_dir, out, n_classes=4):
    _, preds = load_raster_dir(pred_dir)
    _, gts   = load_raster_dir(gt_dir)
    if len(preds) != len(gts):
        raise ValueError(f"{len(preds)} predictions vs {len(gts)} ground-truth files")

    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for p, g in zip(preds, gts):
        p, g = p.ravel(), g.ravel()
        valid = (g != IGNORE_INDEX) & (g < n_classes) & (p < n_classes)
        np.add.at(cm, (g[valid].astype(int), p[valid].astype(int)), 1)

    row_sums = cm.sum(axis=1, keepdims=True)
    cm_norm = np.divide(cm, row_sums, out=np.zeros_like(cm, float),
                        where=row_sums > 0) * 100.0

    cmap = LinearSegmentedColormap.from_list(
        "paper_blue", ["#ffffff", PALETTE["fill"], PALETTE["primary"]])

    fig, ax = plt.subplots(figsize=(COL_SINGLE, 3.0))
    im = ax.imshow(cm_norm, cmap=cmap, vmin=0, vmax=100, aspect="equal")

    for i in range(n_classes):
        for j in range(n_classes):
            v = cm_norm[i, j]
            ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                    fontsize=6.8,
                    color="white" if v > 55 else "#222222",
                    fontweight="bold" if i == j else "normal")

    ax.set_xticks(range(n_classes)); ax.set_yticks(range(n_classes))
    ax.set_xticklabels(CLASS_SHORT); ax.set_yticklabels(CLASS_SHORT)
    ax.set_xlabel("Predicted class"); ax.set_ylabel("True class")
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, n_classes, 1), minor=True)
    ax.set_yticks(np.arange(-.5, n_classes, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2, linestyle="-")
    ax.tick_params(which="minor", length=0)

    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Row-normalised (%)", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    cb.outline.set_linewidth(0.5)

    fig.savefig(out)
    plt.close(fig)

    print(f"[Fig J] {out}")
    print(f"        {cm.sum():,} valid pixels over {len(preds)} scenes")
    for i in range(n_classes):
        if row_sums[i, 0] == 0:
            continue
        off = [(j, cm_norm[i, j]) for j in range(n_classes) if j != i]
        j_max, v_max = max(off, key=lambda t: t[1])
        print(f"        {CLASS_SHORT[i]} recall {cm_norm[i, i]:5.1f}%  |  "
              f"largest leak -> {CLASS_SHORT[j_max]} ({v_max:.1f}%)")


# ─────────────────────────────────────────────────────────────
# Figure K — empirical semantic-alert size, validates Eq. (11)
# ─────────────────────────────────────────────────────────────
def build_alert_packet(raster, prob=None, min_area_px=8, gsd_m=10.0,
                       n_classes=4, spacecraft="SAT-11", sensor="HSI-32"):
    """
    Extract connected-component ROIs and serialise a semantic alert exactly
    as modelled by Eq. (11): D_3 = D_fixed + sum_i D_ROI,i.

    Returns (packet_dict, n_rois).
    """
    packet = {
        "schema": "MOSN-ALERT/1.0",                 # D_fixed begins
        "sc_id": spacecraft,
        "sensor": sensor,
        "t_acq": "2026-01-01T00:42:11.284Z",
        "t_proc": "2026-01-01T00:42:12.982Z",
        "model": "MambaOpticSatNet-Lite@a3f9c21e",
        "qc_flags": {"cal": "ok", "geo": "ok", "cloud_frac": 0.07},
        "crc32": "00000000",
        "rois": [],                                  # D_ROI,i records follow
    }

    for cls in range(n_classes):
        mask = (raster == cls)
        if not mask.any():
            continue
        lab, n = ndimage.label(mask)
        if n == 0:
            continue
        objs = ndimage.find_objects(lab)
        for idx, sl in enumerate(objs, start=1):
            comp = (lab[sl] == idx)
            area_px = int(comp.sum())
            if area_px < min_area_px:
                continue
            cy, cx = ndimage.center_of_mass(comp)
            cy += sl[0].start
            cx += sl[1].start

            conf = 0.5
            if prob is not None:
                pm = prob[cls][sl][comp]
                conf = float(np.mean(pm))

            packet["rois"].append({
                "cls": cls,
                "area_m2": round(area_px * gsd_m * gsd_m, 1),
                "lat": round(36.3721 + (cy - raster.shape[0] / 2) * 9e-5, 6),
                "lon": round(127.3604 + (cx - raster.shape[1] / 2) * 1.1e-4, 6),
                "bbox": [int(sl[1].start), int(sl[0].start),
                         int(sl[1].stop), int(sl[0].stop)],
                "conf": round(conf, 3),
                "sigma": round(float(np.clip(1.0 - conf, 0.01, 0.5)), 3),
            })

    blob = json.dumps(packet, separators=(",", ":")).encode("utf-8")
    packet["crc32"] = format(zlib.crc32(blob) & 0xFFFFFFFF, "08x")
    return packet, len(packet["rois"])


def fig_alertsize(pred_dir, out, prob_dir=None, min_area_px=8,
                  gsd_m=10.0, assumed_kb=100.0, rate_mbps=1.0,
                  min_access_s=4.6):
    files, rasters = load_raster_dir(pred_dir)

    probs = [None] * len(rasters)
    if prob_dir:
        try:
            _, probs = load_raster_dir(prob_dir)
        except FileNotFoundError:
            print("  [warn] no probability rasters found; using conf=0.5",
                  file=sys.stderr)

    sizes_kb, n_rois, sizes_gz_kb = [], [], []
    for r, p in zip(rasters, probs):
        pkt, n = build_alert_packet(r, prob=p, min_area_px=min_area_px,
                                    gsd_m=gsd_m)
        blob = json.dumps(pkt, separators=(",", ":")).encode("utf-8")
        sizes_kb.append(len(blob) / 1000.0)
        sizes_gz_kb.append(len(zlib.compress(blob, 9)) / 1000.0)
        n_rois.append(n)

    sizes_kb = np.array(sizes_kb)
    sizes_gz_kb = np.array(sizes_gz_kb)
    n_rois = np.array(n_rois)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(COL_DOUBLE, 2.6))

    # Left: size distribution
    lo = min(sizes_gz_kb.min(), sizes_kb.min()) * 0.7
    hi = max(sizes_kb.max(), assumed_kb) * 1.5
    bins = np.logspace(np.log10(lo), np.log10(hi), 40)

    ax1.hist(sizes_gz_kb, bins=bins, color=PALETTE["accent"], edgecolor="white",
             linewidth=0.4, alpha=0.85, label="Deflate-compressed")
    ax1.hist(sizes_kb, bins=bins, color=PALETTE["fill"], edgecolor="white",
             linewidth=0.4, alpha=0.85, label="Uncompressed JSON")
    ax1.axvline(assumed_kb, color=PALETTE["secondary"], linestyle="--",
                linewidth=1.0, label=f"Assumed {assumed_kb:.0f} kB")
    ax1.set_xscale("log")
    ax1.set_xlim(lo, hi)

    ceiling_kb = rate_mbps * min_access_s * 1000.0 / 8.0
    if ceiling_kb < max(sizes_kb.max(), assumed_kb) * 1.4:
        ax1.axvline(ceiling_kb, color=PALETTE["neutral"], linestyle=":",
                    linewidth=1.0,
                    label=f"{min_access_s:g} s ceiling ({ceiling_kb:.0f} kB)")

    ax1.set_xlabel(r"Semantic alert size $D_3$ (kB, log scale)")
    ax1.set_ylabel("Number of scenes")
    ax1.legend(frameon=False, fontsize=6, loc="upper left")

    # Right: Eq. (11) linearity check
    ax2.scatter(n_rois, sizes_kb, s=9, color=PALETTE["primary"],
                alpha=0.55, edgecolors="none")
    if len(n_rois) > 2 and n_rois.std() > 0:
        slope, intercept = np.polyfit(n_rois, sizes_kb, 1)
        xs = np.linspace(0, n_rois.max() * 1.05, 50)
        ax2.plot(xs, slope * xs + intercept, color=PALETTE["secondary"],
                 linewidth=1.0,
                 label=(r"$D_3 = %.3f + %.4f\,n$" % (intercept, slope)))
        r = np.corrcoef(n_rois, sizes_kb)[0, 1]
        ax2.text(0.04, 0.92, f"$R^2$ = {r**2:.4f}", transform=ax2.transAxes,
                 fontsize=6.5)
        ax2.legend(frameon=False, fontsize=6, loc="lower right")

    ax2.set_xlabel("Number of detected ROIs, $n$")
    ax2.set_ylabel(r"$D_3$ (kB)")

    fig.tight_layout(w_pad=1.6)
    fig.savefig(out)
    plt.close(fig)

    print(f"[Fig K] {out}")
    print(f"        {len(sizes_kb)} scenes | ROIs/scene: "
          f"median {np.median(n_rois):.0f}, max {n_rois.max()}")
    print(f"        D_3 uncompressed: median {np.median(sizes_kb):.2f} kB, "
          f"p95 {np.percentile(sizes_kb, 95):.2f} kB, max {sizes_kb.max():.2f} kB")
    print(f"        D_3 compressed  : median {np.median(sizes_gz_kb):.2f} kB, "
          f"p95 {np.percentile(sizes_gz_kb, 95):.2f} kB")
    over = float(np.mean(sizes_kb > assumed_kb)) * 100.0
    print(f"        {over:.1f}% of scenes exceed the assumed {assumed_kb:.0f} kB")
    if intercept_note := (np.median(sizes_kb) < assumed_kb * 0.5):
        print(f"        NOTE: measured median is well below the {assumed_kb:.0f} kB "
              f"assumption - your reported reduction factor is conservative.")


# ─────────────────────────────────────────────────────────────
# Figure L — adaptive gate activation, validates Eq. (22)-(23)
# ─────────────────────────────────────────────────────────────
def fig_gate(gate_path, out, raster_path=None):
    """
    `gate_path` is a .npy of the sigmoid gate tensor G from Eq. (22),
    shaped (H_f, W_f, D) or (N_tokens, D).
    G -> 1 favours the Transformer branch; G -> 0 favours the SSM branch.
    """
    G = np.load(gate_path)
    if G.ndim == 2:                                   # (N, D) -> square grid
        n, d = G.shape
        side = int(np.sqrt(n))
        if side * side == n:
            G = G.reshape(side, side, d)
    if G.ndim != 3:
        raise ValueError(f"Gate tensor must be (H,W,D) or (N,D); got {G.shape}")

    flat = G.ravel()
    spatial = G.mean(axis=2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(COL_DOUBLE, 2.5))

    ax1.hist(flat, bins=60, color=PALETTE["fill"], edgecolor="white",
             linewidth=0.3, alpha=0.9)
    mu = float(flat.mean())
    ax1.axvline(0.5, color=PALETTE["neutral"], linestyle=":", linewidth=0.9)
    ax1.axvline(mu, color=PALETTE["secondary"], linestyle="--", linewidth=1.0,
                label=f"mean = {mu:.3f}")
    ax1.set_xlabel(r"Gate value $\mathcal{G}$")
    ax1.set_ylabel("Count")
    ax1.set_xlim(0, 1)
    ax1.legend(frameon=False, fontsize=6.5)
    ax1.text(0.02, 0.94, "SSM branch", transform=ax1.transAxes,
             fontsize=6, color=PALETTE["neutral"])
    ax1.text(0.98, 0.94, "Transformer branch", transform=ax1.transAxes,
             fontsize=6, ha="right", color=PALETTE["neutral"])

    im = ax2.imshow(spatial, cmap="RdBu_r", vmin=0, vmax=1)
    ax2.set_title(r"Token-wise mean $\mathcal{G}$", fontsize=7.5)
    ax2.set_xticks([]); ax2.set_yticks([]); ax2.grid(False)
    cb = fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cb.ax.tick_params(labelsize=6)
    cb.outline.set_linewidth(0.5)

    fig.tight_layout(w_pad=1.4)
    fig.savefig(out)
    plt.close(fig)

    sd = float(flat.std())
    print(f"[Fig L] {out}")
    print(f"        mean {mu:.4f} | std {sd:.4f} | "
          f"range [{flat.min():.3f}, {flat.max():.3f}]")
    print(f"        spatial variation of token-mean: std {spatial.std():.4f}")
    if sd < 0.05:
        print("        WARNING: gate is near-constant. A fixed weighted sum "
              "would perform equivalently - report this honestly.",
              file=sys.stderr)
    else:
        print("        Gate is genuinely adaptive - supports the Eq. (23) claim.")


# ─────────────────────────────────────────────────────────────
# Figure M — L_post breakdown, visualises Eq. (18)
# ─────────────────────────────────────────────────────────────
def fig_latency(out, tproc_s=1.698, twait_p0_s=None, twait_p3_s=None,
                b0_mbit=13120.0, b3_mbit=0.80, rate_mbps=1.0,
                tground_s=30.0):
    # Defaults reflect the STK-derived chronology if not supplied
    if twait_p3_s is None:
        twait_p3_s = 3600.0                     # ~1 h to next usable contact
    if twait_p0_s is None:
        twait_p0_s = 21 * 24 * 3600.0 - b0_mbit / rate_mbps

    comps = ["$T_{proc}$", "$T_{wait,1}$", "$T_{delivery}$", "$T_{ground}$"]
    p0 = [tproc_s, twait_p0_s, b0_mbit / rate_mbps, tground_s]
    p3 = [tproc_s, twait_p3_s, b3_mbit / rate_mbps, tground_s]

    colours = [PALETTE["accent"], PALETTE["neutral"],
               PALETTE["secondary"], PALETTE["warm"]]

    fig, ax = plt.subplots(figsize=(COL_SINGLE, 2.7))
    labels = ["$P_0$\n(raw cube)", "$P_3$\n(semantic alert)"]
    x = np.arange(2)
    bottom = np.zeros(2)

    for k, (name, colour) in enumerate(zip(comps, colours)):
        vals = np.array([p0[k], p3[k]])
        ax.bar(x, vals, 0.5, bottom=bottom, color=colour,
               edgecolor="white", linewidth=0.5, label=name)
        bottom += vals

    for xi, tot in zip(x, bottom):
        ax.text(xi, tot * 1.12,
                f"{tot/3600:.2f} h" if tot < 86400 else f"{tot/86400:.1f} d",
                ha="center", fontsize=6.5, fontweight="bold")

    ax.set_yscale("log")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Contribution to $L_{post}$ (s, log scale)")
    ax.set_ylim(0.1, bottom.max() * 30)          # headroom for value labels
    ax.legend(frameon=False, fontsize=6.2, ncol=4,
              loc="upper center", bbox_to_anchor=(0.5, -0.16),
              handlelength=1.2, columnspacing=1.0)
    ax.grid(axis="x", visible=False)

    fig.savefig(out)
    plt.close(fig)

    print(f"[Fig M] {out}")
    print(f"        L_post(P0) = {bottom[0]/3600:8.2f} h  "
          f"({bottom[0]/86400:.2f} days)")
    print(f"        L_post(P3) = {bottom[1]/3600:8.2f} h")
    print(f"        ratio = {bottom[0]/bottom[1]:.1f}x")
    print(f"        T_proc is {tproc_s/bottom[1]*100:.3f}% of L_post(P3) "
          f"- onboard inference is not the bottleneck")


# ─────────────────────────────────────────────────────────────
# Figure N — energy vs latency (Table 6)
# ─────────────────────────────────────────────────────────────
TABLE6 = pd.DataFrame({
    "platform":   ["Jetson Xavier NX", "Jetson AGX Xavier",
                   "Jetson Orin NX", "Jetson AGX Orin"],
    "latency_ms": [8826.2, 4753.7, 6620.0, 1697.6],
    "power_w":    [12.50, 28.50, 15.00, 25.00],
    "energy_j":   [110.36, 135.51, 99.30, 42.44],
})


def fig_energy(out, csv_path=None):
    df = pd.read_csv(csv_path) if csv_path else TABLE6.copy()
    df.columns = [c.strip().lower() for c in df.columns]

    fig, ax = plt.subplots(figsize=(COL_SINGLE, 2.6))

    sizes = (df["power_w"] / df["power_w"].max()) * 260 + 40
    colours = [PALETTE["accent"] if e == df["energy_j"].min()
               else PALETTE["fill"] for e in df["energy_j"]]

    ax.scatter(df["latency_ms"] / 1000.0, df["energy_j"],
               s=sizes, c=colours, alpha=0.85,
               edgecolors=PALETTE["primary"], linewidths=0.7, zorder=3)

    x_max = df["latency_ms"].max() / 1000.0 * 1.30
    y_max = df["energy_j"].max() * 1.30
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max)

    # Two iso-power reference curves only (min and max observed power);
    # four lines crowd this panel. Labels sit inline in the empty
    # upper-left wedge, rotated to follow each line.
    t = np.linspace(0.3, x_max, 100)
    p_lo, p_hi = df["power_w"].min(), df["power_w"].max()
    for p_ref in (p_lo, p_hi):
        ax.plot(t, p_ref * t, color=PALETTE["neutral"], linestyle=":",
                linewidth=0.55, zorder=1)
        x_lab = min(x_max * 0.30, y_max * 0.88 / p_ref)
        ang = np.degrees(np.arctan2(p_ref * (x_max / y_max), 1.0))
        ax.text(x_lab, p_ref * x_lab, f"{p_ref:g} W",
                fontsize=5.2, color=PALETTE["neutral"],
                ha="center", va="bottom", rotation=ang,
                rotation_mode="anchor", zorder=2,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))

    # Point labels alternate above/below by ascending latency, so that
    # neighbouring platforms never share a horizontal band.
    ordered = df.sort_values("latency_ms").reset_index(drop=True)
    for k, r in ordered.iterrows():
        best = r["energy_j"] == df["energy_j"].min()
        xs = r["latency_ms"] / 1000.0
        above = (k % 2 == 1)
        right_half = xs > x_max * 0.72
        ax.annotate(f"{r['platform']}\n{r['power_w']:.1f} W",
                    xy=(xs, r["energy_j"]),
                    xytext=(-9 if right_half else 9, 14 if above else -16),
                    textcoords="offset points", fontsize=5.8,
                    ha="right" if right_half else "left",
                    va="bottom" if above else "top",
                    color=PALETTE["accent"] if best else PALETTE["primary"],
                    fontweight="bold" if best else "normal", zorder=4)

    ax.set_xlabel("Cube-level latency (s)")
    ax.set_ylabel("Energy per inference (J)")

    fig.savefig(out)
    plt.close(fig)

    best = df.loc[df["energy_j"].idxmin()]
    print(f"[Fig N] {out}")
    print(f"        lowest energy: {best['platform']} at {best['energy_j']:.2f} J "
          f"({best['latency_ms']/1000:.3f} s @ {best['power_w']:.1f} W)")
    print(f"        marker area encodes average power; dotted lines are "
          f"iso-power curves E = P*t")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="Model- and mission-side figures for the Mamba-OpticSatNet paper.")
    p.add_argument("--mode", required=True,
                   choices=["ablation", "confusion", "alertsize", "gate",
                            "latency", "energy", "all"])
    p.add_argument("--pred-dir",     default=None, help="Dir of .npy prediction rasters")
    p.add_argument("--gt-dir",       default=None, help="Dir of .npy ground-truth rasters")
    p.add_argument("--prob-dir",     default=None, help="Dir of .npy class-probability maps")
    p.add_argument("--ablation-csv", default=None)
    p.add_argument("--gate-npy",     default=None)
    p.add_argument("--energy-csv",   default=None)
    p.add_argument("--out",    default=None)
    p.add_argument("--outdir", default="./figures")

    # Paper parameters
    p.add_argument("--tproc",       type=float, default=1.698)
    p.add_argument("--rate",        type=float, default=1.0)
    p.add_argument("--b0",          type=float, default=13120.0)
    p.add_argument("--b3",          type=float, default=0.80)
    p.add_argument("--assumed-kb",  type=float, default=100.0)
    p.add_argument("--min-area-px", type=int,   default=8)
    p.add_argument("--gsd",         type=float, default=10.0)
    p.add_argument("--twait-p0",    type=float, default=None)
    p.add_argument("--twait-p3",    type=float, default=None)

    a = p.parse_args()
    apply_style()
    os.makedirs(a.outdir, exist_ok=True)

    def path_for(name):
        return a.out if a.out else os.path.join(a.outdir, name)

    modes = (["ablation", "confusion", "alertsize", "gate", "latency", "energy"]
             if a.mode == "all" else [a.mode])

    for m in modes:
        try:
            if m == "ablation":
                if not a.ablation_csv:
                    raise ValueError("--ablation-csv required")
                fig_ablation(a.ablation_csv, path_for("fig_I_ablation.pdf"))
            elif m == "confusion":
                if not (a.pred_dir and a.gt_dir):
                    raise ValueError("--pred-dir and --gt-dir required")
                fig_confusion(a.pred_dir, a.gt_dir, path_for("fig_J_confusion.pdf"))
            elif m == "alertsize":
                if not a.pred_dir:
                    raise ValueError("--pred-dir required")
                fig_alertsize(a.pred_dir, path_for("fig_K_alertsize.pdf"),
                              prob_dir=a.prob_dir, min_area_px=a.min_area_px,
                              gsd_m=a.gsd, assumed_kb=a.assumed_kb,
                              rate_mbps=a.rate)
            elif m == "gate":
                if not a.gate_npy:
                    raise ValueError("--gate-npy required")
                fig_gate(a.gate_npy, path_for("fig_L_gate.pdf"))
            elif m == "latency":
                fig_latency(path_for("fig_M_latency.pdf"), tproc_s=a.tproc,
                            twait_p0_s=a.twait_p0, twait_p3_s=a.twait_p3,
                            b0_mbit=a.b0, b3_mbit=a.b3, rate_mbps=a.rate)
            elif m == "energy":
                fig_energy(path_for("fig_N_energy.pdf"), csv_path=a.energy_csv)
        except Exception as exc:                       # noqa: BLE001
            print(f"[error] mode '{m}': {exc}", file=sys.stderr)

    print("\nDone.")


if __name__ == "__main__":
    main()
