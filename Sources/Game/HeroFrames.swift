import SpriteKit

enum HeroFrames {
    static func load(_ hero: Int) -> [[SKTexture]] {
        // Real frame textures keep shader UVs local (0...1). A subtexture's
        // atlas coordinates must never be mistaken for leg or projection UVs.
        var rows = ["Directions", "Diagonals"].flatMap { suffix -> [[SKTexture]] in
            guard let atlas = UIImage(named: "Hero\(hero)\(suffix)")?.cgImage else {
                fatalError("Missing hero atlas: \(hero)\(suffix)")
            }
            let cell = atlas.width / 4
            return (0..<4).map { row in (0..<4).map { column in
                let rect = CGRect(x: column * cell, y: row * cell, width: cell, height: cell)
                guard let image = atlas.cropping(to: rect) else { fatalError("Invalid hero frame") }
                let texture = SKTexture(cgImage: image)
                texture.filteringMode = .nearest
                return texture
            } }
        }
        // The right-profile source is visibly a toe-raised, wide passing pose.
        // Reuse the complete left-profile animation and mirror it as a unit.
        rows[3] = rows[1]
        return rows
    }

    static func sourceFacing(_ facing: Int) -> Int {
        let normalized = ((facing % 8) + 8) % 8
        return normalized == 3 ? 1 : normalized
    }

    static func isMirrored(_ facing: Int) -> Bool {
        ((facing % 8) + 8) % 8 == 3
    }
}

/// A frame's lower-body correction, shared by the SpriteKit actor and the
/// Metal alpha-depth caster. The contact art is authored in a 4x4 atlas; the
/// front/back rows compress the projected foot separation much more than the
/// profile rows, so a small continuous leg warp supplements only those poses.
struct HeroPose {
    static let gridColumns = 8
    static let gridRows = 8
    static let referenceSize: CGFloat = 64

    // Projected distance between the two boot centers in a contact pair,
    // measured from the three generated atlases at 64pt display size. The
    // rear-facing feet overlap; their value is a conservative visual estimate.
    // Order follows HeroFrames: front, left, back, right, SE, SW, NW, NE.
    private static let measuredStride: [[CGFloat]] = [
        [1.1, 12.3, 1.0, 13.0, 8.2, 8.8, 6.1, 8.1],
        [1.0, 11.6, 1.0, 13.6, 5.4, 6.4, 6.0, 7.8],
        [0.3, 11.9, 1.0, 12.8, 6.3, 6.8, 6.8, 9.5]
    ]
    private static let targetStride: CGFloat = 12
    private static let maximumReach: CGFloat = 5.5

    /// Hero index is zero-based (0...2), matching GameScene's actor array.
    let heroIndex: Int
    let facing: Int
    let frame: Int
    /// Unit cycle phase, where frame 1 is contact A, frame 3 is contact B,
    /// and frame 2 is the passing pose on either half of the cycle.
    let phase: CGFloat

    init(heroIndex: Int, facing: Int, frame: Int, phase: CGFloat) {
        self.heroIndex = min(2, max(0, heroIndex))
        self.facing = ((facing % 8) + 8) % 8
        self.frame = min(3, max(0, frame))
        let wrapped = phase.truncatingRemainder(dividingBy: 1)
        self.phase = wrapped < 0 ? wrapped + 1 : wrapped
    }

    var measuredStridePoints: CGFloat {
        Self.measuredStride[heroIndex][HeroFrames.sourceFacing(facing)]
    }

    /// Extra travel for each lower leg at contact, in points at the 64pt
    /// gameplay size. Values are capped to keep the correction subordinate to
    /// the authored legs; both profiles stay untouched, including the user's
    /// already-approved left-facing baseline and its complete mirrored mate.
    var legReachPoints: CGFloat {
        guard frame != 0, HeroFrames.sourceFacing(facing) != 1 else { return 0 }
        return min(Self.maximumReach, max(0, (Self.targetStride - measuredStridePoints) / 2))
    }

    /// The source-image left half is the stance leg from contact A (phase 0) through the
    /// first half-cycle; it sweeps backward until contact B (phase 0.5). The
    /// other leg takes stance for the second half. Passing poses use zero
    /// stride correction while both contact poses use opposite extrema. A
    /// linear drive keeps the planted sole moving backward as the actor root
    /// advances. Its travel is capped by `maximumReach` because several source
    /// atlases already carry part of the stride in their authored frames.
    var legDrive: CGFloat {
        guard frame != 0 else { return 0 }
        return phase < 0.5 ? 1 - 4 * phase : -3 + 4 * phase
    }

    /// Keep the actor root on its path. Foot travel belongs in the two lower-leg
    /// mesh regions; shifting the whole sprite would cancel that travel and move
    /// the head, caster root, and interaction point along with the feet.
    func bodyOffset(size: CGSize = CGSize(width: referenceSize, height: referenceSize)) -> CGPoint {
        _ = size
        return .zero
    }

    /// Nonuniform grid points put vertices through the legs and fade the warp
    /// into the hips. SpriteKit and the Metal caster consume the same arrays.
    var sourcePositions: [SIMD2<Float>] {
        Self.yCoordinates.flatMap { y in xCoordinates.map { SIMD2($0, y) } }
    }

    func destinationPositions() -> [SIMD2<Float>] {
        let heading = Self.localHeading[facing]
        let reach = Float(legReachPoints / Self.referenceSize)
        let drive = Float(legDrive)
        return sourcePositions.map { point in
            let side = legSide(at: point.x)
            let weight = Self.lowerLegWeight(at: point.y)
            let travel = reach * drive * side * weight
            return SIMD2(point.x + heading.x * travel,
                         point.y + heading.y * travel)
        }
    }

    func warpGeometry() -> SKWarpGeometryGrid {
        SKWarpGeometryGrid(columns: Self.gridColumns, rows: Self.gridRows,
                           sourcePositions: sourcePositions,
                           destinationPositions: destinationPositions())
    }

    private var xCoordinates: [Float] {
        // NW boots occupy roughly x=0.38 and x=0.50, rather than opposite
        // halves of the image. Put the transition BETWEEN those boots: the
        // former center at 0.50 left the right boot almost stationary.
        if facing == 6 { return [0, 0.20, 0.32, 0.395, 0.445, 0.495, 0.58, 0.80, 1] }
        return [0, 0.20, 0.34, 0.40, 0.50, 0.60, 0.66, 0.80, 1]
    }
    // SpriteKit's normalized warp coordinates are bottom-origin.
    private static let yCoordinates: [Float] = [0, 0.125, 0.18, 0.25, 0.32, 0.40, 0.55, 0.76, 1]

    // Node-local coordinates (positive y is up), in the logical direction
    // order. Facing right reuses left-profile art and is mirrored by the node,
    // so its source-space walk vector remains leftward before that transform.
    private static let localHeading: [SIMD2<Float>] = [
        SIMD2(0, -1), SIMD2(-1, 0), SIMD2(0, 1), SIMD2(-1, 0),
        SIMD2(0.70710677, -0.70710677), SIMD2(-0.70710677, -0.70710677),
        SIMD2(-0.70710677, 0.70710677), SIMD2(0.70710677, 0.70710677)
    ]

    private func legSide(at x: Float) -> Float {
        if facing == 6 { return max(-1, min(1, (0.445 - x) / 0.050)) }
        if x <= 0.40 { return 1 }
        if x >= 0.60 { return -1 }
        return 1 - (x - 0.40) * 10
    }

    private static func lowerLegWeight(at y: Float) -> Float {
        if y <= 0.18 { return 1 }
        if y >= 0.42 { return 0 }
        let t = (y - 0.18) / 0.24
        let smooth = t * t * (3 - 2 * t)
        return 1 - smooth
    }
}
