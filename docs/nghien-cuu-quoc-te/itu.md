# Note: ITU Resolution 35 milestone approach
URLs (index, read 2026-10-19):
- https://www.itu.int/en/mediacentre/backgrounders/Pages/Non-geostationary-satellite-systems.aspx (BIU = 1 satellite in one orbital plane within 7-year regulatory period (11.48); Res 35 milestones: 10% within 2 yrs, 50% within 5 yrs, 100% within 7 yrs after end of 7-yr period; applies to FSS/MSS/BSS NGSO in 10.7-13.25, 13.75-14.5, 17.3-20.2, 27.5-30, 37.5-42.5, 47.2-51.4 GHz)
- https://www.itu.int/en/ITU-R/space/WRS20space/1-2-Non-GSO%20space%20station%20Milestone%20implementation%20and%20Res%2076%20(WRC-19)%20implementation.pdf (WRC-19 outcomes: same bands; aggregate EPFD verification from WRC-19)
- https://www.lexology.com/library/detail.aspx?g=346339b2-4c2f-40d4-84a7-a4ae3e1b5e1f (WRC-23: revised Res 35 with post-milestone provisions and orbital-characteristics reporting)
- https://www.itu.int/hub/publication/R0C0A0000110041/ (Res 8 WRC-23: tolerances on orbital characteristics)

# Note: ITU filing process + coordination triggers
URLs (index, read 2026-10-19):
- https://www.itu.int/hub/space/faq/ (FAQ: API -> coordination (9.7, 9.11A, 9.12, 9.12A, 9.13, 9.7A/9.7B) -> notification (Art 11) -> MIFR; EPFD examined at CR and notification; arc above 17.3 GHz: +-8 deg FSS-FSS, +-16 deg FSS-BSS)
- https://www.itu.int/dms_pub/itu-r/md/15/wrs18/c/R15-WRS18-C-0012!!PDF-E.pdf (WRS-18 App. 5 Table 5-1 rows: No. 9.7 +-6 deg for SRS/FSS Ku etc.; Ka rows +-8 deg; 21.4-22 GHz BSS +-12 deg)
- https://WWW.ITU.INT/en/ITU-R/space/WRS18space/WRS18_Coordination_between_GSO_Networks_06122018.pdf (trigger arcs: 6 deg FSS/BSS, BSS/FSS, FSS/SRS Ku; 7 deg FSS/FSS C-band; 8 deg FSS/FSS Ka+; 12 deg BSS/BSS 21.4-22 GHz R1&3; 16 deg FSS/BSS Ka)
- https://docbay.net/... (BO.1505: Delta-T/T > 6% triggers coordination under No. 9.7, App. 8)

# Note: ITU PFD / EPFD limits
URLs (index, read 2026-10-19):
- https://www.govregs.com/regulations/47/47CFR25.208 (mirrors RR Table 21-4: 10.7-11.7 GHz: -150 dBW/m2/4kHz (0-5 deg), +0.5(delta-5), -140 (25-90 deg); or -126/-116 dBW/m2/1MHz; 17.7-19.3 GHz: -115/-105 dBW/m2/MHz)
- https://www.govregs.com/regulations/47/47CFR2.106-21.16 (US footnote NGSO >=51 sats: reduce by X; X=(5/119)(n-50) for n<=288; X=(1/69)(n+402) for n>288)
- https://api-prod.fcc.gov/icfs-attachment/exp/api/v1/11e847291b5db610b2252062f54bcba3 (SES FCC filing Nov 18, 2025: Table 22-1A single-entry -160 dBW/m2/40kHz never-to-exceed; Res 76 aggregate Table 1A values; references BO.1505 (Annex 2) and Rec S.1714-1 triggers)
- https://www.itu.int/hub/publication/R0C0A00000F0026/ (Res 76 aggregate EPFD for 10.7-12.75 GHz)
- https://www.itu.int/en/ITU-R/space/snl/SNL/Supplement/S1503/R-REC-S.1503-2-201706-I!!PDF-E.pdf (S.1503-2: functional description for EPFD software; epfd-down/up/IS simulation; WCG algorithm; independent implementations agree <0.1 dB)
- https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-S.1714-1-2022-PDF-E.pdf (S.1714-1: 9.7A/9.7B triggers 10.7-12.75 GHz: -174.5 dB(W/(m2x40kHz)) NGSO all <=2500 km, or -202 any sat >2500 km; 17.8-18.6/19.7-20.2: -157 dB(W/(m2xMHz)) / -185)

# Note: WRC-23 NGSO decisions
URLs (index, read 2026-10-19):
- https://www.itu.int/hub/publication/R0C0A0000110054/ (Res 123: NGSO ESIMs 17.7-18.6, 18.8-19.3, 19.7-20.2 GHz s-E; 27.5-29.1, 29.5-30 GHz E-s)
- https://www.itu.int/hub/publication/R0C0A0000110041/ (Res 8: orbital characteristic tolerances)
- https://www.lexology.com/library/detail.aspx?g=346339b2-4c2f-40d4-84a7-a4ae3e1b5e1f (AI 1.19 new FSS s-E 17.3-17.7 GHz Region 2; AI 1.17 Res 679 NGSO inter-satellite links: 18.6-18.8 GHz pfd -110 dBW/(m2x200MHz) over oceans; 27.5-30 GHz e.i.r.p. 52.5 dBW/10MHz; EPFD studies for WRC-27; yearly aggregate-EPFD meetings; orbital-characteristics reporting 11 yrs then every 4 yrs)
