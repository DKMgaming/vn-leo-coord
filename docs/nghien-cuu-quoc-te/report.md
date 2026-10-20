# How the World Manages Radio Frequencies and Orbits for LEO / NGSO Satellite Constellations

Research for a national regulator (Vietnam) building an LEO/NGSO spectrum-and-orbit management strategy.
Compiled 2026-10-19. All research was done via the web index (the live research browser was unavailable during this run); no claim was confirmed by a live in-browser check. Primary sources (FCC, ITU, regulator documents) are preferred below; aggregator/legal-analysis sources are identified as such.

## Executive Summary

- **FCC (USA)** moved in stages from rigid EPFD limits to operator-to-operator coordination: 2017 NGSO FSS Order set 50%-in-6-years / 100%-in-9-years milestones and a 6% ΔT/T NGSO-NGSO sharing trigger; the 2024 Second R&O adopted throughput-degradation protection criteria (3% time-weighted average, 0.4% absolute unavailability increase) between earlier- and later-round systems with a 10-year sunset; and the April 30, 2026 R&O replaced EPFD limits with a performance-based NGSO–GSO coordination framework in 10.7–12.7, 17.3–18.6 and 19.7–20.2 GHz. Warehousing deterrents include an escalating $3M (GSO) / $5M (NGSO) surety bond and application fees of $15,050 per NGSO system. A 5-year post-mission disposal rule (2022) and the Supplemental Coverage from Space framework (2024) complete the picture.
- **ITU** enforces anti-warehousing through WRC-19 Resolution 35 milestones (10%/50%/100% of the constellation at +2/+5/+7 years after the 7-year bringing-into-use period), revised at WRC-23 with post-milestone obligations. Interference protection rests on PFD limits (RR Art. 21 Table 21-4), EPFD limits (Art. 22 + Res. 76 aggregate), Appendix 5 coordination arcs, and the Appendix 8 ΔT/T 6% criterion, all computed with the ITU-R S.1503 methodology.
- **Other administrations** mix ITU-aligned licensing with national fees, milestone-like conditions (UK 12-month gateway build-out; Thailand whole-system landing rights), and ownership/local-presence conditions (Singapore).
- **Sustainability**: the IADC 25-year rule (2021 Rev. 3) remains the global baseline, but the trend is toward shorter disposal (FCC 5 years; EU Space Act proposal: 90% disposal success) and mandatory collision avoidance.
- **Vietnam** already has the legal hooks (Law on Radio Frequencies' "frequency and satellite orbit use licence"; ARFM under the Ministry of Science and Technology; a Space Committee; a space S&T strategy to 2030; and a 2025–2030 LEO pilot that has already licensed Starlink).

---

## 1. FCC (USA) NGSO licensing reforms

### 1a. From EPFD limits toward operator-to-operator coordination

**2017 — NGSO FSS Report and Order (FCC 17-122, IB Docket No. 16-408, adopted 26 Sept 2017).**
Updated the rules for non-geostationary satellites in the FSS. Key elements: amended the US Table of Frequency Allocations to accommodate NGSO and GSO use in Ka-band (20/30 GHz); **eliminated international geographic coverage requirements**; and adopted a **new default spectrum-sharing threshold mechanism** that applies between NGSO operators when they have no coordination agreement (coordination in good faith comes first; the default mechanism is the fallback). The order also introduced the **6% ΔT/T coordination trigger** for NGSO–NGSO sharing in 47 CFR 25.261 (a value borrowed from the ITU's Appendix 8 criterion): if good-faith coordination fails, the default remedy is an **equal split of spectrum during in-line (congestion) events**, with **seniority ordered by launch** — earlier-launched systems are senior. Source: https://docs.fcc.gov/public/attachments/DOC-346893A1.pdf (FCC news release, index).

**2021–2023 — "Revising Spectrum Sharing Rules for Non-Geostationary Orbit, Fixed-Satellite Service Systems" (IB Docket No. 21-456).**
In December 2023 the FCC opened an NPRM (on a SpaceX petition) asking whether the **first-mover priority** for NGSO–NGSO sharing should be sunset or reformed. The resulting Report and Order created an **inter-round protection framework**: systems licensed in an earlier processing round get **primary spectrum access**; systems in later rounds must demonstrate (via a degraded-throughput compatibility analysis) they can operate compatibly with earlier-round systems. The inter-round protection carried a **10-year sunset**. Sources: https://connectivitybusiness.com/news/government-legal/fcc-initiates-review-of-ngso-spectrum-sharing-regulations/; https://www.newamerica.org/insights/leo-satellites/chapter-i-fueling-connectivity-from-space-spectrum-sharing-and-coexistence/ (index).

**2024 — Second Report and Order, FCC 24-117 (IB Docket No. 21-456, adopted 5 Nov 2024; 39 FCC Rcd 12656).**
Refined the methodology: in the absence of a coordination agreement, later-round NGSO FSS licensees must meet two quantitative protection criteria vis-à-vis earlier-round systems —
- **long-term: 3% time-weighted average throughput degradation** (computed per ITU-R S.2131-1), and
- **short-term: 0.4% absolute increase in link unavailability**.
The Commission declined to adopt additional metrics or an aggregate interference limit, and an Order on Reconsideration denied OneWeb's petition against the sunset. Sources: http://docs.fcc.gov/public/attachments/DOC-407457A1.pdf (FCC news release, index); https://www.lexology.com/library/detail.aspx?g=6554abb9-e969-42a7-8c47-56e62777c1ad (legal analysis, index).

**2025–2026 — EPFD replacement.** An NPRM adopted 29 April 2025 proposed replacing hard EPFD limits with a degraded-throughput framework in 10.7–12.7, 17.3–18.6 and 19.7–20.2 GHz (https://www.tlp.law/2025/05/02/fcc-releases-adopted-nprm-proposing-to-update-spectrum-sharing-rules-for-satellite-broadband/, index). On **30 April 2026 the FCC adopted a unanimous Report and Order** that did so: in those bands NGSO systems must engage in **mandatory good-faith coordination with GSO systems**, with performance backstops of **3% time-weighted average throughput degradation** (for adaptive-coding-and-modulation links), a **0.1% absolute increase in unavailability**, and **−10.5 dB I/N for 80% of the time** (for non-ACM links). Aggregate interference limits were rejected; **ITU EPFD obligations for cross-border coordination were left unchanged** — the domestic change does not alter what the US must show at the ITU. Sources: https://www.jdsupra.com/legalnews/fcc-modernizes-satellite-spectrum-5634424/; https://www.lexology.com/library/detail.aspx?g=4476b010-c92c-4f71-a1e4-b8295933508d (legal analyses, index).

### 1b. Milestones, performance bonds, application fees

- **Milestones (FCC 17-122, 2017):** 50% of the authorized constellation within **6 years** of license grant, 100% within **9 years** (the prior rule demanded 100% in 6 years). Failure → the authorization is **reduced to the number of satellites actually deployed** (https://docs.fcc.gov/public/attachments/DOC-346893A1.pdf).
- **Surety bond (FCC 15-167, IB Docket No. 12-267, 2015):** an **escalating performance bond — $3M for GSO, $5M for NGSO** — payable (forfeited) if deployment milestones are not met (https://www.federalregister.gov/documents/full_text/html/2021/03/01/2020-28907.html, index).
- **Application fees (FCC 21-110, 2021):** **$15,050 per NGSO system** of technically identical satellites per call sign; **$2,175 for small-satellite NGSO** systems; **$15,050 for an NGSO market-access petition**; $3,555 per GSO satellite (https://docs.fcc.gov/public/attachments/FCC-21-110A1.txt, index).
- **Proposed (not adopted) — Space Modernization NPRM (2025):** would eliminate GSO milestones; align NGSO milestones with the ITU (1 satellite within 7 years; 10% within 9; 50% within 12; 100% within 14 years of the ITU milestone start); convert the bond to a **de-escalating bond reaching $0 at 90% deployment** (for systems ≥200 satellites); and set **20-year license terms** (https://www.insideglobaltech.com/2025/11/11/fcc-proposes-space-modernization-for-the-21st-century-key-highlights-for-industry-and-stakeholders/, legal analysis, index). **Flag: proposal only — do not treat as current law.**

### 1c. 5-year post-mission disposal rule

Second Report and Order in **FCC 22-74 (IB Docket Nos. 18-313 and 22-271), adopted 29 Sept 2022 (4–0 vote)**: satellites in the **LEO region (below 2,000 km)** that would reenter uncontrolled must be **disposed of as soon as practicable and no later than 5 years after mission completion** — replacing the prior 25-year guideline. Applies to US-licensed satellites **and** foreign systems seeking US market access, for satellites **launched 2 or more years after adoption**. Sources: https://docs.fcc.gov/public/attachments/DA-25-256A1.pdf; https://advanced-television.com/2022/09/30/fcc-adopts-5-year-satellite-deorbiting-rule/ (index).

### 1d. Supplemental Coverage from Space (SCS)

Report and Order + FNPRM, **FCC 24-28 (GN Docket No. 23-65), adopted 14 March 2024**: created a **secondary, bi-directional Mobile-Satellite Service allocation** in flexible-use terrestrial bands (600 MHz, 700 MHz, 800 MHz, PCS, AWS-H) so satellites can provide **supplemental coverage from space** to terrestrial mobile networks. An SCS arrangement requires a **spectrum lease from the terrestrial licensee(s) holding all licenses in a Geographically Independent Area**; interim rules address 911 routing to public-safety answering points. Sources: https://www.tlp.law/2024/03/20/fcc-releases-adopted-scs-item/; https://www.satellitetoday.com/connectivity/2024/02/23/fcc-releases-the-draft-order-for-its-satellite-to-cell-regulatory-framework/ (index).

### Section 1 — summary table

| Instrument / document | Year | Key numeric requirements | Source URL |
|---|---|---|---|
| NGSO FSS R&O, FCC 17-122 (IB Dkt 16-408) | 2017 | Milestones: 50% in 6 yrs, 100% in 9 yrs; fail → authorization reduced; 6% ΔT/T NGSO–NGSO sharing trigger (47 CFR 25.261); default = equal spectrum split, seniority by launch | https://docs.fcc.gov/public/attachments/DOC-346893A1.pdf |
| NGSO sharing R&O (IB Dkt 21-456) | 2023 | Earlier-round systems get primary access; 10-year sunset on inter-round protection | https://www.newamerica.org/insights/leo-satellites/chapter-i-fueling-connectivity-from-space-spectrum-sharing-and-coexistence/ |
| NGSO sharing 2nd R&O, FCC 24-117 (39 FCC Rcd 12656) | 2024 | Later-round must protect earlier-round: 3% time-weighted avg throughput degradation; 0.4% absolute increase in link unavailability | http://docs.fcc.gov/public/attachments/DOC-407457A1.pdf |
| NGSO–GSO R&O (EPFD replacement) | 2026 | Bands 10.7–12.7, 17.3–18.6, 19.7–20.2 GHz: 3% throughput (ACM), 0.1% unavailability, −10.5 dB I/N 80% (non-ACM); ITU EPFD obligations unchanged | https://www.jdsupra.com/legalnews/fcc-modernizes-satellite-spectrum-5634424/ |
| Surety bond, FCC 15-167 (IB Dkt 12-267) | 2015 | Escalating bond: $3M GSO / $5M NGSO, forfeited if milestones missed | https://www.federalregister.gov/documents/full_text/html/2021/03/01/2020-28907.html |
| Application fees, FCC 21-110 | 2021 | $15,050 per NGSO system; $2,175 small-sat NGSO; $15,050 NGSO market access | https://docs.fcc.gov/public/attachments/FCC-21-110A1.txt |
| 5-yr deorbit, 2nd R&O in FCC 22-74 (IB Dkts 18-313, 22-271) | 2022 | LEO <2,000 km: deorbit ≤5 yrs after mission end; applies to sats launched ≥2 yrs after adoption | https://docs.fcc.gov/public/attachments/DA-25-256A1.pdf |
| SCS framework, FCC 24-28 (GN Dkt 23-65) | 2024 | Secondary bi-directional MSS; lease required from terrestrial licensee(s) in each Geographically Independent Area | https://www.tlp.law/2024/03/20/fcc-releases-adopted-scs-item/ |

---

## 2. ITU

### 2a. WRC-19 Resolution 35 milestone approach

**Resolution 35 (WRC-19)** imposes a milestone-based deployment schedule to combat spectrum/orbit warehousing. Definitions and values:
- **Bringing into use (BIU):** deployment of **one satellite** in one orbital plane of the filed constellation, within the standard **7-year regulatory period** (RR No. 11.48) from the API.
- **Milestones (after the end of the 7-year period):** **10%** of the filed constellation within **2 years**; **50%** within **5 years**; **100%** within **7 years**.
- Missing a milestone → the recorded (MIFR) constellation is **reduced** to the number actually deployed.
- **Applies to** NGSO systems in the **FSS, MSS and BSS** in the bands **10.7–13.25 GHz, 13.75–14.5 GHz, 17.3–20.2 GHz, 27.5–30 GHz, 37.5–42.5 GHz, and 47.2–51.4 GHz**.
Sources: https://www.itu.int/en/mediacentre/backgrounders/Pages/Non-geostationary-satellite-systems.aspx; https://www.itu.int/en/ITU-R/space/WRS20space/1-2-Non-GSO%20space%20station%20Milestone%20implementation%20and%20Res%2076%20(WRC-19)%20implementation.pdf (index).

**WRC-23 revision of Resolution 35:** added **post-milestone provisions** (including a new "post-milestone procedure") and a requirement to **report orbital characteristics** of the deployed constellation — first at **11 years after the BIU deadline**, then **every 4 years**. Source: https://www.lexology.com/library/detail.aspx?g=346339b2-4c2f-40d4-84a7-a4ae3e1b5e1f (legal analysis, index).

### 2b. International filing process

The standard sequence for a satellite network (per the ITU Space FAQ and the Radio Regulations):
1. **Advance Publication Information (API)** — RR Art. 9 §I (No. 9.1); published in the BR IFIC; **4-month commenting period** (No. 9.3).
2. **Coordination** — RR Art. 9 §II: **No. 9.7** (GSO–GSO), **No. 9.11A** (GSO vs terrestrial / other cases), **No. 9.12** (NGSO–NGSO), **No. 9.12A** (NGSO vs GSO), **No. 9.13** (GSO vs NGSO), **Nos. 9.7A/9.7B** (coordination of specific earth stations — see pfd triggers in (e) below).
3. **Notification** — RR Art. 11 (examination under Nos. 11.31/11.32, including EPFD checks).
4. **Recording in the MIFR** — with the 7-year BIU regulatory period (No. 11.44/11.48); **EPFD compliance is examined at the coordination-request and notification stages** (WRC-19 clarified single-entry and aggregate EPFD verification, the latter via consultative meetings).
Source: https://www.itu.int/hub/space/faq/ (ITU Space FAQ, index).

### 2c. PFD limits — RR Article 21, Table 21-4

The pfd (power flux-density) at the Earth's surface from space-station emissions, as a function of **angle of arrival δ** above the horizontal:

- **10.7–11.7 GHz (FSS downlink):**
  - δ = 0–5°: **−150 dB(W/m²)/4 kHz** (equivalently **−126 dB(W/m²)/1 MHz**)
  - δ = 5–25°: **−150 + 0.5(δ − 5)** dB(W/m²)/4 kHz (equivalently −126 + 0.5(δ − 5) /1 MHz)
  - δ = 25–90°: **−140 dB(W/m²)/4 kHz** (equivalently **−116 dB(W/m²)/1 MHz**)
- **17.7–19.3 GHz (FSS downlink):**
  - δ = 0–5°: **−115 dB(W/m²)/1 MHz**
  - δ = 5–25°: **−115 + 0.5(δ − 5)** dB(W/m²)/1 MHz
  - δ = 25–90°: **−105 dB(W/m²)/1 MHz**
  - For **NGSO systems with ≥51 satellites**, the limits are **reduced by factor X**: **X = (5/119)(n − 50)** for n ≤ 288; **X = (1/69)(n + 402)** for n > 288 (implemented in the US at 47 CFR 2.106 n. 21.16; the reduction originates in the WRC-19 revisions to the Table 21-4 regime).
Sources: https://www.govregs.com/regulations/47/47CFR25.208; https://www.govregs.com/regulations/47/47CFR2.106-21.16 (US CFR mirroring RR, index).

### 2d. EPFD limits — RR Article 22

Article 22 (Tables 22-1A through 22-4) caps the **equivalent pfd (epfd)** produced by NGSO FSS systems into GSO receivers — single-entry limits per system plus aggregate limits:
- **Single-entry epfd↓ (Table 22-1A), 10.7–12.75 GHz:** the mask's **never-to-be-exceeded point is −160 dBW/m²/40 kHz** (SES licence filing, 18 Nov 2025). ⚠️ **Flag:** the full single-entry mask curve (limit vs. percentage of time) could not be verified from an open citable source in this run.
- **Aggregate epfd↓ (Resolution 76, Table 1A), 10.7–12.75 GHz** — sum of all NGSO systems, per reference antenna:
  - 60 cm antenna (S.1428 pattern), 40 kHz: **−170 dBW/m² (0% of time), −168.6 (90%), −165.3 (99%), −160.4 (99.97%), −160 (99.99%), −160 (100%)**
  - 1.2 m: **−176.5 (0%), −173 (99.5%), −164 (99.84%), −161.5 (99.945%), −161 (100%)**
  - 3 m: **−185.3 (0%), −184 (99.97%), −180.8 (99.99%), −180 (100%)**
  - 10 m: **−191.5 (0%), −190 (99.97%), −189.8 (99.99%), −189 (100%)**
Sources: https://api-prod.fcc.gov/icfs-attachment/exp/api/v1/11e847291b5db610b2252062f54bcba3 (SES FCC filing, index); https://www.itu.int/hub/publication/R0C0A00000F0026/ (Resolution 76 text).

### 2e. Coordination triggers — Appendix 5 arcs and Appendix 8 ΔT/T

- **RR Appendix 5, Table 5-1 coordination arcs** (band-overlap + a GSO space station within ±arc of the nominal orbital position; NGSO–GSO coordination under No. 9.12A uses the same arcs relative to the GSO position). Per ITU WRS training material (post-WRC-15):
  - **±6°: Ku band** — FSS/BSS, BSS/FSS, FSS/SRS, SRS/FSS
  - **±7°: C band** — FSS/FSS
  - **±8°: Ka band and above** — FSS/FSS (also FSS/MetSat, MetSat/FSS at 18 GHz; FSS/BSS, BSS/FSS)
  - **±12°: 21.4–22 GHz (Regions 1 & 3)** — BSS/BSS
  - **±16°: Ka band** — FSS/BSS, BSS/FSS, BSS/BSS
  - So for **NGSO vs GSO in FSS bands: ±6° in Ku-band, ±8° in Ka-band and above**.
  Sources: https://WWW.ITU.INT/en/ITU-R/space/WRS18space/WRS18_Coordination_between_GSO_Networks_06122018.pdf (ITU WRS-18 training, index); confirmed for >17.3 GHz (±8°/±16°) in the ITU Space FAQ (https://www.itu.int/hub/space/faq/).
- **Appendix 8 ΔT/T criterion:** coordination under No. 9.7 is triggered when the calculated **ΔT/T exceeds 6%** (applies where no coordination arc is defined — e.g., NGSO vs GSO cases outside arcs and other services). Source: ITU-R BO.1505 (Annex 2) presentation, index.
- **Nos. 9.7A/9.7B specific-earth-station pfd triggers** (Rec. ITU-R S.1714-1): **10.7–12.75 GHz:** **−174.5 dB(W/(m²·40 kHz))** (NGSO with all satellites ≤2,500 km) or **−202** (any satellite >2,500 km); **17.8–18.6 / 19.7–20.2 GHz:** **−157 dB(W/(m²·MHz))** or **−185**. Source: https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-S.1714-1-2022-PDF-E.pdf (index).

### 2f. ITU-R S.1503 EPFD methodology

**Recommendation ITU-R S.1503-2** is the *functional description* to be used in developing software tools that check whether an NGSO FSS system complies with the Article 22 EPFD limits. What it simulates:
- computation of **epfd↓ (downlink), epfd↑ (uplink) and epfd-IS (inter-satellite)** statistics from the filed pfd and e.i.r.p. masks of the NGSO system;
- a **worst-case geometry (WCG) algorithm** plus time-stepped simulation of the constellation against reference GSO links/antennas;
- generation of **cumulative distribution functions (CDFs)** of epfd, compared point-by-point against the Article 22 / Resolution 76 masks.
Two independently developed implementations (Agenium, Transfinite) were cross-validated and agreed to **<0.1 dB**. Source: https://www.itu.int/en/ITU-R/space/snl/SNL/Supplement/S1503/R-REC-S.1503-2-201706-I!!PDF-E.pdf (index).

### 2g. WRC-23 decisions affecting NGSO

- **Resolution 8 (WRC-23)** — *tolerance of certain orbital characteristics* of NGSO FSS/BSS/MSS space stations: administrations must keep inclination, apogee/perigee altitudes and argument of perigee within declared tolerances (prevents "paper constellations" drifting from filings). https://www.itu.int/hub/publication/R0C0A0000110041/
- **Resolution 123 (WRC-23)** — NGSO **earth stations in motion (ESIMs)**: 17.7–18.6, 18.8–19.3, 19.7–20.2 GHz (space-to-Earth) and 27.5–29.1, 29.5–30 GHz (Earth-to-space). https://www.itu.int/hub/publication/R0C0A0000110054/
- **Resolution 35 revised** — post-milestone procedures and periodic orbital-characteristics reporting (see 2a).
- **Resolution 679 (WRC-23)** — **NGSO satellite-to-satellite (inter-satellite) links** in FSS bands 18.1–18.6, 18.8–20.2, 27.5–30 GHz; guard conditions include **pfd −110 dBW/(m²·200 MHz) in 18.6–18.8 GHz over oceans** and **e.i.r.p. 52.5 dBW/10 MHz in 27.5–30 GHz**.
- **Agenda item 1.19** — new FSS (space-to-Earth) allocation **17.3–17.7 GHz in Region 2** (GSO and NGSO).
- **EPFD work program** — studies invited for WRC-27 on possible revision of EPFD limits; **yearly aggregate-EPFD consultative meetings** institutionalized.
Source for WRC-23 package: https://www.lexology.com/library/detail.aspx?g=346339b2-4c2f-40d4-84a7-a4ae3e1b5e1f (legal analysis, index).

### Section 2 — summary table

| Instrument / document | Year | Key numeric requirements | Source URL |
|---|---|---|---|
| Res. 35 (WRC-19); revised WRC-23 | 2019 / 2023 | BIU = 1 sat in 7-yr period; milestones 10%/50%/100% at +2/+5/+7 yrs; bands 10.7–13.25, 13.75–14.5, 17.3–20.2, 27.5–30, 37.5–42.5, 47.2–51.4 GHz; WRC-23 adds reporting at 11 yrs then every 4 yrs | https://www.itu.int/en/mediacentre/backgrounders/Pages/Non-geostationary-satellite-systems.aspx |
| RR Art. 9 / Art. 11 filing | — | API → 4-mo comments → coordination (9.7/9.11A/9.12/9.12A/9.13/9.7A/9.7B) → notification → MIFR | https://www.itu.int/hub/space/faq/ |
| RR Art. 21 Table 21-4 | — | 10.7–11.7 GHz: −150/−126 dB(W/m²) (0–5°), +0.5(δ−5), −140/−116 (25–90°); 17.7–19.3 GHz: −115/−105 /MHz, +0.5(δ−5); NGSO ≥51 sats reduced by X (X=(5/119)(n−50), n≤288; X=(1/69)(n+402), n>288) | https://www.govregs.com/regulations/47/47CFR25.208 |
| RR Art. 22 Tables 22-1A–22-4; Res. 76 | — | Single-entry epfd↓ 10.7–12.75 GHz: −160 dBW/m²/40 kHz never-exceed; aggregate Res. 76 Table 1A e.g. 60 cm: −170/−168.6/−165.3/−160.4/−160/−160 at 0/90/99/99.97/99.99/100% time | https://www.itu.int/hub/publication/R0C0A00000F0026/ |
| RR App. 5 Table 5-1; App. 8 | — | Arcs: ±6° Ku FSS/BSS; ±7° C FSS/FSS; ±8° Ka+ FSS/FSS; ±12° 21.4–22 GHz BSS; ±16° Ka FSS/BSS; ΔT/T > 6% triggers coordination | https://WWW.ITU.INT/en/ITU-R/space/WRS18space/WRS18_Coordination_between_GSO_Networks_06122018.pdf |
| Rec. ITU-R S.1503-2 | 2017 | Functional spec for EPFD software; simulates epfd↓/↑/IS via masks + worst-case geometry; validated <0.1 dB | https://www.itu.int/en/ITU-R/space/snl/SNL/Supplement/S1503/R-REC-S.1503-2-201706-I!!PDF-E.pdf |
| WRC-23: Res. 8, Res. 123, Res. 679; AI 1.19 | 2023 | Orbital tolerances (Res. 8); NGSO ESIMs (Res. 123); NGSO inter-satellite links: −110 dBW/(m²·200 MHz) in 18.6–18.8 GHz over oceans, 52.5 dBW/10 MHz in 27.5–30 GHz (Res. 679); new R2 FSS 17.3–17.7 GHz s-E (AI 1.19) | https://www.lexology.com/library/detail.aspx?g=346339b2-4c2f-40d4-84a7-a4ae3e1b5e1f |

---

## 3. Other administrations' models (concise)

- **United Kingdom (Ofcom):** NGSO licensing under the Wireless Telegraphy Act with cost-based fees — **£500/year per NGSO gateway, £200/year per NGSO network**; gateway fees move to Administered Incentive Pricing from **early 2027** (statement 31 Mar 2026). Licence condition: each **gateway must be operational within 12 months of grant** (a milestone-like anti-warehousing lever). Orbital/debris licensing is separate, under the **Space Industry Act 2018** (UK Civil Aviation Authority). Source: https://www.ofcom.org.uk/siteassets/resources/documents/spectrum/licensing-and-certification/information-and-guidance-on-ngso-licensing-decisions-31-mar-2026.pdf (index).
- **France (ANFR/ARCEP; French Space Operations Act, Loi n° 2008-518, 3 June 2008):** national authorization for space operations; the **2023 revision** allows a **single authorization covering a whole constellation** (previously per-satellite); Technical Regulation updated **June 2024**; requires **deorbit within 25 years** and **third-party liability insurance ≥ €60M**. (Researched in prior session; figures from regulatory summaries — re-verify against the FSOA text before citing formally.)
- **European Union (EU Space Act proposal, June 2025; Council doc ST-7806-2026):** would impose **90% end-of-life disposal success rate**, **mandatory collision-avoidance services**, special measures for **constellations >100 satellites**, manoeuvrability requirements above **400 km**, penalties up to **2% of global turnover**, and an authorization fee of **~€100,000 per platform**. IRIS² (the EU secure-connectivity constellation) would operate under this framework once adopted — proposal only. Source: https://data.consilium.europa.eu/doc/document/ST-7806-2026-INIT/en/pdf (index).
- **Japan (MIC):** radio-station licensing under the **Radio Act**; space activities authorized under the **Space Activities Act (2016)** with debris-mitigation conditions; government funds competitiveness via the **Space Strategy Fund** and the **J-LEO** initiative (~$1B, with a Rakuten/AST SpaceMobile JV preliminarily selected). (Regulatory summaries; fee/debris specifics not re-verified this run.)
- **South Korea (MSIT/KASA):** satellite licensing under MSIT; **KASA (Korea AeroSpace Administration) established May 2024**; in **June 2025 MSIT granted OneWeb a LEO regulatory licence** — the first **cross-border satellite supply agreement** approved in Korea. (News reports; Korea-specific debris conditions not verified this run.)
- **Australia (ACMA):** space licences (space licence + space receive licence) under the **Space (Launches and Returns) Act 2018**; **Space Objects Determinations ASOD/FSOD 2025**; requires a **debris-mitigation strategy aligned with UN guidelines** per launch/return permit — no hard statutory disposal deadline yet; spectrum apparatus licences up to **20 years**. (Regulatory summaries.)
- **Singapore (IMDA):** **Satellite Orbital Slot Licence Guidelines v2 (23 Sept 2025)**: licensee must be **Singapore-incorporated**, satellite coverage must **include all of Singapore**, **TT&C and NOC in Singapore**, **≥50% effective ownership** of the satellite, and demonstrated familiarity with ITU RR; satellite communication station licence **$100/year per station** ($50 portable). Source: https://www.imda.gov.sg/-/media/imda/files/regulation-licensing-and-consultations/licensing-licenses/satellite-orbital-slot/5cbf608a-9b3b-47c3-a8cd-fdd2a0d81c2d.pdf (index).
- **Thailand (NBTC):** **landing-rights (Foreign Satellite Approval)** regime simplified 2026: **one-time fee THB 2,000,000 per Right per satellite filing** (for NGSO, **one Right = one entire system per licensee**), plus an **annual fee of 3.2% of the operator's satellite-business revenues in Thailand**; the Right is exclusive to one operator per satellite/system; orbital-slot licences carry replacement timelines and financial guarantees (e.g., Thaicom 50.5°E case). Source: https://www.fosrlaw.com/en/news-articles/2026/08/thailand-simplifies-satellite-landing-rights-regime (index).

### Section 3 — summary table

| Administration | Instrument / document | Year | Key numeric requirements | Source URL |
|---|---|---|---|---|
| UK | Ofcom NGSO licensing guidance | 2026 | Gateway £500/yr, network £200/yr; AIP from early 2027; gateway operational ≤12 months | https://www.ofcom.org.uk/siteassets/resources/documents/spectrum/licensing-and-certification/information-and-guidance-on-ngso-licensing-decisions-31-mar-2026.pdf |
| France | Space Operations Act (Loi n° 2008-518); 2023 revision | 2008 / 2023 | Single constellation authorization; deorbit ≤25 yrs; insurance ≥€60M | — (verify in FSOA text) |
| EU | EU Space Act proposal (ST-7806-2026) | 2025 (proposal) | 90% disposal success; collision avoidance mandatory; >100-sat measures; fine ≤2% turnover; ~€100k/platform fee | https://data.consilium.europa.eu/doc/document/ST-7806-2026-INIT/en/pdf |
| Japan | Radio Act; Space Activities Act | 2016 | Debris-mitigation licence conditions | — (not re-verified) |
| South Korea | MSIT licensing; KASA | 2024–2025 | OneWeb LEO licence June 2025 (first cross-border supply agreement) | — (news reports) |
| Australia | Space (Launches and Returns) Act 2018; ASOD/FSOD 2025 | 2018 / 2025 | Debris-mitigation strategy per permit; spectrum licences ≤20 yrs | — (regulatory summaries) |
| Singapore | IMDA Orbital Slot Licence Guidelines v2 | 2025 | SG-incorporated; coverage incl. all SG; TT&C/NOC in SG; ≥50% ownership; station licence $100/yr | https://www.imda.gov.sg/-/media/imda/files/regulation-licensing-and-consultations/licensing-licenses/satellite-orbital-slot/5cbf608a-9b3b-47c3-a8cd-fdd2a0d81c2d.pdf |
| Thailand | NBTC landing-rights regime | 2026 | THB 2,000,000 one-time per Right/system; 3.2%/yr of Thai satellite revenues; one system per licensee | https://www.fosrlaw.com/en/news-articles/2026/08/thailand-simplifies-satellite-landing-rights-regime |

---

## 4. Space sustainability

### 4a. IADC Space Debris Mitigation Guidelines

The **Inter-Agency Space Debris Coordination Committee (IADC) Space Debris Mitigation Guidelines** — first issued **2002**, revised as **Rev. 1 (2007)**, **Rev. 2 (2020)**, **Rev. 3 (2021)** — are the global baseline (endorsed in reduced form by UN COPUOS and the UN General Assembly in 2007). Core provisions:
- **Post-mission disposal, LEO (guideline 5.3.2):** spacecraft or orbital stages ending their operational life in orbits passing through or potentially interfering with the LEO region should be **deorbited (direct reentry preferred)** or manoeuvred into an orbit with an **expected residual orbital lifetime of ≤25 years**. The **probability of successful disposal must be ≥90%**. **For specific operations such as large constellations, a shorter residual orbital lifetime and/or a higher probability of success may be necessary.** Retrieval is also a recognized disposal option.
- **GEO graveyard (5.3.1):** minimum perigee raise of **235 km × (1000 × CR × A/m)** (CR = solar radiation pressure coefficient; A/m = area-to-dry-mass ratio), eccentricity **≤0.003**.
- **Passivation (5.2)** of stored energy at end of mission; **break-up avoidance** during operations (5.1).
- **Collision avoidance (5.4):** mission design must **estimate and limit the probability of accidental collision** with known objects over the orbital lifetime; **if reliable orbital data are available, avoidance manoeuvres and launch-window coordination may be used** when collision risk is not negligible; design must limit consequences of small-debris strikes that could prevent post-mission disposal.
Sources: https://sup1qywlxpbg9wylvrlmvhrlopvprl3qi.vcatalyst.top/library/iadc-space-debris-guidelines-revision-2.pdf (index); https://www.talksatellite.com/EMEA2331.html (index).

### 4b. Trend toward shorter post-mission disposal and collision-avoidance expectations

- **FCC 5-year rule (2022)** — the first major regulator to break from the 25-year norm (see §1c).
- **EU Space Act proposal (2025)** — **90% end-of-life disposal success rate** as a hard target and **mandatory collision-avoidance services** for operators (see §3).
- **UN COPUOS Guidelines for the Long-term Sustainability of Outer Space Activities (2019)** — 21 voluntary guidelines covering debris mitigation, conjunction assessment and information sharing; widely referenced in national licensing conditions (e.g., Australia's debris-mitigation strategy requirement). ⚠️ *Background knowledge; not sourced from a primary document in this run — verify against the COPUOS text before formal citation.*
- Net effect for large constellations: regulators increasingly expect **designed-in manoeuvrability, active conjunction screening and avoidance, passivation, and disposal timelines well under 25 years** — with the IADC guideline itself (5.3.2) already anticipating **stricter treatment for large constellations**.

### Section 4 — summary table

| Instrument / document | Year | Key numeric requirements | Source URL |
|---|---|---|---|
| IADC Space Debris Mitigation Guidelines (Rev. 3) | 2002 / 2021 | LEO residual lifetime ≤25 yrs; disposal success ≥90%; large constellations: shorter lifetime/higher probability may be needed; GEO perigee raise ≥235 km×(1000·CR·A/m), e ≤0.003 | https://sup1qywlxpbg9wylvrlmvhrlopvprl3qi.vcatalyst.top/library/iadc-space-debris-guidelines-revision-2.pdf |
| UN COPUOS Space Debris Mitigation Guidelines | 2007 (UNGA endorsement) | Reduced consensus set based on IADC | — (verify) |
| UN COPUOS Long-term Sustainability Guidelines | 2019 | 21 voluntary guidelines (debris, conjunctions, info sharing) | — (verify) |
| FCC 5-yr deorbit rule | 2022 | ≤5 yrs after mission end (LEO <2,000 km) | https://docs.fcc.gov/public/attachments/DA-25-256A1.pdf |
| EU Space Act proposal | 2025 (proposal) | 90% disposal success; mandatory collision avoidance | https://data.consilium.europa.eu/doc/document/ST-7806-2026-INIT/en/pdf |

---

## 5. Vietnam

### 5a. Legal documents on satellite frequency management

- **Law on Radio Frequencies (Law No. 42/2009/QH12, amended 2018):** the framework law; anyone wishing to use radio frequencies must obtain a licence. Licence types include **"frequency and satellite orbit use licences"** (giấy phép sử dụng tần số và quỹ đạo vệ tinh) — the direct legal hook for NGSO constellation authorization. Licensing principles require compliance with the Radio Frequency Master Plan; licences may be issued directly, by examination/selection, or by auction. Source: https://webiis08.mondaq.com/social-media/1288674/tmt-comparative-guide (index).
- **Authority of Radio Frequency Management (ARFM — Cục Tần số vô tuyến điện):** the specialized agency under the **Ministry of Science and Technology** (formerly the Ministry of Information and Communications) responsible for spectrum licensing, including satellite frequency and equipment approvals.
- **Operational precedent:** under the LEO pilot (see 5c), the **Radio Frequency Department separately approved Starlink's spectrum use and radio equipment** alongside the telecom licence — illustrating the dual licensing track (telecom service + frequency use) that foreign NGSO systems face. Source: https://www.thefreelibrary.com/Via%3e%3e%2b%2bt+Nam+opens+door+to+Starlink+to+boost+nationwide+digital...-a0875052860 (index).

### 5b. National space strategy to 2030 (and beyond)

- **Strategy on research into and application of aerospace technology to 2020** — **Decision No. 137/2006/QD-TTg (14 June 2006)**; created the policy framework and the Space Committee (see 5c).
- **Strategy for development and application of space science and technology to 2030** — signed by Prime Minister Nguyễn Xuân Phúc (**Decision No. 169/QD-TTg, 4 Feb 2021**). Goals: widely apply space S&T; selectively invest in defence/security, natural-resource and environmental management; build national capacity. Targets: **~300 experts and 3,000 engineers** trained in space S&T by 2030; **~10 specialized laboratories** upgraded; master technologies for **optical sensors/radars on Earth-observation satellites**, **in-country assembly/integration/testing of small satellites**, terminal devices, Earth stations and telecom-satellite transponders; develop national PNT capacity. Source: https://www.roc-taiwan.org/vn_en/post/3984.html (index).
- **Post-2030 orientation:** Vietnam aims for a **mid-level regional position by 2030** and, after 2030, **independent satellite-technology development** capability; the Prime Minister has directed work **toward a national space law** and major national programmes (Earth observation, shared satellite-data infrastructure). Source: https://www.thefreelibrary.com/PM+calls+for+accelerated+space+technology+development+in+Vietnam.-a0878528448 (index). ⚠️ **Flag:** no document explicitly titled "space strategy to 2040" was found; 2040-level specifics remain unverified.

### 5c. Role of the Vietnam Space Committee and ARFM

- **Vietnam Committee for Aerospace Technology Research and Application ("Vietnam Space Committee")** — established by **Decision No. 137/2006/QD-TTg** to **assist the Prime Minister in organizing and directing implementation of the space strategy**; the Committee itself was set up in **2010** and **enhanced in January 2013** to include representatives of national agencies, notably the **Ministry of National Defense**. Source: https://english.luatvietnam.vn/decision-no-137-2006-qd-ttg-dated-june-14-2006-of-the-prime-minister-approving-the-strategy-on-research-into-and-application-of-aerospace-technolo-18791-doc1.html (index).
- **ARFM (Cục Tần số vô tuyến điện):** the regulator that would license NGSO spectrum/orbit use under the Law on Radio Frequencies; it is the counterpart agency for any ITU filing and frequency-coordination work (Vietnam is the notifying administration for its satellite networks).
- **LEO pilot — Decision No. 659/QD-TTg (26 March 2025):** permits a **five-year pilot of LEO satellite telecommunications services without foreign-ownership limits**, subject to national defence/security requirements, concluding **before 1 January 2031**. Under it, the Authority of Telecommunications (MST) licensed **Starlink Services Vietnam Co., Ltd.** for satellite telecom services with network infrastructure, and the Radio Frequency Department approved spectrum/equipment use — rollout plan: **4 gateway stations and up to 600,000 user terminals** nationwide. Source: https://www.thefreelibrary.com/Via%3e%3e%2b%2bt+Nam+opens+door+to+Starlink+to+boost+nationwide+digital...-a0875052860 (index).

### Section 5 — summary table

| Instrument / document | Year | Key numeric requirements | Source URL |
|---|---|---|---|
| Law on Radio Frequencies (42/2009/QH12, amended 2018) | 2009 / 2018 | Licence types incl. "frequency and satellite orbit use licence"; licensing via direct grant, examination, or auction | https://webiis08.mondaq.com/social-media/1288674/tmt-comparative-guide |
| Decision 137/2006/QD-TTg | 2006 | Space strategy to 2020; established Vietnam Space Committee (set up 2010, enhanced Jan 2013 incl. Defense Ministry) | https://english.luatvietnam.vn/decision-no-137-2006-qd-ttg-dated-june-14-2006-of-the-prime-minister-approving-the-strategy-on-research-into-and-application-of-aerospace-technolo-18791-doc1.html |
| Decision 169/QD-TTg (space S&T strategy to 2030) | 2021 | 300 experts + 3,000 engineers by 2030; ~10 labs; in-country small-sat assembly/integration | https://www.roc-taiwan.org/vn_en/post/3984.html |
| Decision 659/QD-TTg (LEO pilot) | 2025 | 5-yr pilot, no foreign-ownership cap, ends before 1 Jan 2031; Starlink: 4 gateways + ≤600,000 terminals | https://www.thefreelibrary.com/Via%3e%3e%2b%2bt+Nam+opens+door+to+Starlink+to+boost+nationwide+digital...-a0875052860 |

---

## Could not verify / open questions

1. **Full Table 22-1A single-entry EPFD-down mask curve** (limit vs. percentage of time for 10.7–12.75 GHz) — only the −160 dBW/m²/40 kHz never-to-exceed anchor was verified from an open source (SES FCC filing). Needs the RR Article 22 text.
2. **Ku-band PFD Table 21-4 / EPFD exact footnote text in the RR itself** — values reported via the US CFR mirror (47 CFR 25.208 / 2.106); the underlying RR footnote wording (especially the X-factor reduction for large NGSO constellations) was not read directly from the Radio Regulations (the RR-2024 PDF download failed; not retried per guidance).
3. **France/Japan/South Korea/Australia specifics** (FSOA fee/debris figures; Japan's Radio Act conditions; Korea debris conditions; Australia's ASOD/FSOD content) — carried from prior-session research; recommend re-verification against primary texts before formal citation.
4. **No "space strategy to 2040" document found** — Vietnam's formal strategy runs to 2030; post-2030 goals exist only as policy statements (PM remarks, move toward a national space law).
5. **FCC Space Modernization NPRM (2025)** proposals (ITU-aligned milestones, de-escalating bond, 20-year terms) are **proposed, not adopted** — do not treat as current law.
6. **EU Space Act** figures are from a **2025 proposal** (Council doc ST-7806-2026), not adopted law.
7. All findings in this report are **index-sourced** (the live research browser was unavailable during this run); none was confirmed by a live in-browser read.

## Sources

Full source list with read dates and index/live flags is in `notes/fcc.md`, `notes/itu.md`, and `notes/admins-sustainability-vietnam.md` in this research directory. Key primary sources: FCC documents (docs.fcc.gov), ITU publications (itu.int hub/publication pages, WRS training materials, ITU-R Recommendations S.1503-2 and S.1714-1, Space FAQ), Ofcom (ofcom.org.uk), IMDA (imda.gov.sg), Council of the EU (data.consilium.europa.eu), luatvietnam.vn. Secondary/legal-analysis sources: Lexology, JD Supra, tlp.law, TelecomTV, ConnectivityBusiness, New America, TNGlobal, fosrlaw.com.
