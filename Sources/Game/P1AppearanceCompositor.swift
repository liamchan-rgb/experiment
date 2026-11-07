import UIKit

/// Head parts chosen for P1, by slot ("face.eyes", "hair.front", ...) -> variant id.
/// A missing slot falls back to the outfit's default head.
struct P1HeadSelection: Codable, Equatable {
    var parts: [String: String] = [:]
}

/// Stacks the split P1 sheets (scripts/build-p1-head-split.py) into the same
/// 13 x 4 x 256 atlas layout as the shipped Hero1/P1* atlases, so every
/// existing consumer (sprite frames, shadow caster, inventory preview) can use
/// the result unchanged. Order: under -> hair.back -> body -> eyes -> brows ->
/// nose -> mouth -> hair.front. Hands never overlap the head in any authored
/// cell, so drawing the head above the hands changes no pixel.
enum P1AppearanceCompositor {
    struct Manifest: Decodable {
        struct State: Decodable {
            let under: [String]
            let body: [String]
            let weapon: String
            let armor: String?
        }
        let schemaVersion: Int
        let cell: Int
        let columns: Int
        let rows: Int
        let groups: [String]
        let stackOrder: [String]
        let states: [String: State]
        /// slot -> variant -> [Directions sheet, Diagonals sheet]
        let headParts: [String: [String: [String]]]
        /// outfit -> slot -> variant
        let defaults: [String: [String: String]]
    }

    enum CompositorError: Error, LocalizedError {
        case missingManifest, unknownState(String), unknownPart(String, String), missingImage(String), context
        var errorDescription: String? {
            switch self {
            case .missingManifest: return "外观合成清单缺失"
            case .unknownState(let key): return "外观合成缺少装备状态：\(key)"
            case .unknownPart(let slot, let variant): return "外观部件不存在：\(slot) \(variant)"
            case .missingImage(let name): return "外观合成素材缺失：\(name)"
            case .context: return "外观合成画布分配失败"
            }
        }
    }

    static let manifest: Manifest? = {
        guard let data = NSDataAsset(name: "P1HeadSplitManifest")?.data else { return nil }
        return try? JSONDecoder().decode(Manifest.self, from: data)
    }()

    /// Same key the offline split uses: outfit (or armor) + weapon, e.g.
    /// "ForesterTrainingSword", "LeatherArmorNone".
    static func stateKey(appearanceID: String, weaponID: String?, armorID: String?) -> String {
        func title(_ text: String) -> String { text.prefix(1).uppercased() + text.dropFirst() }
        return title(armorID ?? appearanceID) + title(weaponID ?? "none")
    }

    /// Head parts the shipped atlas for `appearanceID` was baked with.
    static func defaultHead(appearanceID: String) -> P1HeadSelection {
        P1HeadSelection(parts: manifest?.defaults[appearanceID] ?? [:])
    }

    /// Available variants per slot, for the customization screen.
    static var variants: [String: [String]] {
        (manifest?.headParts ?? [:]).mapValues { $0.keys.sorted() }
    }

    /// Two atlases (Directions, Diagonals) in the shipped layout.
    static func compose(appearanceID: String, weaponID: String?, armorID: String?,
                        head: P1HeadSelection, image: (String) -> CGImage? = { UIImage(named: $0)?.cgImage }) throws -> [CGImage] {
        guard let manifest else { throw CompositorError.missingManifest }
        let key = stateKey(appearanceID: appearanceID, weaponID: weaponID, armorID: armorID)
        guard let state = manifest.states[key] else { throw CompositorError.unknownState(key) }
        let defaults = manifest.defaults[appearanceID] ?? [:]
        let width = manifest.cell * manifest.columns, height = manifest.cell * manifest.rows
        return try manifest.groups.indices.map { group -> CGImage in
            var names: [String] = []
            for layer in manifest.stackOrder {
                switch layer {
                case "under": names.append(state.under[group])
                case "body": names.append(state.body[group])
                default:
                    guard let variant = head.parts[layer] ?? defaults[layer] else { continue }
                    guard let sheets = manifest.headParts[layer]?[variant] else { throw CompositorError.unknownPart(layer, variant) }
                    names.append(sheets[group])
                }
            }
            guard let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: 8, bytesPerRow: width * 4,
                                          space: CGColorSpaceCreateDeviceRGB(),
                                          bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { throw CompositorError.context }
            context.interpolationQuality = .none
            context.setBlendMode(.normal)
            let rect = CGRect(x: 0, y: 0, width: width, height: height)
            for name in names {
                // Decode one sheet at a time; release before the next to bound memory.
                try autoreleasepool {
                    guard let sheet = image(name), sheet.width == width, sheet.height == height else {
                        throw CompositorError.missingImage(name)
                    }
                    context.draw(sheet, in: rect)
                }
            }
            guard let result = context.makeImage() else { throw CompositorError.context }
            return result
        }
    }
}
