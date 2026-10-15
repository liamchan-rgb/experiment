import simd

/// The lab uses one world: X right, Y along the ground, Z height; ground is Z=0.
/// Sprite landmarks and shadow geometry share the same per-instance ground root.
struct ShadowLabVertex {
    var position: SIMD4<Float>
    var uvWind: SIMD4<Float>
    var color: SIMD4<Float>
}

struct ShadowLabUniforms {
    var camera: simd_float4x4
    var light: simd_float4x4
    var sunTime: SIMD4<Float>
    var options: SIMD4<Float> // shadow on, inverse map size, wind on, unused
}

struct ShadowLabFrame {
    var time: Float = 0
    var sunAngle: Float = -0.65
    var shadows = true
    var wind = true
    var artwork = true
    var models = false
    var zoom: Float = 1
    var seed: UInt64 = 1
    var heroFrame: Int? = nil
}

enum ShadowLabAsset: String {
    case tree = "OakA", tower = "WatchTower", hero = "Hero1Directions"
}

struct ShadowLabInstance {
    let asset: ShadowLabAsset
    let root: SIMD3<Float>
    let width: Float
    let aspect: Float
    /// Normalized image coordinates measured from the lower-left corner.
    let anchor: SIMD2<Float>
    var screenHeight: Float { width * aspect }
    var cardHeight: Float { screenHeight / ShadowLabMath.cameraUp.z }
    var height: Float { cardHeight * (1 - anchor.y) }

    func imagePoint(_ u: Float, _ vFromTop: Float) -> SIMD3<Float> {
        root + SIMD3((u - anchor.x) * width, 0, (1 - vFromTop - anchor.y) * cardHeight)
    }
}

enum ShadowLabMath {
    static let cameraUp = simd_normalize(SIMD3<Float>(0, 28, 20))

    static func lookAt(eye: SIMD3<Float>, target: SIMD3<Float>, up: SIMD3<Float>) -> simd_float4x4 {
        let f = simd_normalize(target - eye)
        let r = simd_normalize(simd_cross(f, up))
        let u = simd_cross(r, f)
        return simd_float4x4(columns: (
            SIMD4(r.x, u.x, -f.x, 0), SIMD4(r.y, u.y, -f.y, 0),
            SIMD4(r.z, u.z, -f.z, 0), SIMD4(-simd_dot(r, eye), -simd_dot(u, eye), simd_dot(f, eye), 1)))
    }

    /// Right-handed orthographic projection with Metal's 0...1 depth interval.
    static func orthographic(halfWidth: Float, halfHeight: Float, near: Float, far: Float) -> simd_float4x4 {
        simd_float4x4(columns: (SIMD4(1 / halfWidth, 0, 0, 0), SIMD4(0, 1 / halfHeight, 0, 0),
                              SIMD4(0, 0, 1 / (near - far), 0), SIMD4(0, 0, near / (near - far), 1)))
    }

    static func camera(aspect: Float, zoom: Float) -> simd_float4x4 {
        let target = SIMD3<Float>(0, 0, 2.8)
        let view = lookAt(eye: target + SIMD3(0, -20, 28), target: target, up: SIMD3(0, 0, 1))
        let halfHeight = max(6.1, 11.4 / max(aspect, 0.1)) / zoom
        return orthographic(halfWidth: halfHeight * aspect, halfHeight: halfHeight, near: 0.1, far: 100) * view
    }

    static func sun(angle: Float) -> SIMD3<Float> {
        simd_normalize(SIMD3(sin(angle) * 0.85, cos(angle) * 0.85, 1.2))
    }

    static func light(sun: SIMD3<Float>) -> simd_float4x4 {
        let target = SIMD3<Float>(0, 0, 2)
        return orthographic(halfWidth: 18, halfHeight: 18, near: 0.1, far: 80)
            * lookAt(eye: target + sun * 35, target: target, up: SIMD3(0, 0, 1))
    }

    static func instances(seed: UInt64, time: Float) -> [ShadowLabInstance] {
        // One shared record drives both passes; re-layout never places art and shadows separately.
        let offset: Float = seed == 1 ? 0 : Float(Int(seed % 5) - 2) * 0.38
        let depth: Float = seed == 1 ? 0 : Float(Int((seed / 3) % 5) - 2) * 0.28
        let travel = (time * 0.75).truncatingRemainder(dividingBy: 7)
        return [
            ShadowLabInstance(asset: .tree, root: SIMD3(-5.2 + offset, 1 + depth, 0), width: 5,
                              aspect: 553.0 / 516, anchor: SIMD2(0.50, 0.09)),
            ShadowLabInstance(asset: .tower, root: SIMD3(4.0 - offset, 1.1 - depth, 0), width: 4.4,
                              aspect: 499.0 / 388, anchor: SIMD2(0.50, 0.14)),
            ShadowLabInstance(asset: .hero, root: SIMD3(3.5 - travel, -3.0 + depth, 0), width: 2.6,
                              aspect: 1, anchor: SIMD2(0.50, 0.125))
        ]
    }

    static func heroFrame(time: Float) -> Int { [1, 2, 3, 2][Int(max(0, time) * 7) % 4] }
}

struct ShadowLabMesh {
    var vertices: [ShadowLabVertex] = []
    var wind: Float = 0
    var phase: Float = 0
    var color = SIMD4<Float>(0.85, 0.66, 0.29, 0.55)

    mutating func triangle(_ a: SIMD3<Float>, _ b: SIMD3<Float>, _ c: SIMD3<Float>) {
        for p in [a, b, c] {
            vertices.append(ShadowLabVertex(position: SIMD4(p, 1), uvWind: SIMD4(0, 0, wind > 0 ? max(0, p.z / wind) : 0, phase), color: color))
        }
    }

    mutating func box(center: SIMD3<Float>, size: SIMD3<Float>, rotation: Float = 0) {
        let corners: [SIMD3<Float>] = (0..<8).map { i in
            let p = SIMD3<Float>(i & 1 == 0 ? -0.5 : 0.5, i & 2 == 0 ? -0.5 : 0.5, i & 4 == 0 ? -0.5 : 0.5) * size
            return center + SIMD3(cos(rotation) * p.x - sin(rotation) * p.y, sin(rotation) * p.x + cos(rotation) * p.y, p.z)
        }
        for face in [[0, 2, 3, 1], [4, 5, 7, 6], [0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5]] {
            triangle(corners[face[0]], corners[face[1]], corners[face[2]])
            triangle(corners[face[0]], corners[face[2]], corners[face[3]])
        }
    }

    mutating func ellipsoid(center: SIMD3<Float>, radii: SIMD3<Float>, segments: Int = 10, rings: Int = 6) {
        func point(_ i: Int, _ j: Int) -> SIMD3<Float> {
            let a = Float(i) / Float(segments) * .pi * 2
            let b = Float(j) / Float(rings) * .pi
            return center + SIMD3(cos(a) * sin(b), sin(a) * sin(b), cos(b)) * radii
        }
        for j in 0..<rings { for i in 0..<segments {
            triangle(point(i, j), point(i + 1, j), point(i + 1, j + 1))
            triangle(point(i, j), point(i + 1, j + 1), point(i, j + 1))
        } }
    }

    mutating func beam(from a: SIMD3<Float>, to b: SIMD3<Float>, radius: Float, sides: Int = 7) {
        let n = simd_normalize(b - a)
        let tangent = simd_normalize(simd_cross(n, abs(n.z) < 0.9 ? SIMD3(0, 0, 1) : SIMD3(0, 1, 0)))
        let bitangent = simd_cross(n, tangent)
        func ring(_ i: Int) -> SIMD3<Float> {
            let angle = Float(i) * 2 * .pi / Float(sides)
            return (tangent * cos(angle) + bitangent * sin(angle)) * radius
        }
        for i in 0..<sides {
            let u = ring(i), v = ring(i + 1)
            triangle(a + u, b + u, b + v); triangle(a + u, b + v, a + v)
            triangle(a, a + v, a + u); triangle(b, b + u, b + v)
        }
    }

    mutating func addProxy(_ instance: ShadowLabInstance, frame: Int) {
        let r = instance.root, h = instance.height
        switch instance.asset {
        case .tree:
            color = SIMD4(0.87, 0.98, 0.55, 0.45)
            wind = h; phase = 0.4
            beam(from: r, to: r + SIMD3(0, 0, h * 0.58), radius: 0.25)
            for (x, y, z, sx, sz) in [(-1.1, 0.0, 0.48, 1.05, 1.10), (1.1, 0.0, 0.49, 1.00, 1.14),
                                      (-0.8, 0.1, 0.69, 1.13, 1.22), (0.8, 0.1, 0.70, 1.12, 1.22),
                                      (0.0, 0.0, 0.85, 1.02, 1.13), (0.0, -0.3, 0.61, 1.23, 1.20)] as [(Float, Float, Float, Float, Float)] {
                ellipsoid(center: r + SIMD3(x, y, h * z), radii: SIMD3(sx, 0.83, sz))
            }
            wind = 0; phase = 0
        case .tower:
            color = SIMD4(1, 0.75, 0.34, 0.55)
            let angle: Float = .pi / 4
            func p(_ x: Float, _ y: Float, _ z: Float) -> SIMD3<Float> {
                r + SIMD3((x - y) * 0.7071, (x + y) * 0.7071, z)
            }
            for x: Float in [-0.66, 0.66] { for y: Float in [-0.48, 0.48] {
                beam(from: p(x, y, 0), to: p(x, y, h * 0.72), radius: 0.13)
            } }
            for z in [h * 0.32, h * 0.63] {
                box(center: r + SIMD3(0, 0, z), size: SIMD3(1.8, 1.55, 0.16), rotation: angle)
            }
            for y: Float in [-0.48, 0.48] {
                beam(from: p(-0.66, y, h * 0.05), to: p(0.66, y, h * 0.59), radius: 0.07)
                beam(from: p(0.66, y, h * 0.05), to: p(-0.66, y, h * 0.59), radius: 0.07)
            }
            let peak = r + SIMD3<Float>(0, 0, h * 0.98)
            let corners = [p(-1.0, -0.9, h * 0.78), p(1.0, -0.9, h * 0.78), p(1.0, 0.9, h * 0.78), p(-1.0, 0.9, h * 0.78)]
            for i in 0..<4 { triangle(corners[i], corners[(i + 1) % 4], peak) }
        case .hero:
            color = SIMD4(0.55, 0.85, 1, 0.65)
            // The first experiment calibrates the relatively sound left-facing artwork.
            // The contact frame is shared by the visible art and both 3D legs.
            let unit = instance.cardHeight
            let passing = frame == 2 || frame == 0
            let depth: Float = frame == 3 ? -0.12 : 0.12
            let hip = r + SIMD3<Float>(0.01, 0, unit * 0.27)
            let footA = r + SIMD3<Float>(passing ? -0.03 : -0.36, depth, 0.06)
            let footB = r + SIMD3<Float>(passing ? 0.12 : 0.27, -depth, passing ? 0.27 : 0.16)
            for (foot, side) in [(footA, depth), (footB, -depth)] {
                let knee = (hip + foot) * 0.5 + SIMD3<Float>(-0.07, side * 0.5, 0.05)
                beam(from: hip + SIMD3(0, side, 0), to: knee, radius: 0.13)
                beam(from: knee, to: foot, radius: 0.105)
                box(center: foot + SIMD3(-0.07, 0, 0), size: SIMD3(0.32, 0.23, 0.12))
            }
            ellipsoid(center: r + SIMD3(0, 0, unit * 0.40), radii: SIMD3(0.27, 0.22, unit * 0.16), segments: 8)
            ellipsoid(center: r + SIMD3(-0.01, 0, unit * 0.56), radii: SIMD3(0.31, 0.27, 0.33), segments: 8)
            beam(from: r + SIMD3(-0.10, 0, unit * 0.46), to: r + SIMD3(-0.35, 0, unit * 0.31), radius: 0.12)
        }
    }

    mutating func card(_ instance: ShadowLabInstance, rows: Int = 1, windPhase: Float = 0) {
        func vertex(_ u: Float, _ v: Float) -> ShadowLabVertex {
            let z = (1 - v - instance.anchor.y) * instance.cardHeight
            return ShadowLabVertex(position: SIMD4(instance.root + SIMD3((u - instance.anchor.x) * instance.width, 0, z), 1),
                                   uvWind: SIMD4(u, v, instance.asset == .tree ? max(0, z / instance.height) : 0, windPhase), color: SIMD4(repeating: 1))
        }
        for row in 0..<rows {
            let lo = Float(row) / Float(rows), hi = Float(row + 1) / Float(rows)
            vertices += [vertex(0, lo), vertex(0, hi), vertex(1, hi), vertex(0, lo), vertex(1, hi), vertex(1, lo)]
        }
    }
}
