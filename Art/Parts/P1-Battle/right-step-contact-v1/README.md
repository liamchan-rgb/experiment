# Battle side step · first clothed key pose

The user accepted the current battle presentation and requested the next step on 2026-10-21. The original plan resumes with a small right-facing step: foreground boot planted, rear heel raised, sword held ready. The full-character review is `review.png`; the native source is `assembled.png`.

The head, readable facial features, tapered hair, jacket, rear-shoulder shading, belt, hands and sword retain the exact v9 pixels above y=180. The clothing below that line fits the separate common neutral action module in `Art/Templates/P1-Neutral/battle-side/right-step-contact-v1`. No appearance ID changes the body or pose.

The retained generation supplies lower-clothing texture at a fixed 0.2 scale and (0,+5px) registration. `coverage-underpaint.svg` follows the common body's leg silhouette and supplies trouser/boot overlap; the generated texture is clipped to that body. This corrects the first trial's exposed neutral-leg edges without altering the body to fit clothes. The failed first assembly remains in `drafts/`.

Run `build-review.sh` to reproduce the wardrobe layer and composition. This is one unapproved new key pose for review. It is not imported into the application and does not represent a completed walk animation, attack or interchangeable wardrobe contract. The accepted idle appearance remains in the demo.
