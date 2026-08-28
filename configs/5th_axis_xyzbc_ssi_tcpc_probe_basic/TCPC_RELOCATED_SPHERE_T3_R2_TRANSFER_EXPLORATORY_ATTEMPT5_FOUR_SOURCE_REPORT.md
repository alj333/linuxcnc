# T3 R2-Transfer Attempt-5 Four-Source Composite Report

## R2 NOT ACCEPTED

- exploratory classification: `MIXED`
- direct composite: `A1 seq1-14 + A2 seq15-22 + A4 seq23 + A5 seq24-31; no source alignment`
- composite result/state rows: `31 / 31`
- formal same-acquisition `31 / 31 / 14`: `NOT SATISFIED`
- reason: accepted rows span mode30/attempt1 and mode31/attempts2/4/5; only four closures are validated within one source
- validated source-local/cross-source diagnostics: `4 / 10`
- A1 contact/gap rows: `119 / 119`
- A2 contact/gap rows: `64 / 65`
- A3 forensic accepted/contact/gap rows: `0 / 2 / 3`
- A4 contact/gap rows: `8 / 8`
- A5 contact/gap rows: `64 / 64`
- A5 complete rejected try-1 poses: `0`
- maximum validated source-local closure: `0.034535 mm`
- equal-20 baseline RMS/max: `0.251154900 / 0.617559442 mm`
- equal-20 R2 counterfactual RMS/max: `0.148716274 / 0.328314143 mm`
- raw-31 baseline RMS/max: `0.221010740 / 0.650679707 mm`
- raw-31 R2 counterfactual RMS/max: `0.149044164 / 0.352449968 mm`
- centered T3-minus-T4 equal-20 mismatch RMS/max: `0.164423503 / 0.264629483 mm`
- maximum unique-pose worsening: `0.119218671 mm` at `(90, 0)`

## Closure Diagnostics

| scope | block | opening provenance | closing provenance | dx mm | dy mm | dz mm | norm mm | formal_pass |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| validated source-local | 100 | mode30/attempt1/seq1 | mode30/attempt1/seq5 | 0.002696 | 0.005929 | -0.000492 | 0.006532 | PASS |
| validated source-local | 45 | mode30/attempt1/seq6 | mode30/attempt1/seq10 | -0.003320 | 0.004659 | 0.000576 | 0.005750 | PASS |
| validated source-local | 90 | mode31/attempt2/seq17 | mode31/attempt2/seq21 | 0.032605 | 0.000284 | -0.011381 | 0.034535 | PASS |
| validated source-local | 200 | mode31/attempt5/seq27 | mode31/attempt5/seq31 | -0.002964 | 0.007967 | 0.001166 | 0.008580 | PASS |
| cross-source | -45 | mode30/attempt1/seq11 | mode31/attempt2/seq15 | -0.022264 | 0.004475 | -0.012790 | 0.026063 | N/A |
| cross-source | 905 | mode30/attempt1/seq5 | mode31/attempt2/seq16 | -0.031150 | 0.009546 | -0.005638 | 0.033064 | N/A |
| cross-source | -90 | mode31/attempt2/seq22 | mode31/attempt5/seq26 | 0.046061 | -0.042295 | 0.001270 | 0.062547 | N/A |
| cross-source | 911 | mode30/attempt1/seq1 | mode31/attempt5/seq27 | 0.008339 | -0.025552 | -0.012240 | 0.029534 | N/A |
| cross-source | 906 | mode31/attempt2/seq16 | mode31/attempt5/seq27 | 0.036793 | -0.041027 | -0.006110 | 0.055446 | N/A |
| cross-source | 912 | mode30/attempt1/seq2 | mode31/attempt5/seq28 | 0.005363 | -0.028578 | -0.010578 | 0.030941 | N/A |
| cross-source | 913 | mode30/attempt1/seq3 | mode31/attempt5/seq29 | 0.000618 | -0.026171 | -0.011416 | 0.028559 | N/A |
| cross-source | 914 | mode30/attempt1/seq4 | mode31/attempt5/seq30 | 0.002690 | -0.023054 | -0.006415 | 0.024081 | N/A |
| cross-source | 915 | mode30/attempt1/seq5 | mode31/attempt5/seq31 | 0.002679 | -0.023514 | -0.010582 | 0.025924 | N/A |
| cross-source | 900 | mode30/attempt1/seq1 | mode31/attempt5/seq31 | 0.005375 | -0.017585 | -0.011074 | 0.021465 | N/A |

The four validated source-local PASS values apply only to their original
source acquisition. They do not convert this split composite into formal
same-acquisition evidence. Cross-source `formal_pass=N/A` is retained.

Cross-source rows are offline diagnostics with explicit provenance.
They are not controller closure rows, and the 0.050 mm same-acquisition
closure limit is not applied to them.

## Pass-Center Context

- T3 A1 seq1-14 min/max: `0.001133 / 0.025854 mm`
- T3 A2 seq15-22 min/max: `0.003072 / 0.047429 mm`
- T3 A4 seq23: `0.001387 mm`
- T3 A5 seq24-31 min/max: `0.001698 / 0.015579 mm`
- T3 composite min/max: `0.001133 / 0.047429 mm`
- immutable T4 matching-grid min/max: `0.000813 / 0.022114 mm`

| T3 seq | pose | readout | T3 provenance | T3 pass-center delta mm | T4 mode23 source seq | T4 pass-center delta mm |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 1 | B+0/C0 |  | mode30/attempt1 | 0.025854 | 1 | 0.021196 |
| 2 | B+0/C90 |  | mode30/attempt1 | 0.002096 | 3 | 0.000813 |
| 3 | B+0/C180 |  | mode30/attempt1 | 0.001616 | 5 | 0.003141 |
| 4 | B+0/C270 |  | mode30/attempt1 | 0.002107 | 7 | 0.004562 |
| 5 | B+0/C0 |  | mode30/attempt1 | 0.001930 | 9 | 0.009282 |
| 6 | B+45/C0 |  | mode30/attempt1 | 0.011615 | 62 | 0.003336 |
| 7 | B+45/C90 |  | mode30/attempt1 | 0.003850 | 63 | 0.001633 |
| 8 | B+45/C180 |  | mode30/attempt1 | 0.003424 | 64 | 0.008216 |
| 9 | B+45/C270 |  | mode30/attempt1 | 0.001133 | 65 | 0.008940 |
| 10 | B+45/C0 |  | mode30/attempt1 | 0.003493 | 66 | 0.009691 |
| 11 | B-45/C0 |  | mode30/attempt1 | 0.011825 | 67 | 0.002497 |
| 12 | B-45/C90 |  | mode30/attempt1 | 0.001715 | 68 | 0.011459 |
| 13 | B-45/C180 |  | mode30/attempt1 | 0.003756 | 69 | 0.014714 |
| 14 | B-45/C270 |  | mode30/attempt1 | 0.012012 | 70 | 0.009463 |
| 15 | B-45/C0 |  | mode31/attempt2 | 0.007797 | 71 | 0.008671 |
| 16 | B+0/C0 |  | mode31/attempt2 | 0.004305 | 72 | 0.008390 |
| 17 | B+90/C0 |  | mode31/attempt2 | 0.003101 | 83 | 0.013599 |
| 18 | B+90/C90 |  | mode31/attempt2 | 0.004500 | 84 | 0.005669 |
| 19 | B+90/C180 | PRIMARY | mode31/attempt2 | 0.022050 | 85 | 0.005541 |
| 20 | B+90/C270 |  | mode31/attempt2 | 0.003072 | 86 | 0.007147 |
| 21 | B+90/C0 |  | mode31/attempt2 | 0.015667 | 87 | 0.007218 |
| 22 | B-90/C0 |  | mode31/attempt2 | 0.047429 | 88 | 0.009442 |
| 23 | B-90/C90 |  | mode31/attempt4 | 0.001387 | 89 | 0.022114 |
| 24 | B-90/C180 | PRIMARY | mode31/attempt5 | 0.014595 | 90 | 0.003794 |
| 25 | B-90/C270 |  | mode31/attempt5 | 0.004536 | 91 | 0.006766 |
| 26 | B-90/C0 |  | mode31/attempt5 | 0.015579 | 92 | 0.020749 |
| 27 | B+0/C0 |  | mode31/attempt5 | 0.001698 | 93 | 0.009785 |
| 28 | B+0/C90 |  | mode31/attempt5 | 0.002234 | 95 | 0.005868 |
| 29 | B+0/C180 |  | mode31/attempt5 | 0.002064 | 97 | 0.004238 |
| 30 | B+0/C270 |  | mode31/attempt5 | 0.002730 | 99 | 0.004425 |
| 31 | B+0/C0 |  | mode31/attempt5 | 0.003689 | 101 | 0.004266 |

Pass-center deltas are preserved repeatability context, not exclusion
weights. Seq19 B+90/C180 and seq24 B-90/C180 remain mandatory readouts.

## Local Contrasts

`D(B,C) = center(B,C) - mean(center(B,C0-open), center(B,C0-close))`.
The immutable T4 reference uses the same 31 occurrence keys selected by
the frozen scorer from the sealed mode23/attempt1 acquisition.

| pose | readout | T3 dx mm | T3 dy mm | T3 dz mm | T3 norm mm | T4 dx mm | T4 dy mm | T4 dz mm | T4 norm mm | T3-T4 dx mm | T3-T4 dy mm | T3-T4 dz mm | T3-T4 norm mm |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B+45/C90 | SOURCE-LOCAL | 0.019227 | -0.099242 | 0.069113 | 0.122456 | -0.176041 | 0.012125 | 0.023487 | 0.178014 | 0.195268 | -0.111368 | 0.045626 | 0.229378 |
| B+45/C180 | SOURCE-LOCAL | 0.059999 | 0.133444 | 0.081198 | 0.167332 | -0.390817 | 0.232570 | -0.011381 | 0.454924 | 0.450816 | -0.099126 | 0.092579 | 0.470778 |
| B+45/C270 | SOURCE-LOCAL | -0.013570 | 0.040727 | 0.001678 | 0.042961 | -0.345770 | 0.015998 | -0.017436 | 0.346579 | 0.332200 | 0.024729 | 0.019114 | 0.333667 |
| B-45/C90 | CROSS-SOURCE-SENSITIVE | -0.220076 | 0.020039 | -0.047655 | 0.226066 | -0.050672 | -0.001705 | 0.041903 | 0.065776 | -0.169404 | 0.021743 | -0.089559 | 0.192850 |
| B-45/C180 | CROSS-SOURCE-SENSITIVE | -0.377452 | 0.060077 | -0.002979 | 0.382215 | -0.050472 | 0.137804 | 0.089180 | 0.171728 | -0.326980 | -0.077728 | -0.092158 | 0.348497 |
| B-45/C270 | CROSS-SOURCE-SENSITIVE | -0.103287 | -0.495063 | 0.052385 | 0.508429 | 0.031755 | -0.523599 | 0.114248 | 0.536858 | -0.135041 | 0.028536 | -0.061863 | 0.151253 |
| B+90/C90 | SOURCE-LOCAL | 0.090553 | -0.435337 | -0.005697 | 0.444691 | 0.031221 | -0.343386 | -0.037317 | 0.346816 | 0.059331 | -0.091951 | 0.031619 | 0.113907 |
| B+90/C180 | PRIMARY SOURCE-LOCAL | 0.349876 | 0.063338 | 0.018750 | 0.356056 | 0.005543 | 0.176031 | 0.006230 | 0.176228 | 0.344332 | -0.112693 | 0.012520 | 0.362520 |
| B+90/C270 | SOURCE-LOCAL | 0.128324 | -0.100268 | -0.078468 | 0.180771 | -0.151296 | -0.113933 | -0.017735 | 0.190225 | 0.279620 | 0.013665 | -0.060734 | 0.286466 |
| B-90/C90 | CROSS-SOURCE-SENSITIVE | -0.167670 | -0.286125 | -0.064034 | 0.337759 | 0.035481 | -0.365790 | 0.021319 | 0.368125 | -0.203151 | 0.079666 | -0.085353 | 0.234312 |
| B-90/C180 | PRIMARY CROSS-SOURCE-SENSITIVE | -0.207470 | 0.076310 | 0.066689 | 0.230899 | 0.038473 | 0.214956 | 0.082941 | 0.233593 | -0.245943 | -0.138645 | -0.016252 | 0.282797 |
| B-90/C270 | CROSS-SOURCE-SENSITIVE | -0.025615 | -0.729162 | 0.031579 | 0.730294 | 0.089134 | -0.675163 | 0.023734 | 0.681435 | -0.114749 | -0.053999 | 0.007845 | 0.127061 |

Every contrast cancels one common global translation. T3 D(-45,C) is
nevertheless CROSS-SOURCE-SENSITIVE because its C0 opening seq11 is A1
and its C0 closing seq15 is A2. T3 D(-90,C) is also
CROSS-SOURCE-SENSITIVE: its C0 opening seq22 is A2, B-90/C90 seq23
is A4, and its remaining tilted centers plus C0 closing seq26 are A5.
D(+45,C) and D(+90,C) are
source-local and invariant to a constant translation of their own source. The T4
contrasts are all source-local. No contrast, quadrant, or T3-minus-T4
value adds an acceptance gate or receives a source-alignment correction.

## Paired-Sign Components

`even=(D(+B,C)+D(-B,C))/2`; `odd=(D(+B,C)-D(-B,C))/2`.

| abs(B) | C | readout | T3 even x mm | T3 even y mm | T3 even z mm | T3 even norm mm | T3 odd x mm | T3 odd y mm | T3 odd z mm | T3 odd norm mm |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 45 | 90 | CROSS-SOURCE-SENSITIVE | -0.100425 | -0.039602 | 0.010729 | 0.108483 | 0.119652 | -0.059641 | 0.058384 | 0.145884 |
| 45 | 180 | CROSS-SOURCE-SENSITIVE | -0.158726 | 0.096760 | 0.039110 | 0.189964 | 0.218726 | 0.036684 | 0.042089 | 0.225739 |
| 45 | 270 | CROSS-SOURCE-SENSITIVE | -0.058428 | -0.227168 | 0.027032 | 0.236115 | 0.044858 | 0.267895 | -0.025353 | 0.272805 |
| 90 | 90 | CROSS-SOURCE-SENSITIVE | -0.038559 | -0.360731 | -0.034866 | 0.364457 | 0.129112 | -0.074606 | 0.029168 | 0.151943 |
| 90 | 180 | PRIMARY CROSS-SOURCE-SENSITIVE | 0.071203 | 0.069824 | 0.042719 | 0.108491 | 0.278673 | -0.006486 | -0.023970 | 0.279777 |
| 90 | 270 | CROSS-SOURCE-SENSITIVE | 0.051355 | -0.414715 | -0.023445 | 0.418540 | 0.076970 | 0.314447 | -0.055024 | 0.328373 |

| abs(B) | C | readout | T4 even x mm | T4 even y mm | T4 even z mm | T4 even norm mm | T4 odd x mm | T4 odd y mm | T4 odd z mm | T4 odd norm mm | T3-T4 even norm mm | T3-T4 odd norm mm |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 45 | 90 | T3 CROSS-SOURCE-SENSITIVE | -0.113357 | 0.005210 | 0.032695 | 0.118093 | -0.062684 | 0.006915 | -0.009208 | 0.063733 | 0.051555 | 0.205535 |
| 45 | 180 | T3 CROSS-SOURCE-SENSITIVE | -0.220645 | 0.185187 | 0.038899 | 0.290674 | -0.170172 | 0.047383 | -0.050280 | 0.183662 | 0.107950 | 0.399860 |
| 45 | 270 | T3 CROSS-SOURCE-SENSITIVE | -0.157008 | -0.253800 | 0.048406 | 0.302340 | -0.188762 | 0.269799 | -0.065842 | 0.335794 | 0.104326 | 0.237111 |
| 90 | 90 | T3 CROSS-SOURCE-SENSITIVE | 0.033351 | -0.354588 | -0.007999 | 0.356243 | -0.002130 | 0.011202 | -0.029318 | 0.031457 | 0.077011 | 0.167356 |
| 90 | 180 | T3 PRIMARY CROSS-SOURCE-SENSITIVE | 0.022008 | 0.195493 | 0.044585 | 0.201717 | -0.016465 | -0.019462 | -0.038356 | 0.046055 | 0.134968 | 0.295772 |
| 90 | 270 | T3 CROSS-SOURCE-SENSITIVE | -0.031081 | -0.394548 | 0.003000 | 0.395782 | -0.120215 | 0.280615 | -0.020734 | 0.305984 | 0.088891 | 0.202983 |

B+90/C180 and B-90/C180 contribute explicitly to the abs(B)=90/C180
even/odd row; neither pose is searched for or excluded after acquisition.
Every T3 even/odd row inherits a negative-sign acquisition boundary:
D(-45,C) spans A1/A2 and D(-90,C) spans A2/A4/A5. No source translation
is applied.

## B45-vs-B90 Angle Scale

Diagnostic only. `delta D = D(sign*90,C) - D(sign*45,C)` and the
reported ratio is `||D(sign*90,C)|| / ||D(sign*45,C)||`. No value in
this table is an acceptance gate, fitted scale, or coefficient update.

| data | B sign | C | sensitivity | delta-D x mm | delta-D y mm | delta-D z mm | delta-D norm mm | norm ratio B90/B45 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| T3 composite | + | 90 | SOURCE-LOCAL | 0.071326 | -0.336095 | -0.074810 | 0.351630 | 3.631453 |
| T3 composite | + | 180 | SOURCE-LOCAL | 0.289876 | -0.070106 | -0.062449 | 0.304701 | 2.127837 |
| T3 composite | + | 270 | SOURCE-LOCAL | 0.141895 | -0.140995 | -0.080147 | 0.215492 | 4.207838 |
| T3 composite | - | 90 | CROSS-SOURCE-SENSITIVE | 0.052406 | -0.306163 | -0.016379 | 0.311047 | 1.494069 |
| T3 composite | - | 180 | CROSS-SOURCE-SENSITIVE | 0.169982 | 0.016234 | 0.069668 | 0.184421 | 0.604108 |
| T3 composite | - | 270 | CROSS-SOURCE-SENSITIVE | 0.077672 | -0.234098 | -0.020806 | 0.247523 | 1.436374 |
| T4 mode23 | + | 90 | SOURCE-LOCAL | 0.207262 | -0.355511 | -0.060804 | 0.415984 | 1.948247 |
| T4 mode23 | + | 180 | SOURCE-LOCAL | 0.396360 | -0.056539 | 0.017610 | 0.400760 | 0.387379 |
| T4 mode23 | + | 270 | SOURCE-LOCAL | 0.194474 | -0.129931 | -0.000299 | 0.233886 | 0.548865 |
| T4 mode23 | - | 90 | SOURCE-LOCAL | 0.086153 | -0.364085 | -0.020584 | 0.374705 | 5.596621 |
| T4 mode23 | - | 180 | SOURCE-LOCAL | 0.088945 | 0.077152 | -0.006238 | 0.117910 | 1.360250 |
| T4 mode23 | - | 270 | SOURCE-LOCAL | 0.057380 | -0.151564 | -0.090514 | 0.185626 | 1.269301 |

All negative-sign T3 B45-vs-B90 rows combine split-source D(-45,C)
and D(-90,C) references. Their vector differences and norm ratios remain unaligned
diagnostics and do not enter the frozen gates.

## Electrical Burst Diagnostics

A5 requires every successful direct G38 edge delta to be exactly
raw/mux/gated 1/1/1. Matched raw/mux post-contact repeats and
inter-contact gaps with gated delta 0 remain diagnostic even when their
logged burst flag is 1. Raw/mux mismatch, gated repeat/gap activity,
counter reversal, consistency, release, terminal, or no-touch evidence
is invalid.

- post-contact repeat events / burst rows / raw edges: `0 / 0 / 0`
- gap events / burst rows / raw edges: `0 / 0 / 0`

| scope | seq | try | pass | contact | raw delta | mux delta | gated delta | combined extra | burst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| none | N/A | N/A | N/A | N/A | 0 | 0 | 0 | 0 | 0 |

These rows are preserved acquisition diagnostics only. They do not
alter source alignment, closure treatment, the frozen score, or gates.
The bounded ready guard requires two consecutive clear 0.05 s samples
within 10.00 s before every G38 and then repeats all final guards.
The sealed A4 pulse snapshot found no defensible debounce boundary:
accepted/gated n=167 high-time min/median/max was 39.935/50.005/50.940 ms;
ungated faults n=608 was 39.872/49.998/100.098 ms. A later live, unsealed
observation reached n=762 with the same summary and remains context only.
Reseat/reset plus fresh quiet qualification remains an operator precondition.

## Frozen Gates

- PASS: equal20 RMS improvement
- PASS: equal20 max improvement
- PASS: positive-B RMS improvement
- PASS: negative-B RMS improvement
- PASS: B0 RMS non-worsening
- FAIL: maximum pose worsening
- FAIL: equal20 ceiling
- FAIL: raw31 ceiling

## Overlap Sensitivity

This optional five-pose, equal-weight recovery-to-A1 translation is reported
only as acquisition-boundary sensitivity. The recovery side is explicitly
mixed-source: A2 supplies B-45/C0 and B0/C0 seq16; A5 supplies the closing
B0 sweep, while the B0/C0 recovery value averages A2 and A5 occurrences.
It was not used for closures,
gates, classification, centering, or the frozen R2 score.

- estimated mixed-recovery-to-A1 translation XYZ: `0.003970867, 0.017102633, 0.010153533 mm`
- overlap unaligned RMS/max: `0.025734797 / 0.030941201 mm`
- overlap translation-aligned RMS/max: `0.015840381 / 0.028410983 mm`

The counterfactual adds the immutable, pose-keyed T4 R2 deltas to the
direct composite T3 centers using the original single global centering.
No T3 coefficient, rotation, scale, row deletion, or per-source
translation was fitted. This report cannot accept R2 or authorize a
machine calibration parameter change.
