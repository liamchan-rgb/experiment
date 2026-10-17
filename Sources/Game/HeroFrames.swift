import SpriteKit

enum HeroFrames {
    static let walkFrameCount = 24
    static let columns = walkFrameCount + 1 // idle, then a complete two-step cycle
    static let atlasRows = 4

    static func load(_ hero: Int) -> [[SKTexture]] {
        ["Directions", "Diagonals"].flatMap { suffix -> [[SKTexture]] in
            guard let atlas = UIImage(named: "Hero\(hero)\(suffix)")?.cgImage else {
                fatalError("Missing hero atlas: \(hero)\(suffix)")
            }
            let cell = atlas.width / columns
            precondition(atlas.width == cell * columns && atlas.height == cell * atlasRows)
            return (0..<atlasRows).map { row in (0..<columns).map { column in
                let rect = CGRect(x: column * cell, y: row * cell, width: cell, height: cell)
                guard let image = atlas.cropping(to: rect) else { fatalError("Invalid hero frame") }
                let texture = SKTexture(cgImage: image)
                texture.filteringMode = .nearest
                return texture
            } }
        }
    }

    static func sourceFacing(_ facing: Int) -> Int { ((facing % 8) + 8) % 8 }
    static func isMirrored(_ facing: Int) -> Bool { false }

    /// Foreground and native alpha-depth pass address the same authored pose.
    static func atlasRect(facing: Int, frame: Int) -> SIMD4<Float> {
        SIMD4(Float(frame) / Float(columns), Float(sourceFacing(facing) % atlasRows) / Float(atlasRows),
              1 / Float(columns), 1 / Float(atlasRows))
    }
}

/// Limb motion is drawn in whole frames. Neither foreground nor shadow caster
/// stretches or splices pixels around a knee.
struct HeroPose {
    private struct Footprint: Decodable { let feet: [[Float]] }
    private struct Rig: Decodable { let heroes: [[[Footprint]]] }
    private static let rig: Rig = {
        guard let url = Bundle.main.url(forResource: "hero-gait", withExtension: "json"),
              let data = try? Data(contentsOf: url), let rig = try? JSONDecoder().decode(Rig.self, from: data) else {
            fatalError("Missing authored gait footprint data")
        }
        return rig
    }()
    static let gridColumns = 8
    static let gridRows = 8
    static let referenceSize: CGFloat = 64
    let heroIndex: Int
    let facing: Int
    let frame: Int
    let phase: CGFloat
    private let firstFoot: SIMD2<Float>
    private let secondFoot: SIMD2<Float>

    init(heroIndex: Int, facing: Int, frame: Int, phase: CGFloat) {
        let hero = min(2, max(0, heroIndex)), direction = HeroFrames.sourceFacing(facing)
        let column = min(HeroFrames.walkFrameCount, max(0, frame))
        self.heroIndex = hero
        self.facing = direction
        self.frame = column
        let wrapped = phase.truncatingRemainder(dividingBy: 1)
        self.phase = wrapped < 0 ? wrapped + 1 : wrapped
        let feet = Self.rig.heroes[hero][direction][column].feet
        let a = SIMD2(feet[0][0], feet[0][1]), b = SIMD2(feet[1][0], feet[1][1])
        firstFoot = a.x <= b.x ? a : b
        secondFoot = a.x <= b.x ? b : a
    }

    func bodyOffset(size: CGSize = CGSize(width: referenceSize, height: referenceSize)) -> CGPoint { .zero }

    // Retain relief tessellation and the exact sole-height row, with identity
    // positions for every animation phase.
    var sourcePositions: [SIMD2<Float>] {
        (0...Self.gridRows).flatMap { row in
            (0...Self.gridColumns).map { column in
                SIMD2(Float(column) / Float(Self.gridColumns), Float(row) / Float(Self.gridRows))
            }
        }
    }
    func destinationPositions() -> [SIMD2<Float>] { sourcePositions }

    /// Bottom-origin ground line, including each planted foot's depth. A foot
    /// behind the root belongs on the receiver rather than floating above it.
    func groundLine(at u: Float) -> Float {
        let a = firstFoot, b = secondFoot
        let t = abs(b.x - a.x) < 0.001 ? 0.5 : max(0, min(1, (u - a.x) / (b.x - a.x)))
        return 1 - (a.y * (1 - t) + b.y * t)
    }
}
