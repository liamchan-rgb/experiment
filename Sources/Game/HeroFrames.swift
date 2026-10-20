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

    /// Baked output of the layered P1 shoe-color prototype. The art is authored
    /// as transparent layers offline, then packed for the app's normal atlas path.
    static func loadLayeredP1BlueVariant() -> [SKTexture] {
        guard let atlas = UIImage(named: "LayeredP1BlueVariant")?.cgImage else {
            fatalError("Missing layered P1 colorway preview")
        }
        let cell = atlas.height
        precondition(cell == 256 && atlas.width == cell * walkFrameCount,
                     "Layered P1 colorway atlas must be 24 square frames")
        let strip = SKTexture(cgImage: atlas)
        return (0..<walkFrameCount).map { column in
            let rect = CGRect(x: CGFloat(column) / CGFloat(walkFrameCount), y: 0,
                              width: 1 / CGFloat(walkFrameCount), height: 1)
            let texture = SKTexture(rect: rect, in: strip)
            texture.filteringMode = .nearest
            return texture
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
    private let firstFoot: SIMD3<Float>
    private let secondFoot: SIMD3<Float>

    init(heroIndex: Int, facing: Int, frame: Int, phase: CGFloat) {
        let hero = min(2, max(0, heroIndex)), direction = HeroFrames.sourceFacing(facing)
        let column = min(HeroFrames.walkFrameCount, max(0, frame))
        self.heroIndex = hero
        self.facing = direction
        self.frame = column
        let wrapped = phase.truncatingRemainder(dividingBy: 1)
        self.phase = wrapped < 0 ? wrapped + 1 : wrapped
        let feet = Self.rig.heroes[hero][direction][column].feet
        let a = SIMD3(feet[0][0], feet[0][1], feet[0][2]), b = SIMD3(feet[1][0], feet[1][1], feet[1][2])
        firstFoot = a
        secondFoot = b
    }

    func bodyOffset(size: CGSize = CGSize(width: referenceSize, height: referenceSize)) -> CGPoint { .zero }

    // Retain relief tessellation and the exact sole-height row, with identity
    // positions for every animation phase.
    var sourcePositions: [SIMD2<Float>] {
        let feet = footLandmarks
        let xs = Self.stops([0, 0.15, 0.30, 0.50, 0.70, 0.85, 1, feet[0].x, feet[1].x])
        let ys = Self.stops([0, 0.125, 0.25, 0.40, 0.55, 0.75, 1, feet[0].y, feet[1].y])
        return ys.flatMap { y in xs.map { x in SIMD2(x, y) } }
    }

    private static func stops(_ values: [Float]) -> [Float] {
        var result: [Float] = []
        for value in values.sorted() where result.last.map({ abs($0 - value) > 0.000001 }) ?? true { result.append(value) }
        while result.count < 9 {
            var widestGapIndex = 0
            var widestGapWidth: Float = -1
            for index in 0..<(result.count - 1) {
                let gapWidth = result[index + 1] - result[index]
                if gapWidth > widestGapWidth {
                    widestGapWidth = gapWidth
                    widestGapIndex = index
                }
            }
            let midpoint = (result[widestGapIndex] + result[widestGapIndex + 1]) * 0.5
            result.insert(midpoint, at: widestGapIndex + 1)
        }
        return result
    }

    /// x/y are exact source-art landmarks, z is lift in image-height units.
    /// Include these points in the depth mesh so a boot cannot miss the ground
    /// because its foot falls between coarse regular grid vertices.
    var footLandmarks: [SIMD3<Float>] {
        [Self.landmark(firstFoot), Self.landmark(secondFoot)]
    }

    private static func landmark(_ foot: SIMD3<Float>) -> SIMD3<Float> {
        SIMD3(foot.x, 1 - foot.y + foot.z * 0.8660254, foot.z * 0.8660254)
    }

    func destinationPositions() -> [SIMD2<Float>] { sourcePositions }

    /// Both feet can overlap in x while occupying different depths. Select
    /// their ground depth in two image dimensions, then blend back to the
    /// body's root plane above the legs to keep the torso relief stable.
    func groundLine(at point: SIMD2<Float>) -> Float {
        let first = Self.landmark(firstFoot), second = Self.landmark(secondFoot)
        func squared(_ foot: SIMD3<Float>) -> Float {
            let dx = point.x - foot.x, dy = point.y - foot.y
            return dx * dx + dy * dy
        }
        let da = squared(first), db = squared(second)
        let ground: Float
        if da < 0.00000001 { ground = 1 - firstFoot.y }
        else if db < 0.00000001 { ground = 1 - secondFoot.y }
        else {
            let a = 1 / (da * da), b = 1 / (db * db)
            ground = ((1 - firstFoot.y) * a + (1 - secondFoot.y) * b) / (a + b)
        }
        let t = max(0, min(1, (point.y - 0.22) / 0.20))
        let blend = t * t * (3 - 2 * t)
        return ground * (1 - blend) + 0.125 * blend
    }
}
