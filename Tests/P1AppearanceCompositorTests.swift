import XCTest
import UIKit
@testable import MeadowJourney

/// The in-game head compositor must rebuild every shipped P1 map atlas from
/// the split sheets with each outfit's original head (step 1 of face/gender
/// customization). Offline, the split differs from the shipped atlases by at
/// most 1 colour level in 997 of ~200M pixels (8-bit rounding of pre-merged
/// soft edges); on device CoreGraphics premultiplied blending adds at most 1 more
/// level and differs from the offline bake in ~0.2% of pixels.
final class P1AppearanceCompositorTests: XCTestCase {
    private func pixels(_ image: CGImage) -> [UInt8] {
        let width = image.width, height = image.height
        var bytes = [UInt8](repeating: 0, count: width * height * 4)
        bytes.withUnsafeMutableBytes { buffer in
            let context = CGContext(data: buffer.baseAddress, width: width, height: height, bitsPerComponent: 8,
                                    bytesPerRow: width * 4, space: CGColorSpaceCreateDeviceRGB(),
                                    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
            context.interpolationQuality = .none
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        }
        return bytes
    }

    func testManifestCoversEveryShippedP1Atlas() throws {
        let manifest = try XCTUnwrap(P1AppearanceCompositor.manifest)
        XCTAssertEqual(manifest.groups, ["Directions", "Diagonals"])
        XCTAssertEqual(manifest.cell, 256); XCTAssertEqual(manifest.columns, 13); XCTAssertEqual(manifest.rows, 4)
        XCTAssertEqual(manifest.states.count, 20)
        for appearance in HeroFrames.appearanceIDs {
            XCTAssertNotNil(manifest.defaults[appearance])
            for weapon in ["none", "trainingSword", "huntingBow", "greatSword", "legendaryStaff"] {
                for armor in [nil, "leatherArmor", "runeArmor"] {
                    let key = P1AppearanceCompositor.stateKey(appearanceID: appearance, weaponID: weapon, armorID: armor)
                    XCTAssertNotNil(manifest.states[key], key)
                }
            }
        }
    }

    func testDefaultHeadsRebuildShippedAtlases() throws {
        var worst = 0, differing = 0, total = 0
        for (index, appearance) in HeroFrames.appearanceIDs.enumerated() {
            for weapon in ["none", "trainingSword", "huntingBow", "greatSword", "legendaryStaff"] {
                for armor in [nil, "leatherArmor", "runeArmor"] as [String?] {
                    try autoreleasepool {
                        let composed = try P1AppearanceCompositor.compose(
                            appearanceID: appearance, weaponID: weapon, armorID: armor,
                            head: P1AppearanceCompositor.defaultHead(appearanceID: appearance))
                        for (group, image) in composed.enumerated() {
                            let name = HeroFrames.atlasName(heroIndex: 0, diagonal: group == 1, appearanceIndex: index,
                                                            weaponID: weapon, armorID: armor)
                            let shipped = try XCTUnwrap(UIImage(named: name)?.cgImage, name)
                            XCTAssertEqual(image.width, shipped.width, name); XCTAssertEqual(image.height, shipped.height, name)
                            let a = pixels(image), b = pixels(shipped)
                            var atlasWorst = 0
                            for i in stride(from: 0, to: a.count, by: 4) {
                                var pixelWorst = 0
                                for c in 0..<4 { pixelWorst = max(pixelWorst, abs(Int(a[i + c]) - Int(b[i + c]))) }
                                if pixelWorst > 0 { differing += 1 }
                                atlasWorst = max(atlasWorst, pixelWorst)
                            }
                            total += a.count / 4
                            worst = max(worst, atlasWorst)
                            XCTAssertLessThanOrEqual(atlasWorst, 2, "\(name) differs by \(atlasWorst) levels")
                        }
                    }
                }
            }
        }
        // First on-device measurement (CI simulator run 42318430444): every atlas stays within 2 colour levels, but
        // CoreGraphics premultiplied blending of soft head edges rounds differently from the offline PIL bake for
        // ~0.19% of pixels. The per-atlas level bound above is the real guard; this only catches gross drift.
        XCTAssertLessThan(Double(differing) / Double(max(1, total)), 0.004, "\(differing) of \(total) pixels differ")
        print("P1AppearanceCompositor: worst \(worst), \(differing) of \(total) pixels differ")
    }

    func testSwappingHeadOnlyChangesHeadPixels() throws {
        let forester = P1AppearanceCompositor.defaultHead(appearanceID: "forester")
        let wayfarer = P1AppearanceCompositor.defaultHead(appearanceID: "wayfarer")
        XCTAssertNotEqual(forester, wayfarer)
        // Forester outfit with the wayfarer head must equal the wayfarer atlas only where heads are drawn:
        // check that the body (feet row of every cell) is unchanged.
        let swapped = try P1AppearanceCompositor.compose(appearanceID: "forester", weaponID: "trainingSword", armorID: nil, head: wayfarer)
        let original = try P1AppearanceCompositor.compose(appearanceID: "forester", weaponID: "trainingSword", armorID: nil, head: forester)
        let a = pixels(swapped[0]), b = pixels(original[0]), width = swapped[0].width
        var headChanged = false
        for y in 0..<swapped[0].height {
            let local = y % 256
            for x in 0..<width {
                let i = (y * width + x) * 4
                let same = a[i] == b[i] && a[i + 1] == b[i + 1] && a[i + 2] == b[i + 2] && a[i + 3] == b[i + 3]
                if local >= 150 { XCTAssertTrue(same, "body pixel changed at \(x),\(y)"); if !same { return } }
                else if !same { headChanged = true }
            }
        }
        XCTAssertTrue(headChanged)
    }
}
