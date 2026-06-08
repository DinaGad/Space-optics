# Inter-Satellite Laser Communications: Physics, Link Design, and the Optical Subsystem for Small Satellites

A design-oriented tutorial. The aim is that by the end you can (a) reason quantitatively about an optical inter-satellite link (OISL) budget, (b) size the optical head, and (c) understand the dominant engineering constraints that separate a CubeSat terminal from a constellation-class one.

---

## 1. Why optical, and what the trade really is

An optical inter-satellite link is just a microwave link with a wavelength ~10,000–50,000× shorter. Every Friis-style relation you know from RF carries over; only the numbers change, and they change in a way that creates one specific, dominant problem: **pointing**.

The antenna gain of a diffraction-limited aperture is

$$ G = \left(\frac{\pi D}{\lambda}\right)^2 \eta $$

where $D$ is the aperture diameter, $\lambda$ the wavelength, and $\eta$ an efficiency factor (illumination, truncation, obscuration). Because $G \propto \lambda^{-2}$, moving from, say, a Ka-band link at 30 GHz ($\lambda = 1$ cm) to a 1550 nm optical link ($\lambda \approx 1.55\,\mu$m) raises the gain of the *same* aperture by $\sim(10^{-2}/1.55\times10^{-6})^2 \approx 4\times10^{7}$, i.e. roughly **76 dB**. That is why a centimeter-scale optical aperture out-performs a meter-scale dish.

The price is beam divergence. The diffraction-limited far-field half-angle scales as

$$ \theta_{\text{div}} \approx \frac{\lambda}{D} \quad\text{(order-of-magnitude; }k\lambda/D\text{ with }k\approx 1\text{–}1.27\text{ depending on aperture taper)} $$

For an 80 mm aperture at 1550 nm, $\theta_{\text{div}}\sim 19\ \mu$rad. Holding that beam on a target thousands of kilometers away while both endpoints move at ~7.5 km/s, on a platform whose reaction wheels inject micro-vibration, is the central design problem. Almost every architectural choice in an OISL terminal exists to solve pointing, acquisition, and tracking (PAT).

Secondary advantages, which matter especially in the smallsat/New-Space context: no ITU/FCC spectrum coordination (the optical band is unlicensed), low probability of intercept/detection (the beam is a pencil), and the ability to ride telecom-grade 1550 nm components (DFB lasers, EDFAs, modulators, InGaAs detectors) at low cost.

---

## 2. The link budget — the equation you design against

Received signal power for a vacuum link (no atmosphere, which is the ISL case) is the product of a transmit term, a geometric (free-space) loss, a receive term, and the implementation/pointing losses:

$$ P_r = P_t \, G_t \, L_t \, L_{\text{fs}} \, G_r \, L_r \, L_p $$

with the individual terms:

| Term | Expression | Meaning |
|---|---|---|
| $P_t$ | — | Transmit optical power at the aperture (W) |
| $G_t$ | $(\pi D_t/\lambda)^2$ | Transmit antenna gain (peak, on-axis) |
| $L_t$ | $\le 1$ | Transmit optics throughput (mirrors, fiber coupling) |
| $L_{\text{fs}}$ | $\left(\dfrac{\lambda}{4\pi Z}\right)^2$ | Free-space loss; $Z$ = range |
| $G_r$ | $(\pi D_r/\lambda)^2$ | Receive antenna gain |
| $L_r$ | $\le 1$ | Receive optics + fiber-coupling efficiency |
| $L_p$ | $\exp\!\big(-2\,\theta_{\text{err}}^2/\theta_{\text{div}}^2\big)$ | Pointing loss for a Gaussian beam at offset $\theta_{\text{err}}$ |

Note the free-space term uses the *same* $(\lambda/4\pi Z)^2$ form as RF. Combining the geometric terms for matched apertures $D_t=D_r=D$:

$$ \frac{P_r}{P_t}\bigg|_{\text{geom}} = G_t\,L_{\text{fs}}\,G_r = \frac{\pi^2 D_t^2 D_r^2}{16\,\lambda^2 Z^2} $$

Two design levers fall straight out of this:

- **Aperture is king.** $P_r \propto D_t^2 D_r^2$ — a fourth-power leverage across the two ends. Doubling both apertures buys 12 dB.
- **Shorter $\lambda$ helps the budget** (net $\lambda^{-2}$) but tightens the pointing requirement ($\theta_{\text{div}}\propto\lambda$). This is the fundamental tension.

### 2.1 The receiver side: how much power do you actually need?

The required $P_r$ is set by the data rate, the modulation/detection scheme, and the target bit-error rate (BER). The cleanest currency is **photons per bit (PPB)**:

$$ \text{PPB} = \frac{P_r}{h\nu\,R_b}, \qquad h\nu = \frac{hc}{\lambda} = 1.28\times10^{-19}\ \text{J at }1550\text{ nm} $$

where $R_b$ is the bit rate. Rearranged, the receiver sensitivity is

$$ P_{r,\min} = \text{PPB}_{\text{req}} \cdot h\nu \cdot R_b $$

Approximate sensitivity floors by receiver type (1 Gbps class, BER $10^{-9}$ before FEC):

| Receiver | Typical PPB required | Notes |
|---|---|---|
| Direct-detection OOK, InGaAs APD | ~1,000–5,000 | Simplest; thermal + excess-noise limited |
| Pre-amplified (EDFA + PIN), OOK | ~100–500 | ASE-noise limited; common in lasercom |
| Coherent (homodyne BPSK, balanced) | ~10–40 | Near quantum limit; best sensitivity, most complex |
| PPM (deep-space, photon-starved) | ~1–5 (per photon-efficient design) | Rarely used for ISL; high peak-to-avg |

FEC (LDPC, Reed–Solomon, concatenated) buys several dB of coding gain and is assumed in all modern designs; the quasi-error-free target post-FEC is conventionally BER $\le 10^{-12}$ for OISLs.

### 2.2 Margins

Always carry, separately:
- **Pointing loss** (often allocated 1–3 dB) — depends on residual jitter vs beam width (Section 4).
- **Implementation loss** — modulator extinction, timing jitter, ISI: 1–3 dB.
- **Link margin** — the unallocated reserve, typically 3–6 dB for a qualified design.

---

## 3. A worked link budget (do this twice — CubeSat and constellation class)

### 3.1 CubeSat-class crosslink

Assume: $\lambda = 1550$ nm, $D_t=D_r=20$ mm, $P_t=0.2$ W (23 dBm), $Z=1000$ km, $R_b=100$ Mbps.

$$ G_t = G_r = \left(\frac{\pi\cdot0.02}{1.55\times10^{-6}}\right)^2 = 1.64\times10^{9} \;\Rightarrow\; 92.2\ \text{dB} $$
$$ L_{\text{fs}} = \left(\frac{1.55\times10^{-6}}{4\pi\cdot10^{6}}\right)^2 = 1.52\times10^{-26} \;\Rightarrow\; -258.2\ \text{dB} $$

| Line | dB |
|---|---|
| $P_t$ (0.2 W) | +23.0 dBm |
| $G_t$ | +92.2 |
| $L_t$ (TX optics) | −3.0 |
| $L_{\text{fs}}$ | −258.2 |
| $G_r$ | +92.2 |
| $L_r$ (RX optics + fiber) | −3.0 |
| $L_p$ (pointing) | −3.0 |
| **$P_r$** | **−59.8 dBm** = 1.05 nW |

PPB $= 1.05\times10^{-9} / (1.28\times10^{-19}\cdot10^{8}) \approx 82$ photons/bit. With a pre-amplified receiver (≈100–500 PPB needed) this is **tight but closable** with FEC — which is exactly why real CubeSat ISL terminals sit at ~100 Mbps over ~1000–1500 km rather than at Gbps.

### 3.2 Constellation-class crosslink

Assume: $D_t=D_r=80$ mm, $P_t=1$ W (30 dBm), $Z=5000$ km, $R_b=1$ Gbps.

$$ G_t=G_r=\left(\frac{\pi\cdot0.08}{1.55\times10^{-6}}\right)^2 = 2.63\times10^{10}\;\Rightarrow\;104.2\ \text{dB} $$
$$ L_{\text{fs}}=\left(\frac{1.55\times10^{-6}}{4\pi\cdot5\times10^{6}}\right)^2=6.08\times10^{-28}\;\Rightarrow\;-272.2\ \text{dB} $$

Summing with the same −3/−3/−3 dB allocations gives $P_r \approx -42.8$ dBm = 52 nW, or **≈400 PPB at 1 Gbps** — comfortable margin, scalable to 10s of Gbps by raising $P_t$ (booster EDFA) and improving the receiver. This reproduces the real capability envelope of 80 mm constellation terminals.

The takeaway: the *physics* is identical at both scales; what changes is the SWaP you can spend on aperture, transmit power, and a precision pointing chain.

---

## 4. Pointing, Acquisition, and Tracking (PAT) — the part that actually fails

A diffraction-limited beam ~10–30 μrad wide must be held on a target whose *initial* position is known only to the accuracy of the spacecraft attitude system (often ±0.1° to ±1°, i.e. 1,700–17,000 μrad). PAT bridges that three-to-four-order-of-magnitude gap in stages.

### 4.1 The pointing chain (coarse → fine → point-ahead)

1. **Coarse pointing.** Either body-pointing the whole spacecraft (ADCS slew, used by CubeSats to avoid a gimbal) or a 2-axis **gimbal** on larger terminals. Brings line-of-sight (LOS) into the field of uncertainty, on the order of ±1° initially, refined toward ±0.05° once a signal is seen.
2. **Fine pointing / tracking.** A **fast steering mirror (FSM)** — voice-coil or piezo, or a MEMS mirror on CubeSats — driven in closed loop from a tracking-detector error signal, holds the beam to **single-digit μrad rms**, with a control bandwidth of several hundred Hz to a few kHz to reject platform micro-vibration.
3. **Point-ahead.** Because of finite light-travel time and transverse relative motion, you must aim the transmit beam *ahead* of where the partner appears to be, by

$$ \alpha_{\text{PA}} = \frac{2 v_\perp}{c} $$

For $v_\perp = 7.5$ km/s, $\alpha_{\text{PA}} = 2(7500)/(3\times10^8) = 50\ \mu$rad — *larger than the beam itself*. So the transmit path needs a dedicated **point-ahead mechanism** (a second steering element, or an offset commanded on the FSM), decoupled from the receive tracking direction.

### 4.2 Acquisition

The two terminals must first find each other inside the cone of attitude uncertainty. The canonical method:

- One (or both) terminals run a **spiral scan**, sweeping a beam across the uncertainty cone in overlapping steps. The step size $C_{\text{step}}$ relative to the transmit beamwidth sets an *overlap loss* — at $C_{\text{step}}=\theta_{TX}$ the loss is ~8.6 dB; tightening to the FWHM diameter reduces it to ~3 dB at the cost of scan time.
- The partner detects the incoming light on a **wide-field acquisition sensor** (a focal-plane array or quad-cell), reports detection, and both hand over to closed-loop tracking.
- A **point-ahead/scan handshake** plus a defined **state machine** (idle → scan → detect → track → comm) governs the sequence; interoperability standards specify timing budgets for each transition.

### 4.3 Beacon vs. beaconless

- **Beacon-aided:** a separate, often wider and sometimes different-wavelength beacon laser eases acquisition (the partner only needs to find a broad beacon, not the pencil comm beam). Costs SWaP and a second optical chain.
- **Beaconless:** the communication beam itself is used for spatial acquisition. Lower SWaP, harder PAT, and the modern preference for dense LEO constellations.

### 4.4 The jitter requirement (design rule)

Residual pointing jitter $\sigma_p$ couples directly into a power fade through the Gaussian profile. A common allocation is to keep $\sigma_p \lesssim \theta_{\text{div}}/4$ to bound the mean jitter-induced fade to ≈1 dB, and to verify the *fade statistics* (deep-fade probability, not just the mean) against your FEC/interleaver depth. This is what sets the FSM bandwidth and the micro-vibration isolation requirement — and on a CubeSat, it is usually the binding constraint, because reaction-wheel and cryocooler vibration sit right in the control band.

---

## 5. Choosing the operating point: wavelength, modulation, detection

### 5.1 Wavelength

- **1550 nm band** dominates. It inherits the entire telecom ecosystem — DFB/ECL seed lasers, LiNbO₃/EAM modulators, **EDFA** optical amplifiers, low-noise InGaAs APDs/PINs, single-mode fiber, WDM filters — and is comparatively eye-safe.
- **1064 nm** (Yb/Nd:YAG) appears in some beacons and high-power transmitters.
- **800 nm** is the SILEX/early-GEO-relay heritage band (silicon detectors, but no EDFA).
- Interoperability standards in the LEO constellation world fix specific DWDM-grid channels so that any two compliant terminals can link.

### 5.2 Modulation / detection

| Scheme | Detection | Where used | Trade |
|---|---|---|---|
| OOK (NRZ) / Manchester | Direct (APD or EDFA+PIN) | Constellation baseline | Simplest; modest sensitivity |
| DPSK | Direct (delay-line interferometer) | High-rate links | ~3 dB better than OOK, no LO |
| BPSK/QPSK coherent | Homodyne/heterodyne, balanced PDs | Highest-rate, GEO relay | Best sensitivity + spectral efficiency; LO, carrier recovery |
| PPM | Direct, photon-counting | Deep space (not ISL) | Photon-efficient, low throughput |
| (C)PolSK | Polarization-resolved | Experimental smallsat | Robust to phase noise; novel |

Pick the *simplest* scheme that closes the budget. For a first smallsat OISL, OOK with an EDFA-preamplified receiver plus strong FEC is the pragmatic default; reach for coherent only when the rate or range forces it.

---

## 6. The optical subsystem — designing and developing the "optical component"

This is the heart of your question. The **optical head** (terminal optomechanics + photonics) is where the link budget becomes hardware. A monostatic terminal (shared transmit/receive aperture) is standard. Walk the light path:

```
                          ┌──────────── COARSE POINTING ────────────┐
   partner sat  ───►  Telescope / beam expander (defines D, gain)
                          │
                          ▼
                   Coarse pointing:  gimbal  OR  body-point the bus (CubeSat)
                          │
                          ▼
                   Point-ahead mirror  ──┐  (TX leads RX by α_PA)
                          │              │
                          ▼              │
                   Fast Steering Mirror (FSM)  ◄── error signal
                          │
                          ▼
                   TX/RX duplexer  ── by wavelength (dichroic) / polarization / time
                    ├──► RX path ──► narrowband filter ──► beamsplitter
                    │                       ├─► tracking detector (QPD/PSD) ──► FSM loop
                    │                       └─► comm detector (APD / PIN+EDFA / coherent Rx) ──► demod+FEC
                    └──◄ TX path ◄── collimator ◄── booster EDFA ◄── modulator ◄── seed laser (DFB 1550)
```

### 6.1 Telescope / aperture (sets the gain)

Choose $D$ from the link budget (Section 3). On a small satellite this is the single biggest lever and the single biggest SWaP cost. Designs:
- **Reflective** (Cassegrain/RC, off-axis to avoid central obscuration) for larger apertures and achromaticity.
- **Refractive / catadioptric** collimators for the smallest (cm-class) CubeSat heads.
The telescope is an **afocal beam expander**: it magnifies the small internal beam up to the aperture, and reciprocally compresses the incoming wavefront down to the fiber/detector.

### 6.2 Transmit / receive isolation

You must separate your own ~W-class transmit light from the ~nW receive signal sharing the same aperture, with ≥ 60–90 dB isolation:
- **Wavelength duplexing** — TX and RX on different DWDM channels, split by a dichroic. Lets you build symmetric A↔B pairs and constellations (one terminal's TX wavelength is the other's RX). This is the dominant modern approach.
- **Polarization duplexing** — orthogonal TX/RX polarizations split by a PBS.
- **Time duplexing** — alternate TX/RX (simplest, halves throughput).

### 6.3 Fine steering mirror + tracking detector

The FSM and a **quadrant photodiode (QPD)** (or position-sensitive detector / focal-plane array) form the tracking loop. The QPD's four-quadrant difference signals give the LOS error in two axes:

$$ e_x \propto \frac{(Q_1+Q_4)-(Q_2+Q_3)}{\sum Q_i}, \qquad e_y \propto \frac{(Q_1+Q_2)-(Q_3+Q_4)}{\sum Q_i} $$

These drive the FSM to null the error. **Co-boresighting** the QPD null with the transmit beam axis (to μrad) during integration is one of the most alignment-critical, and most error-prone, steps — a scheme used on several CubeSat terminals is to feed back the received beacon onto the QPD center so that nulling it automatically co-aligns the outgoing beam.

### 6.4 Fiber coupling (the silent killer)

Coupling the collected free-space beam into **single-mode fiber** (to reach the EDFA and a coherent or fiber-coupled receiver) is brutally sensitive to wavefront error and residual pointing. Coupling efficiency drops fast once the wavefront error exceeds ~λ/14 RMS or the tip/tilt exceeds a fraction of the mode-field acceptance angle. This pushes:
- a tight **wavefront-error budget** (telescope + bench, often λ/10–λ/20),
- and a fine-tracking residual well inside the fiber's angular acceptance.

A multimode fiber or a direct free-space detector relaxes this at the cost of receiver sensitivity (you lose the coherent/EDFA path).

### 6.5 Transmit chain photonics

Seed **DFB laser** (1550 nm, narrow-linewidth) → external **modulator** (Mach-Zehnder/EAM) or direct modulation → **booster EDFA** to the required $P_t$ (100s mW to several W) → collimator → telescope. The seed/modulator/EDFA are all telecom-derived, which is what makes a New-Space terminal affordable.

### 6.6 Optomechanics & thermal — where smallsats get hard

- **Athermal, stable bench.** Low-CTE materials (invar, Zerodur, or CTE-matched aluminum with athermalized mounts). The TX/RX boresight must hold to μrad across the orbital thermal cycle — a few μm of differential expansion across a 100 mm bench is already several μrad.
- **Micro-vibration.** Reaction wheels, gimbal bearings, and any moving mechanism inject jitter into the control band; budget isolation and FSM bandwidth accordingly. On a CubeSat this is frequently the dominant link-availability risk.
- **Stray light & background.** A narrowband filter (≤1 nm) at the comm wavelength plus baffling rejects sunlit-Earth and direct-sun background. Define **Sun-exclusion** and **Earth-exclusion** angles in the CONOPS — they directly reduce link-available time per orbit.
- **Radiation.** TID and displacement damage degrade detectors and EDFA pump diodes; derate and screen.

---

## 7. Small-satellite-specific design strategy

The defining smallsat constraint is SWaP. The architectural responses:

- **Drop the gimbal, body-point.** Use the ADCS for coarse pointing and rely entirely on an FSM/MEMS mirror for fine pointing. This removes the heaviest, most power-hungry mechanism, at the cost of demanding ADCS performance and orbit/attitude planning. (Body-pointing-only with no fine stage cannot achieve ISL-grade precision — the lesson from early MIT-class free-space modules — so a fine stage is essentially mandatory for ISL.)
- **Single small aperture (cm-class), beaconless.** Accept ~100 Mbps over ~1000–1500 km rather than Gbps.
- **COTS telecom photonics.** Seed/modulator/EDFA/detectors from the fiber-comm industry, space-screened.
- **Integrate the terminal into a standard form factor.** 1U-class self-contained optical heads exist, designed to bolt onto a standard CubeSat bus, with TX/RX wavelength separation so they can form multi-node constellations.

### 7.1 A sizing workflow you can actually run

1. **Geometry** → max range $Z$, geometry vs orbit, relative transverse velocity $v_\perp$ → point-ahead $\alpha_{\text{PA}}$.
2. **Requirement** → $R_b$, BER target → required PPB → $P_{r,\min}$ (Section 2.1).
3. **Fix $\lambda$** (default 1550 nm) and the modulation/detection (default OOK + EDFA preamp + FEC).
4. **Allocate margins** (pointing 1–3 dB, implementation 1–3 dB, reserve 3–6 dB).
5. **Solve the link equation** for the feasible region in $(P_t, D_t, D_r)$.
6. **Pointing closure** → from achievable jitter $\sigma_p$ (ADCS + FSM), set $\theta_{\text{div}}\ge 4\sigma_p$; check this is consistent with the $D$ you chose ($\theta_{\text{div}}\sim k\lambda/D$). If not, you must either narrow the beam (more pointing performance) or widen it (lose gain) — iterate.
7. **SWaP check** → mass/power/volume of aperture + EDFA + FSM + electronics against the bus allocation.

Steps 5–7 are a genuine **multi-objective optimization** (maximize $R_b$, minimize SWaP, subject to pointing closure and margin constraints) — the link budget, the pointing budget, and the SWaP model are coupled constraints over the same design vector $(D, P_t, \theta_{\text{div}}, \text{FSM bandwidth}, \dots)$. If you have a Pareto/MOPSO framework, this maps onto it cleanly: design vector = optical/RF/pointing parameters, objectives = throughput and SWaP, constraints = margin ≥ threshold and $\sigma_p \le \theta_{\text{div}}/4$.

---

## 8. Verification & validation

A representative V&V flow before trusting an OISL terminal:

1. **Component characterization** — laser linewidth/power, EDFA gain/NF, detector responsivity/sensitivity, FSM frequency response.
2. **Optical alignment & wavefront** — interferometric WFE measurement of the assembled telescope/bench; fiber-coupling efficiency map.
3. **TX/RX boresight co-alignment** — to μrad, with thermal stability verification.
4. **Closed-loop tracking** — bandwidth, jitter rejection, residual $\sigma_p$, with **injected platform disturbance** (reaction-wheel jitter emulation).
5. **End-to-end link test** — either a long horizontal atmospheric path (the canonical approach is a tens-to-~150 km mountaintop-to-mountaintop link that mimics the photon budget and turbulence) or a lab link with calibrated attenuation and turbulence/Doppler emulation; measure BER vs. received power and confirm the predicted sensitivity.
6. **Environmental** — thermal-vacuum cycling, vibration/shock, TID/radiation, before flight.

Treat the predicted link budget and the measured sensitivity curve as the two things that must agree; a gap between them is your unmodeled loss (coupling, alignment, implementation) and must be closed before flight.

---

## 9. State of the art (as of early–mid 2026)

**Constellation / "small-satellite-platform" class (cm–dm aperture):**
- The dominant commercial inter-satellite terminal family uses an ~80 mm aperture, single-aperture telescope, and delivers from ~100 Mbps up to ~100 Gbps (configurable) over intra/inter-plane distances of several thousand km, engineered for serial production. These terminals are compliant with the U.S. Space Development Agency (SDA) optical-terminal standard used across its LEO "Tranche" constellations; well over a hundred had been delivered for the Tranche 1 set by mid-2025, and the leading vendor was acquired by a launch/space-systems prime in early 2026.
- An interoperability standard (SDA's Optical Communications Terminal standard, v4.0.0) pins the physical layer so terminals from different makers can link: two DWDM channels at **1536.61 nm and 1553.33 nm** (either may be TX or RX, but not the same one simultaneously), OOK with NRZ/Manchester up to ~2.2 Gbps for proliferated-LEO links, plus two burst-mode Manchester formats (≈48.9 and 36.7 Mbps) that trade rate for robustness on long crosslinks out to ~20,000 km, with a tracking tone and a defined beaconless PAT state machine and spiral-scan acquisition.

**CubeSat class (mm–cm aperture, 1U-ish optical head):**
- DLR's **CubeISL** is a 1U terminal designed for ~100 Mbps inter-satellite links over up to ~1,500 km (and ~1 Gbps downlink), using wavelength separation of TX and RX so multiple units can form a constellation; it was validated on a 143 km horizontal atmospheric link between two Canary Island sites and is flying on a pair of 6U CubeSats.
- DLR's earlier **OSIRIS4CubeSat (O4C)** established the compact direct-to-Earth CubeSat terminal baseline; **MIT's CLICK** series and O4C pioneered the FSM-plus-quad-detector fine-pointing scheme now reused widely (e.g. the University of Chicago **PULSE-A** terminal, which demonstrates circular-polarization-shift-keyed links with a ~250 mW EDFA-amplified 1550 nm transmit path and an FSM/quadrant-photodiode feedback loop).
- In early 2025 The Aerospace Corporation demonstrated the **first optical crosslink between two 6U CubeSats** in LEO ("Flashlight"), a milestone for formation-flying smallsat OISL.

**Heritage anchor:** ESA's **SILEX** (SPOT-4 ↔ Artemis) proved GEO–LEO optical links decades ago but with ~250 mm apertures, ~200 W, ~150 kg terminals — a useful reminder of how far miniaturization has come: today's CubeSat terminals achieve comparable or higher rates at ~1% of the mass.

---

## 10. Quick-reference summary

- The OISL problem **is** an RF link problem with $\lambda^{-2}$-larger antenna gain and correspondingly μrad-narrow beams; **pointing dominates everything.**
- Design against $P_r = P_t G_t L_t L_{\text{fs}} G_r L_r L_p$, convert to **photons/bit**, and pick the simplest modulation/detection that closes it (OOK + EDFA preamp + FEC first; coherent only if forced).
- **Aperture has 4th-power leverage**; shorter $\lambda$ helps the budget but tightens pointing.
- PAT is three nested stages: **coarse (body/gimbal) → fine (FSM + QPD, μrad, kHz) → point-ahead ($2v_\perp/c$, tens of μrad)**, plus an acquisition spiral-scan handshake.
- The optical head = telescope/beam-expander, coarse pointing, point-ahead mirror, FSM, wavelength/polarization duplexer, tracking detector, comm detector, and a telecom-photonics TX chain on a thermally stable, low-jitter bench. **Fiber coupling and TX/RX boresight stability are the quiet failure modes.**
- For **smallsats**: drop the gimbal, body-point + FSM, single small aperture, beaconless, COTS 1550 nm photonics, accept ~100 Mbps over ~1000–1500 km.
- Close the loop with V&V: predicted budget vs. measured sensitivity must agree, and the pointing loop must survive injected platform vibration.

---

*Suggested next steps if you want to go deeper: (1) build a parametric link-budget + pointing-closure model and run it as a multi-objective trade over $(D, P_t, \theta_{\text{div}}, \text{FSM BW})$; (2) read the SDA OCT standard for a concrete, interoperable requirement set; (3) study the O4C / CubeISL / CLICK design papers for worked CubeSat optomechanics.*
