# Su-30SM/SM2 HIGH reference-slot repair — 2026-11-08

This revision supersedes the 2026-11-07 identity layout. The user's in-game images showed actual rectangular label backgrounds and triangular fin-root fragments. The prior “one SUKHOI / large SU-30 / small plant name” layout did not reproduce reference slot semantics.

## Correspondence

| Reference slot | SM | SM2 |
|---|---|---|
| AVIC manufacturer (three original slots) | SUKHOI | SUKHOI |
| Large hatched fin NORINCO | IRKUTSK | IRKUTSK |
| Five 015/016 number slots | 30SM | 30SM2 |
| Three-line wing-root title | SU-30 / SM / IRKUTSK | SU-30 / SM2 / IRKUTSK |
| Small wing bureau / code | SUKHOI / SU-30SM | SUKHOI / SU-30SM2 |
| WS10B3 / AVIC TAIHANG ENGINE | AL-31FP / ENGINE SYSTEM | AL-41F1S / ENGINE SYSTEM |
| ENDFIELD / 01 / world graphics | Preserve | Preserve |

Small original captions and signatures follow their existing reference slots. No invented service unit or tactical serial is added. Exact guide boxes, rotations, tight erase boxes and hatch periods are in schema-2 marking recipes. Number glyphs have angular slashed zeros; manufacturer glyphs are condensed and sheared. Preserve aspect ratio. Apply hatching after final transform.

## Actual clipping and material repair

Do not paste text onto a freshly filled rectangle. Restore the reference substrate, erase only original ink, and apply glyph alpha. Repair C and packed-normal R/B together, retaining native G/A and color alpha. White paint reference samples from J16/J15T/J10C give R=102/B=178. R is inverted roughness and B is metallicity; these are artistic reference coating values, not a universal physical aircraft material.

The big fin lettering belongs to the island hit at guide pixel (1140,440): SM 6605, SM2 6608. Those IDs are bound to exact geometry hashes. Adjacent UV fin faces must be excluded from BOTH lettering and substrate sampling. Recover the original light/dark macro field from hatch gaps rather than extrapolating a plane through the diagonal band.

Fin-root repair uses barycentric native XYZ per pixel. Below-origin Y vertices and the forward leading root must be included; a centroid-only test or X<-3.1/Y>-.1 leaves visible triangular remnants. The final fades, protected world-art boxes, mask arrays and deterministic generator are published in the surface recipes. Restore from pre-root images for every run. Stored 8-bit weights are review/scope data; regenerate float weights for exact blending.

## Verification boundary

Fresh extraction from the current game resource pack reproduced library XYZ and UV exactly for both models. Current native normal G/A resized bicubic to 4096 matches repaired G/A exactly. Pixel checks cover allowed scope, ENDFIELD preservation, protected graphics and DDS/PNG roundtrip. Static rendered evidence is recorded separately with exact texture hashes, cameras and light presets. Comparative Blender PBR uses real C, R/B and decoded G/A; it does not reproduce every Dagor shader behavior. In-game animation, damage and other LODs remain unverified.

Official references: [SM](https://wiki.warthunder.com/unit/su_30sm), [SM2](https://wiki.warthunder.com/unit/su_30sm2), [packed texture channels](https://wiki.warthunder.com/cdk/creation_camo).
