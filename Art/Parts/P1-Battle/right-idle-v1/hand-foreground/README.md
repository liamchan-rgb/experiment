# Far-hand foreground ownership correction

The old static semantic split assigned a small patch of rear-leg skin at y≥177 to the far-hand part. Repeating that entire part in front of clothes restores bare-leg pixels over trousers. This registered copy keeps only the actual far-hand region above y177 on the unchanged 256×256 canvas. The approved complete r2 body is still drawn unchanged underneath; no anatomy is removed or hidden. The original semantic split is preserved.

`build.sh` is a deterministic ownership correction for this one pose. It neither redraws the hand nor establishes a complete moving hand module. This candidate has no additional user approval.
