# build38 · Up-left descending-foot transition

Version1.6.12 build38 corrects the P1 up-left walk's abrupt01→02 landing. A new whole pose02 adds a near-contact left boot and keeps the right boot planted; pose03 completes the weight transfer. The authored cadence stays120ms. Only up-left02 and its three matching runtime foot samples change.

[Full-body comparison](../../Art/Review/P1/directions/up-left/revisions/contact-r1/candidate-compare.png), [complete cycle](../../Art/Review/P1/directions/up-left/revisions/contact-r1/review-2x.png), [normal-speed loop](../../Art/Review/P1/directions/up-left/revisions/contact-r1/walk.gif), [normal-speed road composition](road-motion-four-directions-offline.gif), [parent review](art-review.json). The road composition uses production paths/art but simplifies terrain and shadows; it is offline review evidence, not a device or GPU capture. Original r6/loop-r1, selected and rejected generation sources and exact prompts are retained.

Full-body proportions, boot descent, continuous support and07→08→01→02→03 are internally reviewed. That does not constitute user approval of new artwork. Device Release archive39742884627 and all three build-host Swift checks passed; IPA CRC, arm64/iPhoneOS, version, stored-ZIP, executable permissions, compiled assets/Metal library, bundled gait JSON and remote package SHA all match. See [package metadata](package.json) and [build checks](build-checks.txt); no simulator or physical-device run is performed. The user handles device motion and screenshots. Build37's playable forest encounter remains included.

[Package metadata](package.json) records the source commit and workflow artifacts. Anonymous raw GET returned HTTP200, application/octet-stream,24,201,944 bytes and SHA256 `d36b0a78bb48345fd829ce3967d139faeb3d604020c4250cdabca485ae5673fe`, matching the downloaded IPA and remote packaging log.

Direct IPA:

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b38.ipa
```
