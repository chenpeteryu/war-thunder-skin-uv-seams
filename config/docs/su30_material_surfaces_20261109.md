> Current final C touchup: see [2026-11-10 continuous-root and label revision](su30_touchup_20261110.md). Older root native-C fades are superseded.

# SM/SM2 HIGH material follow-up — 2026-11-09

The user's new in-game screenshots invalidate a claim that the earlier static review proved correct runtime materials. The actual issue is visible in raw packed-channel data: millions of painted SM/SM2 pixels contain R/B near 50/88, whereas the corresponding physical surfaces of the installed J16 and J15T references use 102/178. The difference affects wings, fixed fins and rudders relative to the body and canards. A clean albedo preview does not verify this.

## Corrected pipeline

Use raw R/B values directly, not a color-managed normal-map preview or rendered PNG as numeric channel data. The reviewed paint mask is corrected to 102/178, with native mechanical geometry excluded. Native G/A stays exact to a fresh extraction from the current game. This is an artistic reference match, not a universal real-world aircraft material claim.

LERX correction is separate C work. The approved thick graphics, colored accents and identity lettering are protected. Neutral white coating is 186 with small high-frequency native details admitted only where native GA supports them. A native-world feather joins the surrounding paint. This removes foreign projected panel fragments and irregular substrate tone without filling an atlas rectangle.

The actual front door is gear_c6. Main doors use gear_l9/r9 and gear_l14/r14. Both native winding-Y sides are separate masks: front sides 85; main inner sides 18; main exterior sides 159/161, from physical-area-weighted reference sampling. G/A, legs, actuators and wheels are preserved. Do not assume the same part number names identify the same physical panel on different aircraft: the small target gear_c11 is excluded.

Canard dark band and yellow edge remain unchanged. The originally clipped ENDFIELD caption is erased locally and fitted inside the true chord/span footprint with correct per-face readability, retaining the same text and font. Canard R/B is verified as 102/178; restoring the other painted surfaces to that same reference material resolves their mismatch. Fins and rudders likewise retain approved C artwork; no extra root color band is introduced.

## Reuse and evidence

The two material_surface_20261109 recipes contain exact geometry hashes, pre-repair input hashes, packed masks and a deterministic replay tool. Native source C is required for restricted microscopic structure; full original artwork is not distributed. Replay from the saved inputs must reproduce both final C and N exactly, not just approximately match mask counts. This rule runs after source projection, continuity and marking operations. Earlier marking R/B values are superseded by the raw reference coating policy.

Local records retain rejected partial/full canard transfer attempts and the reverted root-tone boost. Final static before/after comparisons, coating mask checks, fresh-native GA checks and installed file hashes are separate evidence. Static Blender renders do not prove the full Dagor shader or moving/open gear state. Do not label runtime verified without observing the actual game.

Official packed-channel reference: https://wiki.warthunder.com/cdk/creation_camo

## Nose artwork follow-up

The user clarified that nose brightness is lighting. The final nose correction changes C artwork only; N is byte-identical to the saved pre-nose state. The old whole-fuse max-X ratio included the long SM pitot; true skin extents are about13.0736 for J16 and13.0346 for SM/SM2. Per-section ellipse-normalized angular correspondence and native source triangle UVs recover the radome join, calibration circle, warning bars and maintenance text. The parameter-domain error threshold is not a 3D positional alignment claim. Approved marking regions are unchanged. Foreign source interior/hardware samples are excluded from skin artwork, and native optical details are preserved. A raw reference C file is required for exact replay and is not distributed.
