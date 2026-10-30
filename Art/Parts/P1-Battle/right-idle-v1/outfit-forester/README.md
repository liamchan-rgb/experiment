# P1 blue wardrobe colorway candidate

`wardrobe.png` is the same pose-locked, full-canvas 256×256 clothing layer for the approved right-idle r2 body, recolored to match the blue signature of P1 on the map. The pixel geometry, alpha silhouette, gold trim, charcoal trousers, brown boots, and sole registration are unchanged. This remains an unreviewed single-frame candidate.

Run `./build.sh` from this directory to reproduce it. The script point-resizes the retained 1254×1254 `source/registered-chromakey.png` to the full 256×256 canvas, removes the magenta key, rebuilds the boot selection with an explicit luminance-to-alpha conversion, and adds editable SVG underlap clipped to the approved body's alpha silhouette. It then shifts only the green tunic palette to a brighter, more saturated P1 blue in HSL while preserving the source alpha channel and all non-green pixels. It does not alter or conceal the body layer.

Registration is fixed to the approved body canvas: jacket collar starts at y=126; the left trouser/boot zone is x=87..113, y=170..213; the right trouser/boot zone is x=122..165, y=170..213. The sole baseline is y=214, with the final output clipped to rows 0..213. Boots are translated upward by four source pixels while the collar and rest of the garment retain their registered coordinates. Foot underlap uses deep brown `#4a2b1b` inside the body-alpha foot masks and is layered above trouser underlap, then below the boot texture. SVG repair shapes and the boot selection remain editable in `source/`.

`review-runtime-order.png` is a visual check on gray using the neutral body, wardrobe, and the two provided hand layers in runtime order. Hair, face, and weapon are omitted. A reviewer should assess the remaining edge cleanup and fit before treating this as approved art.

Final composite review also extended the charcoal trouser underlap across the far upper-thigh guide at (99,177,14,9), below the actual far fist. This removes a bare-thigh sliver without covering the hand or changing the neutral source.
