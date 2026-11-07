import Foundation

/// Continuous procedural skill effects: a literal port of `scripts/battle-vfx/procfx.py` (the reference and the art spec).
/// Every effect is a closed-form function of time returning drawing primitives (soft glows, elongated glows, rings, arcs,
/// smooth tapered ribbons, flashes), so motion is continuous at any frame rate. Pure Foundation; `scripts/battle-procedural-regression.swift`
/// compares this port with golden samples exported from the Python reference.
///
/// Coordinates are stage points (y grows downward). `t` is seconds since the effect's own start.
enum MeadowSkillProcedural {
    struct RGB: Equatable { let r: Double, g: Double, b: Double; init(_ r: Double, _ g: Double, _ b: Double) { self.r = r; self.g = g; self.b = b } }
    struct Pt: Equatable { var x: Double, y: Double; init(_ x: Double, _ y: Double) { self.x = x; self.y = y } }
    struct Target: Equatable { var chest: Pt, foot: Pt }
    struct Geometry: Equatable { var caster: Pt, casterFoot: Pt, targets: [Target], ground: Double }

    enum Prim: Equatable {
        case glow(x: Double, y: Double, rx: Double, ry: Double, c: RGB, a: Double)
        case ring(x: Double, y: Double, rx: Double, ry: Double, w: Double, c: RGB, a: Double, rot: Double)
        case streak(x: Double, y: Double, rx: Double, ry: Double, ang: Double, c: RGB, a: Double)
        case arc(x: Double, y: Double, rx: Double, ry: Double, a0: Double, a1: Double, w: Double, c: RGB, a: Double)
        case ribbon(pts: [Pt], ws: [Double], c: RGB, a: Double, add: Bool, soft: Double)
        case flash(c: RGB, a: Double)
    }

    // MARK: skill table

    struct Info { let duration: Double, release: Double, dim: Double, dimTint: RGB, support: Bool }
    static let skillIDs = ["starlightPulse", "dragonSoulWard", "dragonScaleWard", "runeSlash", "runeWard", "battleRune", "dragonFlame", "dragonOrder",
                           "healMicro", "healStandard", "healStrong"]
    static let info: [String: Info] = [
        "starlightPulse": Info(duration: 1.6, release: 0.75, dim: 0.34, dimTint: RGB(0.80, 0.76, 1.0), support: false),
        "dragonSoulWard": Info(duration: 2.0, release: 0.38, dim: 0.32, dimTint: RGB(0.74, 0.88, 1.0), support: true),
        "dragonScaleWard": Info(duration: 2.2, release: 0.56, dim: 0.28, dimTint: RGB(1.0, 0.88, 0.7), support: true),
        "runeSlash": Info(duration: 2.4, release: 1.048, dim: 0.30, dimTint: RGB(0.8, 0.92, 1.0), support: false),
        "runeWard": Info(duration: 2.4, release: 0.72, dim: 0.28, dimTint: RGB(0.8, 0.92, 1.0), support: true),
        "battleRune": Info(duration: 2.1, release: 0.56, dim: 0.28, dimTint: RGB(1.0, 0.88, 0.72), support: true),
        "dragonFlame": Info(duration: 2.2, release: 0.46, dim: 0.34, dimTint: RGB(1.0, 0.78, 0.62), support: false),
        "dragonOrder": Info(duration: 2.1, release: 0.56, dim: 0.32, dimTint: RGB(1.0, 0.78, 0.72), support: true),
        "healMicro": Info(duration: 1.35, release: 0.1, dim: 0.26, dimTint: RGB(0.82, 0.96, 0.86), support: true),
        "healStandard": Info(duration: 1.8, release: 0.1, dim: 0.28, dimTint: RGB(0.8, 0.96, 0.85), support: true),
        "healStrong": Info(duration: 2.3, release: 0.1, dim: 0.32, dimTint: RGB(0.78, 0.95, 0.84), support: true)
    ]
    /// Dominant colour of each skill (for the ambient light, floor pool and motes).
    static func tone(_ id: String) -> RGB {
        switch id {
        case "starlightPulse": return RGB(160, 136, 255)
        case "dragonSoulWard": return RGB(56, 140, 255)
        case "dragonScaleWard": return Pal.scale.mid
        case "runeSlash", "runeWard": return Pal.rune.mid
        case "battleRune": return Pal.battle.mid
        case "dragonFlame": return Pal.flame.mid
        case "dragonOrder": return Pal.order.mid
        default: return Pal.heal.mid
        }
    }

    // MARK: maths

    static func clamp01(_ x: Double) -> Double { min(1.0, max(0.0, x)) }
    static func smooth(_ x: Double) -> Double { let t = clamp01(x); return t * t * (3 - 2 * t) }
    static func easeOut(_ x: Double) -> Double { let t = clamp01(x); return 1 - pow(1 - t, 3) }
    static func easeIn(_ x: Double) -> Double { let t = clamp01(x); return t * t }
    static func lerp(_ a: Double, _ b: Double, _ t: Double) -> Double { a + (b - a) * t }
    static func frac(_ i: Int, _ salt: Int) -> Double { Double((i * 73 + salt * 37 + (i * i) * 11) % 101) / 100.0 }
    /// Python-style modulo for floats (the result has the sign of the divisor).
    static func pm(_ a: Double, _ b: Double) -> Double { a - (a / b).rounded(.down) * b }
    static func b2d(_ v: Bool) -> Double { v ? 1.0 : 0.0 }
    static func pw(_ x: Double, _ y: Double) -> Double { pow(max(0, x), y) }

    // MARK: palettes

    struct Pal { let deep: RGB, body: RGB, mid: RGB, light: RGB, a1: RGB, a2: RGB
        static let rune = Pal(deep: RGB(14, 40, 92), body: RGB(40, 150, 235), mid: RGB(90, 215, 255), light: RGB(205, 248, 255), a1: RGB(255, 214, 120), a2: RGB(150, 110, 255))
        static let battle = Pal(deep: RGB(110, 40, 10), body: RGB(230, 120, 30), mid: RGB(255, 180, 60), light: RGB(255, 236, 170), a1: RGB(255, 90, 60), a2: RGB(255, 230, 160))
        static let flame = Pal(deep: RGB(120, 20, 8), body: RGB(235, 70, 20), mid: RGB(255, 150, 40), light: RGB(255, 225, 140), a1: RGB(255, 250, 220), a2: RGB(255, 90, 40))
        static let scale = Pal(deep: RGB(96, 44, 10), body: RGB(214, 120, 28), mid: RGB(255, 180, 70), light: RGB(255, 230, 160), a1: RGB(255, 120, 60), a2: RGB(255, 214, 120))
        static let order = Pal(deep: RGB(90, 10, 30), body: RGB(200, 40, 50), mid: RGB(255, 110, 70), light: RGB(255, 210, 150), a1: RGB(255, 220, 120), a2: RGB(255, 150, 90))
        static let heal = Pal(deep: RGB(8, 66, 40), body: RGB(40, 190, 100), mid: RGB(110, 235, 150), light: RGB(215, 255, 228), a1: RGB(255, 232, 150), a2: RGB(120, 240, 222))
    }
    static let magenta = RGB(255, 128, 226), cyan = RGB(130, 224, 255), gold = RGB(255, 232, 160), white = RGB(255, 255, 255)
    static let starlightTone = [RGB(255, 255, 255), RGB(222, 212, 255), RGB(160, 136, 255), RGB(96, 70, 235), RGB(44, 26, 150)]
    static let soulTone = [RGB(235, 250, 255), RGB(130, 210, 255), RGB(56, 140, 255), RGB(24, 70, 190)]

    // MARK: output builder

    struct Out {
        var prims: [Prim] = []
        mutating func g(_ x: Double, _ y: Double, _ rx: Double, _ ry: Double, _ c: RGB, _ a: Double) { prims.append(.glow(x: x, y: y, rx: rx, ry: ry, c: c, a: a)) }
        mutating func r(_ x: Double, _ y: Double, _ rx: Double, _ ry: Double, _ w: Double, _ c: RGB, _ a: Double, _ rot: Double = 0) { prims.append(.ring(x: x, y: y, rx: rx, ry: ry, w: w, c: c, a: a, rot: rot)) }
        mutating func e(_ x: Double, _ y: Double, _ rx: Double, _ ry: Double, _ ang: Double, _ c: RGB, _ a: Double) { prims.append(.streak(x: x, y: y, rx: rx, ry: ry, ang: ang, c: c, a: a)) }
        mutating func arc(_ x: Double, _ y: Double, _ rx: Double, _ ry: Double, _ a0: Double, _ a1: Double, _ w: Double, _ c: RGB, _ a: Double) { prims.append(.arc(x: x, y: y, rx: rx, ry: ry, a0: a0, a1: a1, w: w, c: c, a: a)) }
        mutating func k(_ pts: [Pt], _ ws: [Double], _ c: RGB, _ a: Double, add: Bool, soft: Double) { prims.append(.ribbon(pts: pts, ws: ws, c: c, a: a, add: add, soft: soft)) }
        mutating func f(_ c: RGB, _ a: Double) { prims.append(.flash(c: c, a: a)) }
        /// Gradient ribbon: several passes, each (width scale, colour, additive, alpha), outer to inner.
        mutating func stack(_ pts: [Pt], _ ws: [Double], _ layers: [(Double, RGB, Bool, Double)], _ alpha: Double = 1.0) {
            for (sc, col, add, a) in layers { k(pts, ws.map { $0 * sc }, col, a * alpha, add: add, soft: max(1.2, 2.4 * sc)) }
        }
        mutating func thinRing(_ x: Double, _ y: Double, _ rx: Double, _ ry: Double, _ w: Double, _ c: RGB, _ a: Double) { r(x, y, rx, ry, w, c, a) }
    }

    static func ell(_ cx: Double, _ cy: Double, _ rx: Double, _ ry: Double, _ a: Double) -> Pt { Pt(cx + cos(a) * rx, cy + sin(a) * ry) }

    /// Floor seal made only of rings, arcs and petals (no straight lines).
    static func sigil2(_ o: inout Out, _ cx: Double, _ cy: Double, _ R: Double, _ ratio: Double, _ t: Double, _ env: Double, _ cols: (RGB, RGB, RGB), _ petals: Int = 8, _ spin: Double = 1.0) {
        if env <= 0.01 { return }
        let (c1, c2, c3) = cols
        o.g(cx, cy, R * 1.18, R * 1.18 * ratio, c2, 0.30 * env); o.g(cx, cy, R * 0.6, R * 0.6 * ratio, c1, 0.22 * env)
        o.r(cx, cy, R, R * ratio, 2.6, c1, 0.85 * env); o.r(cx, cy, R * 0.93, R * 0.93 * ratio, 1.1, c3, 0.6 * env)
        o.r(cx, cy, R * 0.62, R * 0.62 * ratio, 1.6, c1, 0.7 * env); o.r(cx, cy, R * 0.3, R * 0.3 * ratio, 1.2, c3, 0.6 * env)
        for k in 0..<6 {
            let a0 = spin * t * 0.7 + Double(k) * Double.pi / 3
            o.arc(cx, cy, R * 0.8, R * 0.8 * ratio, a0, a0 + 0.72, 3.0, c1, 0.85 * env)
        }
        for k in 0..<4 {
            let a0 = -spin * t * 1.1 + Double(k) * Double.pi / 2
            o.arc(cx, cy, R * 0.46, R * 0.46 * ratio, a0, a0 + 0.9, 2.2, c3, 0.8 * env)
        }
        for k in 0..<petals {
            let a = Double(k) * 2 * Double.pi / Double(petals) - spin * t * 0.4, d = R * 0.5
            let px = cx + cos(a) * d, py = cy + sin(a) * d * ratio
            o.r(px, py, R * 0.3, R * 0.11 * (1 + 1.2 * (1 - ratio)), 1.2, c2, 0.5 * env, a)
            o.e(px, py, R * 0.26, R * 0.08, a, c1, 0.16 * env)
        }
        for k in 0..<16 {
            let a = Double(k) * Double.pi / 8 + spin * t * 0.5
            o.g(cx + cos(a) * R * 0.72, cy + sin(a) * R * 0.72 * ratio, 5, 5, c3, 0.85 * env * (0.55 + 0.45 * sin(t * 5 + Double(k))))
        }
    }

    static func aurora(_ o: inout Out, _ cx: Double, _ cy: Double, _ t: Double, _ env: Double, _ cols: [RGB], _ spread: Double = 150, _ h: Double = 120) {
        if env <= 0.01 { return }
        for k in 0..<3 {
            var pts: [Pt] = [], ws: [Double] = []
            for j in 0..<48 {
                let u = Double(j) / 47, x = cx + (u - 0.5) * spread * 2
                let y = cy - h - 26 * Double(k) + 22 * sin(u * 5 + t * 1.3 + Double(k) * 2) + 9 * sin(u * 11 - t * 2 + Double(k))
                pts.append(Pt(x, y)); ws.append(30 * pw(sin(Double.pi * u), 0.8) * (1 - 0.18 * Double(k)) + 2)
            }
            o.k(pts, ws, cols[k % cols.count], 0.16 * env, add: true, soft: 9)
            o.k(pts, ws.map { $0 * 0.4 }, cols[(k + 1) % cols.count], 0.12 * env, add: true, soft: 6)
        }
    }

    static func arcPts(_ cx: Double, _ cy: Double, _ rx: Double, _ ry: Double, _ a0: Double, _ a1: Double, _ n: Int = 40, _ roll: Double = 0) -> [Pt] {
        (0..<n).map { j in
            let a = lerp(a0, a1, Double(j) / Double(n - 1)), x = cos(a) * rx, y = sin(a) * ry
            return Pt(cx + x * cos(roll) - y * sin(roll), cy + x * sin(roll) + y * cos(roll))
        }
    }

    /// A crackling arc between two points: a jittering smooth ribbon, a bright thin core and a soft halo.
    static func bolt(_ o: inout Out, _ A: Pt, _ B: Pt, _ t: Double, _ seed: Double, _ P: Pal, _ amp: Double = 14, _ n: Int = 16, _ w: Double = 3.2, _ alpha: Double = 1.0, _ rate: Double = 30) {
        var pts: [Pt] = [], ws: [Double] = []
        let dx = B.x - A.x, dy = B.y - A.y, L0 = hypot(dx, dy), L = L0 == 0 ? 1.0 : L0, nx = -dy / L, ny = dx / L
        for j in 0..<n {
            let u = Double(j) / Double(n - 1), env = pw(sin(Double.pi * u), 0.8)
            let jj = Double(j)
            let d = amp * env * (sin(jj * 1.9 + t * rate + seed * 7.1) * 0.6 + sin(jj * 3.3 - t * rate * 1.3 + seed * 3.7) * 0.4)
            pts.append(Pt(A.x + dx * u + nx * d, A.y + dy * u + ny * d)); ws.append(w * (0.55 + 0.45 * env))
        }
        o.stack(pts, ws, [(2.6, P.body, true, 0.22), (1.0, P.mid, true, 0.55), (0.4, P.light, true, 0.95)], alpha)
    }

    static func flame(_ o: inout Out, _ bx: Double, _ by: Double, _ h: Double, _ w: Double, _ t: Double, _ seed: Double, _ P: Pal, _ alpha: Double = 1.0, _ n: Int = 26) {
        var pts: [Pt] = [], ws: [Double] = []
        for j in 0..<n {
            let u = Double(j) / Double(n - 1)
            pts.append(Pt(bx + sin(u * 6 + t * 9 + seed * 3.3) * w * 0.5 * u + sin(u * 13 - t * 14 + seed) * w * 0.15 * u, by - u * h)); ws.append(w * pw(1 - u, 0.85) + 0.8)
        }
        o.stack(pts, ws, [(1.5, P.deep, true, 0.22), (1.0, P.body, true, 0.55), (0.5, P.mid, true, 0.8), (0.18, P.a1, true, 0.95)], alpha)
    }

    // MARK: entry point

    /// Every target gets the effect; caster-side parts (charge-up, seal under the caster, stage flash) are drawn once, for the first target.
    static func primitives(skill id: String, t: Double, geo: Geometry) -> [Prim] {
        guard !geo.targets.isEmpty else { return [] }
        var all: [Prim] = []
        for ti in geo.targets.indices {
            switch id {
            case "starlightPulse": all += starlight(t, geo, ti)
            case "dragonSoulWard": all += soul(t, geo, ti)
            case "dragonScaleWard": all += scaleWard(t, geo, ti)
            case "runeSlash": all += runeSlash(t, geo, ti)
            case "runeWard": all += runeWard(t, geo, ti)
            case "battleRune": all += battleRune(t, geo, ti)
            case "dragonFlame": all += dragonFlame(t, geo, ti)
            case "dragonOrder": all += dragonOrder(t, geo, ti)
            case "healMicro": all += healMicro(t, geo, ti)
            case "healStandard": all += healStandard(t, geo, ti)
            case "healStrong": all += healStrong(t, geo, ti)
            default: return []
            }
        }
        return all
    }

    // MARK: starlight pulse

    static func starlight(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let C = geo.caster, CF = geo.casterFoot, T = geo.targets[ti].chest, TF = geo.targets[ti].foot, imp = 0.75
        let V = starlightTone, DEEP = RGB(40, 24, 140)
        let sig = smooth(t / 0.2) * (1 - smooth((t - 0.42) / 0.25)) * (ti == 0 ? 1.0 : 0.0)
        sigil2(&o, CF.x, CF.y - 2, 66, 0.3, t, sig, (V[2], V[3], V[1]), 8, 1.2)
        if t < 0.55 && ti == 0 {
            for i in 0..<22 {
                let ph = frac(i, 1), u = pm(t * 0.9 + ph, 1.0), di = Double(i)
                let x = CF.x + sin(u * 6 + di) * (24 + 30 * frac(i, 2)), y = CF.y - 6 - u * 130
                let al = sig * pw(sin(Double.pi * u), 0.7)
                o.g(x, y, 8, 8, [V[2], magenta, cyan][i % 3], 0.55 * al); o.g(x, y, 3, 3, V[0], 0.9 * al)
            }
        }
        func path(_ tt: Double) -> (Double, Double, Double) {
            let s = pw(easeIn(clamp01(tt / imp)), 0.8)
            let x = lerp(C.x, T.x, s), y = lerp(C.y, T.y, s)
            return (x, y - 70 * sin(Double.pi * s) * (1 - 0.3 * s), s)
        }
        if t < imp + 0.02 {
            let (hx, hy, _) = path(t)
            let N = 60
            var pts: [Pt] = [], ws: [Double] = [], nrm: [(Double, Double, Double, Int)] = []
            for i in stride(from: N - 1, through: 0, by: -1) {
                let tt = t - Double(i) * 0.0105
                if tt < 0 { continue }
                let (x, y, _) = path(tt), (x2, y2, _) = path(tt + 0.006)
                let dx = x2 - x, dy = y2 - y, L0 = hypot(dx, dy), L = L0 == 0 ? 1.0 : L0, nx = -dy / L, ny = dx / L
                let u = Double(i) / Double(N), lat = 5 * u * sin(tt * 22 + Double(i) * 0.45)
                pts.append(Pt(x + nx * lat, y + ny * lat)); nrm.append((nx, ny, tt, i))
                ws.append(((17 * pw(1 - u, 0.85) + 1.2) * (0.45 + 0.55 * clamp01(tt * 7))) * 2)
            }
            if pts.count > 3 {
                for k in stride(from: 0, to: pts.count, by: 5) { o.g(pts[k].x, pts[k].y, ws[k] * 1.9, ws[k] * 1.9, [V[3], magenta, cyan][(k / 5) % 3], 0.1) }
                o.stack(pts, ws, [(1.25, DEEP, false, 0.5), (1.0, V[4], false, 0.7), (0.72, V[3], false, 0.85), (0.5, V[2], true, 0.55), (0.22, V[1], true, 0.85)])
                for (k, col) in [magenta, cyan, V[1]].enumerated() {
                    var sp: [Pt] = [], sw: [Double] = []
                    for idx in 0..<pts.count {
                        let (nx, ny, tt, i) = nrm[idx], w = ws[idx], px = pts[idx].x, py = pts[idx].y
                        let ang = tt * 18 + Double(i) * 0.3 + Double(k) * 2.094, off = w * 0.62 + 2
                        sp.append(Pt(px + nx * cos(ang) * off, py + ny * cos(ang) * off + sin(ang) * off * 0.3)); sw.append(max(0.8, w * 0.12))
                    }
                    o.k(sp, sw, col, 0.8, add: true, soft: 2.0)
                }
            }
            for i in 0..<34 {
                let tb = frac(i, 1) * imp * 0.95
                if !(0 <= t - tb && t - tb < 0.6) { continue }
                let tt = t - tb, (px, py, _) = path(tb), r = tt / 0.6
                let x = px + (frac(i, 2) - 0.5) * 44 * r, y = py + (frac(i, 3) - 0.3) * 44 * r + 34 * r * r
                let col = [V[0], gold, magenta, cyan][i % 4], k = (1 - r) * (0.6 + 0.4 * sin(tt * 30 + Double(i)))
                o.g(x, y, 8, 8, col, 0.7 * k); o.e(x, y, 8 + 4 * frac(i, 4), 1.1, tt * 3 + Double(i), V[0], 0.8 * k); o.e(x, y, 8 + 4 * frac(i, 4), 1.1, tt * 3 + Double(i) + 1.571, V[0], 0.8 * k)
            }
            let fade = clamp01((imp - t) / 0.05), pulse = 1 + 0.08 * sin(t * 25)
            o.g(hx, hy, 74, 74, V[3], 0.3 * fade); o.g(hx, hy, 40, 40, V[2], 0.42 * fade)
            o.r(hx, hy, 26 * pulse, 26 * pulse, 1.5, V[2], 0.5 * fade); o.r(hx, hy, 34, 34, 1.0, magenta, 0.35 * fade)
            o.g(hx, hy, 24, 24, V[1], 0.75 * fade); o.g(hx, hy, 12, 12, V[0], 1.0 * fade)
            o.e(hx, hy, 110, 3.2, 0, V[1], 0.45 * fade); o.e(hx, hy, 70, 2.4, 0, V[0], 0.5 * fade)
            for k in 0..<4 { o.e(hx, hy, 42 - 10 * Double(k % 2), 2.4, t * 3 + Double(k) * 0.785, V[0], 0.6 * fade) }
            for k in 0..<7 {
                let a = t * 9 + Double(k) * 2 * Double.pi / 7, rr = 24 + 5 * sin(t * 6 + Double(k))
                o.g(hx + cos(a) * rr, hy + sin(a) * rr * 0.6, 6, 6, [V[0], magenta, cyan][k % 3], 0.8 * fade)
            }
        }
        let a = t - imp
        if a >= 0 {
            let cx = T.x, cy = T.y
            if a < 0.2 && ti == 0 { o.f(V[2], 0.12 * exp(-a * 18)) }
            o.g(cx, cy, 170 * (0.5 + easeOut(a / 0.35)), 170 * (0.5 + easeOut(a / 0.35)), V[3], 0.4 * (1 - easeIn(a / 0.8)))
            o.g(cx, cy, 60, 60, V[2], 0.5 * (1 - easeIn(a / 0.35)))
            o.g(cx, cy, 22, 22, V[1], 0.6 * (1 - easeIn(a / 0.22))); o.g(cx, cy, 10, 10, V[0], 0.9 * (1 - easeIn(a / 0.16)))
            o.e(cx, cy, 230 * easeOut(a / 0.2), 4.5, 0, V[1], 0.55 * (1 - easeIn(a / 0.45)))
            o.e(cx, cy, 110 * easeOut(a / 0.2), 3.2, 0, V[0], 0.55 * (1 - easeIn(a / 0.35)))
            o.e(cx, cy, 90 * easeOut(a / 0.2), 3.0, 1.571, V[1], 0.4 * (1 - easeIn(a / 0.35)))
            for k in 0..<40 {
                let ang = Double(k) * 2 * Double.pi / 40 + a * 0.4
                let L = (60 + 100 * frac(k, 2)) * easeOut(a / 0.16) * (1 - easeIn((a - 0.1) / 0.6))
                if L > 3 { o.e(cx + cos(ang) * L / 2, cy + sin(ang) * L / 2, L / 2, 1.8, ang, [V[2], magenta, cyan, V[1]][k % 4], 0.55 * (1 - a / 0.7)) }
            }
            for (d, col) in [(0.0, V[2]), (0.07, magenta), (0.14, cyan), (0.22, V[1])] where a - d >= 0 {
                let r = 12 + 150 * easeOut((a - d) / 0.6)
                o.r(cx, cy, r, r * 0.8, 3.0 * (1 - (a - d) / 0.65) + 0.6, col, 0.85 * (1 - easeIn((a - d) / 0.65)))
            }
            let lotus: [(Int, RGB, Double, Double)] = [(12, V[2], 0.0, 120), (8, magenta, 0.39, 82), (12, cyan, 0.13, 150)]
            for (layer, (nP, col, rot0, size)) in lotus.enumerated() {
                let k = easeOut((a - Double(layer) * 0.05) / 0.3) * (1 - easeIn((a - 0.22 - Double(layer) * 0.05) / 0.5))
                if k > 0.02 {
                    for q in 0..<nP {
                        let ang = Double(q) * 2 * Double.pi / Double(nP) + rot0 + a * (0.9 - 0.3 * Double(layer)), L = size * k
                        let px = cx + cos(ang) * L * 0.5, py = cy + sin(ang) * L * 0.5 * 0.82
                        o.r(px, py, L * 0.5, L * 0.13, 1.4, col, 0.6 * k, ang); o.e(px, py, L * 0.42, L * 0.1, ang, col, 0.2 * k)
                    }
                }
            }
            let sg2 = smooth(a / 0.08) * (1 - easeIn((a - 0.22) / 0.6))
            sigil2(&o, TF.x, TF.y - 2, 46 + 62 * easeOut(a / 0.3), 0.3, a + imp, sg2, (V[2], V[3], V[1]), 8, 1.6)
            for q in 0..<3 {
                var pts: [Pt] = [], ws: [Double] = []
                for j in 0..<40 {
                    let u = Double(j) / 39, ang = Double(q) * 2.094 + u * 7 + a * 5, rr = 36 + 40 * u
                    pts.append(Pt(TF.x + cos(ang) * rr, TF.y - 8 - u * 150 * easeOut(a / 0.5) + sin(ang) * rr * 0.3)); ws.append(5 * pw(sin(Double.pi * u), 0.8) + 0.6)
                }
                o.k(pts, ws, [V[2], magenta, cyan][q], 0.55 * (1 - easeIn((a - 0.15) / 0.6)), add: true, soft: 3.0)
            }
            for i in 0..<90 {
                let life = 0.55 + 0.6 * frac(i, 2), tt = a - 0.02 * frac(i, 5)
                if !(0 <= tt && tt < life) { continue }
                let ang = frac(i, 3) * 6.283, spd = 160 + 300 * frac(i, 4), tr = tt / life
                let d = spd * (1 - exp(-tt * 5)) / 5, v = spd * exp(-tt * 5)
                let x = cx + cos(ang) * d, y = cy + sin(ang) * d * 0.8 + 140 * tt * tt * b2d(frac(i, 6) > 0.5)
                let tw = 0.6 + 0.4 * sin(tt * 40 + Double(i)), col = [V[0], gold, magenta, cyan, V[1]][i % 5]
                o.e(x - cos(ang) * v * 0.014, y - sin(ang) * v * 0.014 * 0.8, max(3.0, v * 0.03), 1.9 * (1 - 0.5 * tr), ang, col, 0.9 * (1 - tr) * tw)
                o.g(x, y, 7, 7, col, 0.5 * (1 - tr) * tw)
            }
            for i in 0..<34 {
                let tb = 0.06 + 0.55 * frac(i, 1), tt = a - tb
                if !(0 <= tt && tt < 0.9) { continue }
                let x = cx + (frac(i, 2) - 0.5) * 210, y = cy - 130 + tt * (70 + 40 * frac(i, 3)), r = tt / 0.9
                let col = [V[0], gold, V[1], cyan][i % 4], k = sin(Double.pi * r) * (0.6 + 0.4 * sin(tt * 30 + Double(i)))
                let sz = 5 + 6 * frac(i, 4)
                o.g(x, y, sz, sz, col, 0.7 * k); o.e(x, y, sz * 1.7, 1.1, tt * 2 + Double(i), V[0], 0.8 * k); o.e(x, y, sz * 1.7, 1.1, tt * 2 + Double(i) + 1.571, V[0], 0.8 * k)
            }
            aurora(&o, cx, cy - 20, a * 1.4, smooth(a / 0.25) * (1 - smooth((a - 0.4) / 0.5)), [V[3], magenta, cyan], 140, 100)
        }
        return o.prims
    }

    // MARK: dragon soul ward (power and presence, nothing literal)

    static func soul(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let D = soulTone, chest = geo.targets[ti].chest, foot = geo.targets[ti].foot, fx = foot.x, fy = foot.y, gy = foot.y
        let cx = chest.x, cy = chest.y
        let BODY = RGB(34, 98, 220), MID = RGB(70, 150, 255), LIGHT = RGB(170, 225, 255)
        let REL = 0.38
        let pre = clamp01(t / REL), post = t - REL
        let sg = smooth(t / 0.22) * (1 - smooth((t - 1.55) / 0.4))
        sigil2(&o, fx, gy - 2, 74 - 14 * easeIn(pre) * b2d(post < 0) + 8 * easeOut(post / 0.3), 0.28, t, sg, (D[2], RGB(36, 90, 220), D[1]), 10, 1.0 + 3 * easeIn(pre) * b2d(post < 0))
        if t < REL + 0.05 {
            for i in 0..<34 {
                let ph = frac(i, 1), tt = clamp01((t - ph * 0.12) / (REL - ph * 0.12))
                let a = frac(i, 2) * 6.283 + tt * 4.5, r = (120 + 80 * frac(i, 3)) * pw(1 - easeIn(tt), 1.4)
                let x = cx + cos(a) * r, y = cy + 20 + sin(a) * r * 0.55 - 20 * easeIn(tt)
                let k = pw(sin(Double.pi * min(1, tt * 1.05)), 0.6)
                o.e(x, y, 9 + 18 * (1 - tt), 1.8, a + 1.571 + tt * 4.5, [D[0], D[1], gold][i % 3], 0.8 * k)
                o.g(x, y, 6, 6, D[0], 0.8 * k)
            }
            let k = easeIn(pre) * b2d(post < 0)
            o.g(cx, cy, 70 - 40 * k + 20, 90 - 50 * k + 20, D[3], 0.22 + 0.22 * k); o.g(cx, cy, 20, 26, D[1], 0.5 * k)
        }
        if post >= 0 {
            if post < 0.22 && ti == 0 { o.f(D[2], 0.12 * exp(-post * 14)) }
            let waves: [(Double, Double)] = [(0, 7.0), (0.08, 5.0), (0.17, 3.4), (0.28, 2.2)]
            for (j, (d, wd)) in waves.enumerated() where post - d >= 0 {
                let r = 14 + 190 * easeOut((post - d) / 0.7)
                o.r(fx, gy - 2, r, r * 0.27, wd * (1 - (post - d) / 0.75) + 0.5, [D[1], D[2], D[2], D[1]][j], 0.8 * (1 - easeIn((post - d) / 0.75)))
            }
            for j in 0..<2 where post - Double(j) * 0.1 >= 0 {
                let pj = post - Double(j) * 0.1, r = 26 + 120 * easeOut(pj / 0.5)
                o.r(cx, cy, r, r * 1.25, 2.4 * (1 - pj / 0.55) + 0.5, D[1], 0.6 * (1 - easeIn(pj / 0.55)))
            }
            let colEnv = smooth(post / 0.12) * (1 - smooth((post - 0.95) / 0.55))
            let layers: [(Double, RGB, Double)] = [(84, D[3], 0.12), (52, BODY, 0.12), (26, D[2], 0.12), (9, MID, 0.3)]
            let us = (0..<41).map { Double($0) / 40 }
            for (lyr, (w, c_, a)) in layers.enumerated() {
                let top = fy - 250 * easeOut(post / 0.2), dl = Double(lyr)
                let pts = us.map { u in Pt(fx + sin(u * 7 + t * 4 + dl) * 3 * (1 - u), fy - u * (fy - top)) }
                let ws = us.map { u in w * (0.5 + 0.5 * pw(sin(Double.pi * (u * 0.9 + 0.1)), 0.5)) * (1 + 0.06 * sin(t * 20 + dl)) }
                o.k(pts, ws, c_, a * colEnv, add: true, soft: lyr < 2 ? 14 : 6)
            }
            for q in 0..<6 {
                let sgn: Double = q % 2 == 0 ? 1 : -1, dq = Double(q)
                var pts: [Pt] = [], ws: [Double] = []
                let head = easeOut(clamp01(post / 0.5)), tail = easeIn(clamp01((post - 0.9) / 0.6))
                for j in 0..<72 {
                    let u = Double(j) / 71
                    if u > head || u < tail * 0.9 { continue }
                    let ang = dq * 1.047 + sgn * (u * (7 + 0.7 * dq) - post * (4.5 + 0.4 * dq)), rr = 40 + 30 * sin(u * 3 + dq) + 34 * u * (1 + 0.15 * dq)
                    pts.append(Pt(fx + cos(ang) * rr, fy - 8 - u * 215 + sin(ang) * rr * 0.3)); ws.append((11 * pw(1 - u, 0.9) + 1.4) * (1 - tail) * (0.75 + 0.25 * sin(u * 9 + dq)))
                }
                if pts.count > 3 {
                    o.stack(pts, ws, [(1.7, D[3], true, 0.30), (1.0, BODY, true, 0.5), (0.5, MID, true, 0.7), (0.16, LIGHT, true, 0.8)], colEnv)
                    o.k(pts, ws.map { $0 * 3.0 }, D[3], 0.1 * colEnv, add: true, soft: 12)
                }
            }
            for i in 0..<44 {
                let tb = 0.02 + 0.5 * frac(i, 1), tt = post - tb
                if !(0 <= tt && tt < 0.9) { continue }
                let a = frac(i, 3) * 6.283, r = (60 + 160 * frac(i, 4)) * easeOut(tt / 0.6)
                let x = cx + cos(a) * r, y = cy + 40 + sin(a) * r * 0.3 - 70 * tt * (0.5 + frac(i, 5)), k = (1 - tt / 0.9) * (0.6 + 0.4 * sin(tt * 30 + Double(i)))
                o.e(x, y, 10, 1.7, a, [D[0], gold, D[1]][i % 3], 0.8 * k); o.g(x, y, 6, 6, D[0], 0.7 * k)
            }
            for k in 0..<26 {
                let a = Double(k) * 2 * Double.pi / 26 + 0.3 * frac(k, 2), L = 40 + 60 * frac(k, 3), r = (30 + 160 * easeOut(post / 0.6)) * (0.7 + 0.5 * frac(k, 4))
                o.e(fx + cos(a) * r, gy - 4 + sin(a) * r * 0.27, L, 1.8, a, D[2], 0.5 * (1 - easeIn(post / 0.8)))
            }
        }
        let aura = post > 0 ? smooth((post - 0.1) / 0.4) * (1 - smooth((t - 1.6) / 0.4)) : 0.0
        if aura > 0.01 {
            let pulse = 1 + 0.05 * sin(t * 6), RX = 56 * pulse, RY = 86 * pulse
            o.g(cx, cy, RX * 1.6, RY * 1.3, D[3], 0.22 * aura); o.g(cx, cy, RX * 1.05, RY * 1.0, D[2], 0.08 * aura)
            for (sc, w, c_, al) in [(1.0, 3.0, D[1], 0.55), (0.94, 1.6, D[2], 0.5), (1.1, 1.4, D[2], 0.35)] { o.r(cx, cy, RX * sc, RY * sc, w, c_, al * aura) }
            for k in 0..<5 {
                let dk = Double(k), a0 = t * (1.3 + 0.35 * dk) + dk * 1.3
                o.arc(cx, cy, RX * (1 + 0.03 * dk), RY * (1 + 0.03 * dk), a0, a0 + 1.0, 2.8, D[1], 0.6 * aura)
            }
            for i in 0..<16 {
                let di = Double(i), ph = frac(i, 1), u0 = pm(t * 0.55 + ph, 1.0), a = frac(i, 2) * 6.283
                let bx = cx + cos(a) * RX * 0.7, by = cy + RY * 0.75
                var pts: [Pt] = [], ws: [Double] = []
                for j in 0..<22 {
                    let u = Double(j) / 21, y = by - u * (90 + 70 * frac(i, 3)) * (0.35 + 0.65 * u0)
                    pts.append(Pt(bx + sin(u * 5 + t * 3 + di) * 9 * u + (frac(i, 4) - 0.5) * 20 * u, y)); ws.append(8 * pw(1 - u, 1.1) + 0.4)
                }
                let fade = pw(sin(Double.pi * u0), 0.8)
                o.k(pts, ws, [D[2], D[1], D[2]][i % 3], 0.4 * aura * fade, add: true, soft: 3.0)
            }
            for i in 0..<30 {
                let u = pm(t * 0.4 + frac(i, 1), 1.0), a = frac(i, 2) * 6.283 + t * 0.8
                let x = cx + cos(a) * RX * 0.95 * frac(i, 3), y = cy + RY * (1 - 2 * u), k = aura * sin(Double.pi * u)
                o.g(x, y, 8, 8, [D[0], D[1], gold][i % 3], 0.65 * k); o.g(x, y, 3, 3, white, 0.9 * k)
            }
            let halo = aura * (0.7 + 0.3 * sin(t * 5))
            o.r(cx, cy - RY - 14, 34, 9, 2.2, gold, 0.75 * halo); o.g(cx, cy - RY - 14, 50, 16, gold, 0.28 * halo)
        }
        return o.prims
    }

    // MARK: spellblade: rune slash

    static func runeSlash(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.rune, C = geo.caster, T = geo.targets[ti].chest, imp = 1.048
        let pre = clamp01((t - 0.25) / (imp - 0.25)), cx = T.x, cy = T.y
        let ANG: [Double] = [-0.95, 0.35, 1.25, -0.2, -1.75]
        for k in 0..<(ti == 0 ? 5 : 0) {
            let dk = Double(k), e = smooth((t - 0.2 - dk * 0.09) / 0.35)
            if e <= 0.01 || t >= imp + 0.05 * dk { continue }
            let sp = 3 + 14 * pre * pre, a = t * sp + dk * 1.2566, R = 52 + 10 * sin(t * 5 + dk)
            let px = C.x + 24 + cos(a) * R, py = C.y + sin(a) * R * 0.55, ang = a + 1.571
            let pts = (0..<12).map { i -> Pt in let s_ = Double(i) / 11 - 0.5; return Pt(px + cos(ang) * s_ * 24, py + sin(ang) * s_ * 24 * 0.55) }
            let ws = (0..<12).map { i in 9 * pw(sin(Double.pi * (Double(i) / 11)), 0.8) + 0.6 }
            o.stack(pts, ws, [(2.2, P.body, true, 0.25), (1.0, P.mid, true, 0.6), (0.4, P.light, true, 0.95)], e)
        }
        if t < imp && ti == 0 {
            o.g(C.x + 24, C.y, 40 + 30 * pre, 50 + 30 * pre, P.body, 0.22 + 0.25 * pre); o.g(C.x + 24, C.y, 14, 18, P.light, 0.8 * pre)
        }
        let last = imp + 0.06 * 4
        for k in 0..<5 {
            let dk = Double(k), a = t - imp - 0.06 * dk
            if a < 0 { continue }
            let th = ANG[k], L = 150 + 30 * Double(k % 2)
            let reveal = easeOut(clamp01(a / 0.07))
            let env = 1 - easeIn((a - 0.06) / 0.55)
            let ux = cos(th), uy = sin(th) * 0.8, nx = -uy, ny = ux
            var pts: [Pt] = [], ws: [Double] = []
            for j in 0..<30 {
                let u = Double(j) / 29, s_ = (u - 0.5) * 2, bow = (1 - s_ * s_) * 16
                pts.append(Pt(cx + ux * s_ * L * reveal + nx * bow, cy + uy * s_ * L * reveal + ny * bow)); ws.append(10 * pw(sin(Double.pi * u), 0.75) + 0.5)
            }
            if env > 0.01 {
                o.stack(pts, ws, [(2.4, P.deep, true, 0.3), (1.2, P.body, true, 0.5), (0.6, P.mid, true, 0.7), (0.22, P.light, true, 0.95)], env)
                let col = k % 2 == 0 ? P.a1 : P.light
                o.g(cx, cy, 44, 44, col, 0.4 * env * (1 - easeIn(a / 0.3))); o.e(cx, cy, 120, 3.0, th, P.mid, 0.5 * (1 - easeIn(a / 0.22)))
            }
            for i in 0..<8 {
                let ang2 = th + (frac(i + 9 * k, 3) - 0.5) * 1.4 + (i % 2 == 1 ? Double.pi : 0), d = (30 + 80 * frac(i + 9 * k, 4)) * easeOut(a / 0.4)
                o.e(cx + cos(ang2) * d, cy + sin(ang2) * d * 0.8, 9, 1.5, ang2, i % 2 == 0 ? P.light : P.a1, 0.8 * (1 - easeIn(a / 0.5)))
            }
        }
        if t - last > 0 {
            let a = t - last
            if ti == 0 { o.f(P.light, 0.1 * exp(-a * 20)) }
            let r = 20 + 100 * easeOut(a / 0.35); o.r(cx, cy, r, r * 0.8, 2.4 * (1 - a / 0.4) + 0.4, P.mid, 0.7 * (1 - easeIn(a / 0.4)))
            for i in 0..<26 {
                let ang2 = frac(i, 3) * 6.283, d = (40 + 130 * frac(i, 4)) * easeOut(a / 0.6), tr = a / 0.9
                o.e(cx + cos(ang2) * d, cy + sin(ang2) * d * 0.8 + 40 * a * a, 12, 1.4, ang2 + 1.2 * a, [P.light, P.a1, P.mid][i % 3], 0.8 * (1 - tr))
            }
        }
        return o.prims
    }

    // MARK: spellblade: rune ward

    static func runeWard(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.rune, foot = geo.targets[ti].foot, chest = geo.targets[ti].chest, fx = foot.x, fy = foot.y, cy = chest.y, imp = 0.72
        let N = 6, H = 150.0
        let close = t >= imp ? easeOut(clamp01((t - imp) / 0.4)) : 0.0
        let appear = smooth(t / 0.4), fadeout = 1 - smooth((t - 1.9) / 0.45)
        let R = t >= imp ? lerp(112, 50, close) : 112 - 6 * sin(t * 6)
        let spin = t * (0.5 + 4 * (1 - close)) * (t < imp ? 1.0 : (1 - close))
        for k in 0..<N {
            let dk = Double(k), a = spin + dk * 2 * Double.pi / Double(N), half = Double.pi / Double(N) * (0.86 + 0.14 * close)
            var ptsB: [Pt] = []
            for j in 0..<26 {
                let u = Double(j) / 25, aa = a + (u - 0.5) * 2 * half * (t >= imp ? 1.0 : 0.6)
                ptsB.append(Pt(fx + cos(aa) * R, fy - 4 + sin(aa) * R * 0.28))
            }
            let depth = sin(a)
            for j in stride(from: 0, to: 26, by: 3) {
                let x0 = ptsB[j].x, y0 = ptsB[j].y, u = Double(j) / 25, h = H * (0.92 + 0.08 * sin(u * Double.pi)) * (t < imp ? appear : 1.0)
                let pwp = (0..<15).map { q in Pt(x0, y0 - Double(q) * h / 14 + sin(Double(q) * 0.5 + t * 3 + dk) * 1.5) }
                let ww = (0..<15).map { q in 6 + 2 * sin(Double(q) / 14 * Double.pi) }
                o.k(pwp, ww, depth < 0 ? P.body : P.mid, (depth < 0 ? 0.2 : 0.34) * appear * fadeout, add: true, soft: 5.0)
            }
            let top = ptsB.map { Pt($0.x, $0.y - H * (t < imp ? appear : 1.0)) }
            o.k(top, [Double](repeating: 3.2, count: top.count), P.light, (depth >= 0 ? 0.5 : 0.3) * appear * fadeout, add: true, soft: 2.0)
            o.k(ptsB, [Double](repeating: 3.2, count: ptsB.count), P.light, (depth >= 0 ? 0.55 : 0.3) * appear * fadeout, add: true, soft: 2.0)
            let ca = cos(a), sa = sin(a)
            for m in 0..<3 {
                let uu = pm(t * 0.35 + Double(m) / 3 + dk * 0.13, 1.0), x = fx + ca * R, y = fy - 4 + sa * R * 0.28 - uu * H
                o.g(x, y, 7, 7, P.a1, 0.7 * appear * fadeout * sin(Double.pi * uu))
            }
        }
        if t >= imp {
            let a = t - imp
            if a < 0.5 {
                if ti == 0 { o.f(P.light, 0.1 * exp(-a * 16)) }
                let r = 30 + 120 * easeOut(a / 0.45); o.r(fx, fy - 2, r, r * 0.28, 3.4 * (1 - a / 0.5) + 0.5, P.light, 0.8 * (1 - easeIn(a / 0.5)))
            }
            for k in 0..<N {
                let dk = Double(k), ph = pm(t * 1.4 - dk / Double(N), 1.0), ang = dk * 2 * Double.pi / Double(N) + spin + Double.pi / Double(N)
                let x = fx + cos(ang) * R, y = fy - 4 + sin(ang) * R * 0.28
                let pts = (0..<13).map { q in Pt(x, y - Double(q) * H / 12) }
                o.k(pts, [Double](repeating: 2.6, count: 13), P.light, (0.9 * exp(-ph * 4)) * fadeout, add: true, soft: 2.0)
            }
            o.g(fx, cy, 70, 100, P.body, 0.12 * fadeout)
        }
        if t < imp {
            for i in 0..<30 {
                let ph = frac(i, 1), a = frac(i, 2) * 6.283 + t * 2, r = 120 + 40 * ph
                o.g(fx + cos(a) * r, fy - 6 - frac(i, 3) * H + sin(a) * r * 0.28, 6, 6, P.mid, 0.6 * appear * (1 - clamp01((t - imp + 0.1) / 0.1)))
            }
        }
        return o.prims
    }

    // MARK: spellblade: battle rune

    static func battleRune(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.battle, chest = geo.targets[ti].chest, foot = geo.targets[ti].foot, fx = foot.x, fy = foot.y, cx = chest.x, cy = chest.y, imp = 0.56
        let pre = clamp01((t - 0.05) / (imp - 0.05)), post = t - imp, fade = 1 - smooth((t - 1.75) / 0.35)
        let NODES = (0..<6).map { k -> Pt in let a = Double(k) * Double.pi / 3 + 0.4; return Pt(cx + cos(a) * 46, cy + sin(a) * 58) }
        if t < imp {
            for k in 0..<Int(3 + 9 * pre) {
                let ia = k % 6, ib = (k * 5 + 2) % 6
                if ia != ib { bolt(&o, NODES[ia], NODES[ib], t, Double(k), P, 6 + 6 * pre, 10, 1.6, 0.5 + 0.5 * pre) }
            }
            o.g(cx, cy, 70, 90, P.body, 0.15 + 0.2 * pre)
        }
        if post >= 0 {
            if post < 0.15 && ti == 0 { o.f(P.light, 0.2 * exp(-post * 18)) }
            let env = smooth(post / 0.08) * fade
            for k in 0..<16 {
                let ph = Int(t * 24) + k * 7, r1 = frac(ph, 1), r2 = frac(ph, 2)
                let a1 = Double(k) * 0.393 + r1 * 0.5, ang2 = a1 + 1.2 + r2 * 2.2
                let A = Pt(cx + cos(a1) * (30 + 20 * r1), cy + sin(a1) * (40 + 20 * r1))
                var B = Pt(fx + cos(ang2) * (70 + 60 * r2), fy - 4 + sin(ang2) * 18)
                if k % 3 == 0 { B = Pt(cx + cos(ang2) * (90 + 40 * r2), cy + sin(ang2) * (100 + 30 * r2) - 20) }
                bolt(&o, A, B, t, Double(k + 1), P, 22, 16, 3.0, env * (0.45 + 0.55 * frac(ph, 3)) * (1 - easeIn(post / 1.6) * 0.6))
            }
            for q in 0..<4 {
                let d = Double(q) * 0.06, aa = post - d
                if 0 <= aa && aa < 0.5 {
                    let y = fy - 170 * easeOut(aa / 0.45), w = 62 * (1 - aa / 0.6)
                    let us = (0..<21).map { Double($0) / 20 }
                    let pts = us.map { u in Pt(cx + (u - 0.5) * 2 * w, y + 8 * sin(u * 3.1)) }
                    o.k(pts, us.map { 3.4 * sin(Double.pi * $0) + 0.4 }, [P.light, P.a1, P.mid, P.body][q], 0.8 * (1 - aa / 0.5), add: true, soft: 3.0)
                }
            }
            for i in 0..<34 {
                let tb = frac(i, 1) * 0.6, tt = post - tb
                if !(0 <= tt && tt < 0.8) { continue }
                let ang = frac(i, 3) * 6.283, d = (50 + 120 * frac(i, 4)) * easeOut(tt / 0.5)
                let x = cx + cos(ang) * d, y = cy + sin(ang) * d * 0.6 - 60 * tt * (0.4 + frac(i, 5)) + 120 * tt * tt * b2d(frac(i, 6) > 0.5), k = 1 - tt / 0.8
                o.e(x, y, 8, 1.5, ang, [P.light, P.a1, P.mid][i % 3], 0.8 * k); o.g(x, y, 5, 5, P.light, 0.7 * k)
            }
            for k in 0..<6 {
                let dk = Double(k), ang = dk * 1.047 + 0.3, x = fx + cos(ang) * 60, y = fy - 4 + sin(ang) * 16
                o.g(x, y, 26, 8, P.deep, 0.35 * fade); o.g(x, y, 10, 4, P.mid, 0.5 * fade * (0.5 + 0.5 * sin(t * 25 + dk * 2)))
            }
        }
        return o.prims
    }

    // MARK: dragon knight: dragon flame

    static func dragonFlame(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.flame, C = geo.caster, T = geo.targets[ti].chest, TF = geo.targets[ti].foot, imp = 0.46
        let cx = T.x, cy = T.y, post = t - imp
        let SX = cx - 170, SY = cy - 330
        o.g(SX, SY, 160, 120, P.body, 0.22 * smooth(t / 0.2) * (1 - smooth(post / 0.3)))
        if post < 0.4 { o.g(SX, SY, 70, 60, P.mid, 0.25 * smooth(t / 0.2) * (1 - smooth(post / 0.3))) }
        func path(_ tt: Double) -> (Double, Double, Double) {
            let s = pw(easeIn(clamp01(tt / imp)), 1.5)
            return (lerp(SX, cx, s) + sin(s * 5) * 8 * (1 - s), lerp(SY, cy, s), s)
        }
        if t < imp + 0.03 {
            let (hx, hy, _) = path(t)
            var pts: [Pt] = [], ws: [Double] = []
            for i in stride(from: 48, through: 0, by: -1) {
                let tt = t - Double(i) * 0.012
                if tt < 0 { continue }
                let (x, y, _) = path(tt), u = Double(i) / 48, di = Double(i)
                pts.append(Pt(x + sin(tt * 40 + di * 0.6) * 5 * u, y + cos(tt * 33 + di * 0.4) * 5 * u)); ws.append((13 * pw(1 - u, 0.9) + 1.0) * (0.5 + 0.5 * clamp01(tt * 6)))
            }
            if pts.count > 3 { o.stack(pts, ws, [(1.8, P.deep, true, 0.22), (1.0, P.body, true, 0.5), (0.5, P.mid, true, 0.8), (0.2, P.a1, true, 0.95)]) }
            for q in 0..<12 {
                let dq = Double(q)
                var fp: [Pt] = [], fw: [Double] = []
                for j in 0..<18 {
                    let u = Double(j) / 17
                    fp.append(Pt(hx - (cx - SX) / 380 * u * 90 + sin(u * 7 + t * 20 + dq * 1.1) * 10 * u + (dq - 5.5) * 3, hy - (cy - SY) / 380 * u * 90 + cos(u * 6 + t * 17 + dq) * 8 * u)); fw.append(6 * pw(1 - u, 0.9) + 0.4)
                }
                o.k(fp, fw, [P.mid, P.a2, P.body][q % 3], 0.5, add: true, soft: 1.6)
            }
            o.g(hx, hy, 70, 70, P.body, 0.5); o.g(hx, hy, 34, 34, P.mid, 0.8); o.g(hx, hy, 14, 14, P.a1, 1.0)
        }
        if post >= 0 {
            if post < 0.25 && ti == 0 { o.f(P.mid, 0.26 * exp(-post * 12)) }
            o.g(cx, cy, 290 * (0.5 + easeOut(post / 0.3)), 190 * (0.5 + easeOut(post / 0.3)), P.body, 0.45 * (1 - easeIn(post / 0.7)))
            o.g(cx, cy, 70, 60, P.a1, 0.8 * (1 - easeIn(post / 0.22)))
            for k in 0..<22 {
                let dk = Double(k), a = dk * 2 * Double.pi / 22 + 0.2 * frac(k, 2), L = (120 + 110 * frac(k, 3)) * easeOut(post / 0.45)
                let x = TF.x + cos(a) * L, y = TF.y - 4 + sin(a) * L * 0.27
                flame(&o, x, y, 40 + 60 * frac(k, 4) * (1 - easeIn(post / 1.4)), 10, t, dk, P, (1 - easeIn((post - 0.4) / 1.2)) * smooth(post / 0.1))
            }
            for i in 0..<48 {
                let di = Double(i), ang = frac(i, 5) * 6.283, rr = 20 + 150 * frac(i, 6), x = TF.x + cos(ang) * rr * 1.1, y = TF.y - 3 + sin(ang) * rr * 0.27
                let born = 0.15 + 0.5 * frac(i, 7), lifeA = clamp01((post - born) / 0.2) * (1 - clamp01((post - born - 0.9 - 0.5 * frac(i, 8)) / 0.5))
                if lifeA > 0.01 { flame(&o, x, y, (26 + 44 * frac(i, 9)) * (0.7 + 0.3 * sin(t * 11 + di)), 5.5 + 4 * frac(i, 1), t, di + 20, P, lifeA, 18) }
            }
            for i in 0..<14 {
                let u = clamp01((post - 0.2 - 0.05 * Double(i)) / 1.3)
                if 0 < u && u < 1 { o.g(TF.x + (frac(i, 1) - 0.5) * 100, TF.y - 30 - u * 190, 36 + 34 * u, 30 + 26 * u, P.deep, 0.24 * sin(Double.pi * u)) }
            }
            o.g(TF.x, TF.y - 2, 120, 26, P.deep, 0.36 * smooth(post / 0.3) * (1 - smooth((post - 1.6) / 0.6)))
            for i in 0..<60 {
                let tb = 0.02 + 0.5 * frac(i, 1), tt = post - tb
                if !(0 <= tt && tt < 1.2) { continue }
                let a = frac(i, 3) * 6.283, r = (40 + 190 * frac(i, 4)) * easeOut(tt / 0.6), k = 1 - tt / 1.2
                o.e(cx + cos(a) * r, cy + 20 + sin(a) * r * 0.4 - 130 * tt * (0.4 + frac(i, 5)) + 90 * tt * tt, 9, 1.6, a - 1.2 * tt, [P.a1, P.mid, P.a2][i % 3], 0.85 * k * (0.6 + 0.4 * sin(tt * 30 + Double(i))))
            }
        }
        if t < imp + 0.9 && ti == 0 {
            let e = smooth((t - 0.05) / 0.2) * (1 - smooth((t - imp - 0.5) / 0.4)); o.g(C.x + 26, C.y - 6, 36, 40, P.mid, 0.25 * e)
        }
        return o.prims
    }

    // MARK: dragon knight: dragon scale ward

    static func scaleWard(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.scale, chest = geo.targets[ti].chest, foot = geo.targets[ti].foot, fx = foot.x, fy = foot.y, cx = chest.x, cy = chest.y, imp = 0.56
        let fadeout = 1 - smooth((t - 1.85) / 0.4)
        let ORB: [(Double, Double, Double, Int)] = [(60, 0.35, 1.0, 5), (74, 1.15, -0.65, 5), (86, -1.2, 0.5, 5)]
        let BR = RGB(96, 52, 14)
        for (oi, (R, tilt, spd, n)) in ORB.enumerated() {
            let doi = Double(oi)
            let lock = t >= imp - 0.3 ? easeOut(clamp01((t - imp + 0.16 * (2 - doi) - 0.1) / 0.34)) : 0.0
            for k in 0..<n {
                let dk = Double(k)
                let drop = clamp01((t - 0.05 * dk - 0.08 * doi) / (imp - 0.1)), fall = pw(1 - easeOut(drop), 1.5)
                let a0 = spd * t * (1 + 1.5 * (1 - lock)) + dk * 2 * Double.pi / Double(n) + doi
                let half = 0.30 - 0.03 * doi
                var pts: [Pt] = []
                for j in 0..<24 {
                    let a = a0 + (Double(j) / 23 - 0.5) * 2 * half, x = cos(a) * R, z = sin(a) * R
                    let y = z * sin(tilt) * 1.0 + fall * -170, px = cx + x * cos(tilt * 0.6), py = cy + y * 1.05 + z * 0.12
                    pts.append(Pt(px, py))
                }
                let depth = sin(a0) * cos(tilt)
                let alpha = (depth > -0.3 ? 1.0 : 0.55) * fadeout * smooth(drop * 3)
                let ws = (0..<24).map { j in 8.5 * pw(sin(Double.pi * (Double(j) / 23)), 0.6) + 1.6 }
                o.stack(pts, ws, [(1.3, BR, false, 0.9), (1.0, P.body, false, 1.0), (0.5, P.mid, false, 0.85), (0.16, P.light, true, 0.95)], alpha)
                o.k(pts, ws.map { $0 * 2.4 }, P.body, 0.12 * alpha, add: true, soft: 6)
                o.k(pts, [Double](repeating: 1.0, count: pts.count), P.light, 0.5 * alpha, add: true, soft: 1.0)
            }
        }
        if t >= imp {
            let a = t - imp
            if a < 0.5 {
                if ti == 0 { o.f(P.mid, 0.12 * exp(-a * 16)) }
                let r = 24 + 130 * easeOut(a / 0.45); o.r(fx, fy - 2, r, r * 0.28, 6 * (1 - a / 0.5) + 0.6, P.light, 0.8 * (1 - easeIn(a / 0.5)))
                let r2 = 40 + 90 * easeOut(a / 0.35); o.r(cx, cy, r2, r2 * 1.25, 3 * (1 - a / 0.4) + 0.5, P.mid, 0.6 * (1 - easeIn(a / 0.4)))
            }
            for (oi, (R, tilt, _, _)) in ORB.enumerated() {
                let ph = pm(t * 1.1 - Double(oi) * 0.18, 1.0)
                let pts = arcPts(cx, cy, R * cos(tilt * 0.6), R * sin(abs(tilt)) * 1.05 + 2, 0, 6.283, 60, 0)
                o.k(pts, [Double](repeating: 1.1, count: pts.count), P.a2, (0.5 * exp(-ph * 3.5) + 0.14) * fadeout, add: true, soft: 1.2)
            }
            o.g(cx, cy, 80, 110, P.body, 0.1 * fadeout)
            for i in 0..<20 {
                let u = pm(t * 0.35 + frac(i, 1), 1.0), ang = frac(i, 2) * 6.283 + t * 0.5
                o.g(cx + cos(ang) * 80 * frac(i, 3), fy - 6 - u * 190, 7, 7, [P.light, P.a1, P.mid][i % 3], 0.6 * fadeout * sin(Double.pi * u))
            }
        }
        return o.prims
    }

    // MARK: dragon knight: dragon order

    static func dragonOrder(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.order, C = geo.caster, CF = geo.casterFoot, imp = 0.56
        let BEATS = [imp, imp + 0.3, imp + 0.6], fadeout = 1 - smooth((t - 1.85) / 0.3)
        if t < imp && ti == 0 {
            for k in 0..<3 {
                let tap = max(0.0, 1 - abs(t - (0.15 + Double(k) * 0.17)) / 0.06); o.g(C.x, C.y, 44 + 30 * tap, 54 + 30 * tap, P.body, 0.12 + 0.3 * tap)
            }
        }
        for (bi, tb) in BEATS.enumerated() {
            let a = t - tb
            if a < 0 { continue }
            let big = 1.0 + 0.5 * b2d(bi == 2), dbi = Double(bi)
            if a < 0.14 && ti == 0 { o.f(P.mid, (0.1 + 0.08 * dbi) * exp(-a * 24)) }
            for rI in 0..<(ti == 0 ? 3 : 0) {
                let d = Double(rI) * 0.05, tt = a - d
                if tt < 0 { continue }
                let r = (40 + 470 * easeOut(tt / 0.85)) * big, fade = 1 - easeIn(tt / 0.9)
                o.arc(C.x + 20, C.y, r, r * 0.52, -1.15, 1.15, (7.0 - Double(rI) * 1.8) * fade + 0.8, [P.light, P.a1, P.mid][rI], 0.85 * fade)
            }
            if ti == 0 { let r = 20 + 130 * big * easeOut(a / 0.5); o.r(CF.x, CF.y - 2, r, r * 0.27, 6 * (1 - a / 0.55) + 0.6, P.mid, 0.8 * (1 - easeIn(a / 0.55))) }
            for (n, tg) in [(ti, geo.targets[ti])] {
                let hit = a - 0.1 - 0.05 * Double(n)
                if hit < 0 { continue }
                let cx = tg.chest.x, cy = tg.chest.y, fx = tg.foot.x, fy = tg.foot.y
                let R0 = 130 * big, rr = R0 * (1 - easeOut(hit / 0.26)) + 14, al = (1 - easeIn(hit / 0.3)) * smooth(hit / 0.04)
                o.r(cx, cy, rr * 0.8, rr * 1.3, 4.0 * al + 0.5, [P.a1, P.light, P.mid][bi], 0.9 * al)
                o.r(fx, fy - 2, rr * 1.4, rr * 1.4 * 0.27, 3.4 * al + 0.5, P.mid, 0.7 * al)
                if hit < 0.3 {
                    o.g(cx, cy, 70 * (1 - easeIn(hit / 0.3)) + 36, 92 * (1 - easeIn(hit / 0.3)) + 46, P.a1, 0.45 * al * (1 + 0.4 * dbi)); o.g(cx, cy, 24, 32, white, 0.5 * al)
                }
                for i in 0..<10 {
                    let ang = frac(i + 11 * bi, 3) * 6.283, d = (30 + 70 * frac(i + 11 * bi, 4)) * easeOut(hit / 0.4)
                    o.e(cx + cos(ang) * d, cy + sin(ang) * d * 0.8 - 20 * hit, 9, 1.5, ang, [P.a1, P.light, P.a2][i % 3], 0.8 * (1 - easeIn(hit / 0.55)))
                }
            }
        }
        let last = t - BEATS[2]
        for (n, tg) in [(ti, geo.targets[ti])] {
            if last < 0.15 { continue }
            let cx = tg.chest.x, cy = tg.chest.y, ph = pm(t * 2.0 - Double(n) * 0.2, 1.0), env = smooth((last - 0.15) / 0.25) * fadeout
            o.g(cx, cy, 52 + 14 * exp(-ph * 5), 80 + 18 * exp(-ph * 5), P.body, (0.14 + 0.3 * exp(-ph * 5)) * env)
            o.r(cx, cy, 44 + 30 * ph, 70 + 40 * ph, 1.8 * (1 - ph) + 0.4, P.a1, 0.7 * (1 - ph) * env)
            for i in 0..<12 {
                let u = pm(t * 0.5 + frac(i, 1), 1.0), ang = frac(i, 2) * 6.283
                o.g(cx + cos(ang) * 40 * frac(i, 3), tg.foot.y - 6 - u * 150, 7, 7, [P.a1, P.light, P.mid][i % 3], 0.6 * env * sin(Double.pi * u))
            }
        }
        return o.prims
    }

    // MARK: healing (micro, standard, strong)

    static func healMicro(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.heal, chest = geo.targets[ti].chest, foot = geo.targets[ti].foot, fx = foot.x, fy = foot.y, cx = chest.x, cy = chest.y
        let fade = 1 - smooth((t - 1.1) / 0.25)
        let r = 10 + 40 * easeOut(t / 0.6); o.thinRing(fx, fy - 2, r, r * 0.27, 1.5 * (1 - t / 0.7) + 0.4, P.mid, 0.7 * (1 - easeIn(t / 0.7)))
        let pulse = exp(-pow((t - 0.28) / 0.13, 2)); o.g(cx, cy, 60, 74, P.body, 0.4 * pulse); o.g(cx, cy, 18, 22, P.light, 0.6 * pulse)
        o.thinRing(cx, cy, 14 + 40 * easeOut((t - 0.2) / 0.45), 18 + 52 * easeOut((t - 0.2) / 0.45), 1.2, P.light, 0.6 * (1 - easeIn((t - 0.2) / 0.5)) * smooth((t - 0.2) / 0.05))
        for i in 0..<7 {
            let di = Double(i), u = clamp01((t - 0.05 * di) / 1.0)
            if u <= 0 || u >= 1 { continue }
            func pos(_ uu: Double) -> Pt { Pt(fx + (frac(i, 2) - 0.5) * 44 + sin(uu * 5.5 + di * 1.7) * (11 + 9 * frac(i, 3)), fy - 8 - uu * (110 + 50 * frac(i, 4))) }
            let pts = (0..<12).map { q in pos(max(0.0, u - 0.16 * (1 - Double(q) / 11))) }
            let env = pw(sin(Double.pi * u), 0.8) * fade
            o.k(pts, (0..<12).map { q in 0.5 + 3.2 * (Double(q) / 11) }, P.mid, 0.9 * env, add: true, soft: 1.2)
            let p = pos(u), col = [P.light, P.a1, P.mid][i % 3]
            o.g(p.x, p.y, 15, 15, col, 0.7 * env); o.g(p.x, p.y, 4.6, 4.6, white, 1.0 * env)
        }
        return o.prims
    }

    static func healStandard(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.heal, chest = geo.targets[ti].chest, foot = geo.targets[ti].foot, fx = foot.x, fy = foot.y, cx = chest.x, cy = chest.y
        let fade = 1 - smooth((t - 1.45) / 0.3)
        for q in 0..<2 {
            let head = easeOut(clamp01(t / 0.9)), tail = easeIn(clamp01((t - 0.7) / 0.8))
            var pts: [Pt] = [], ws: [Double] = []
            for j in 0..<80 {
                let u = Double(j) / 79
                if u > head || u < tail * 0.9 { continue }
                let ang = Double(q) * Double.pi + u * 11 - t * 3.2, rr = 38 - 8 * u
                pts.append(Pt(fx + cos(ang) * rr, fy - 6 - u * 170 + sin(ang) * rr * 0.3)); ws.append(3.2 * pw(sin(Double.pi * u), 0.6) + 0.6)
            }
            if pts.count > 3 { o.stack(pts, ws, [(3.0, P.body, true, 0.16), (1.0, P.mid, true, 0.6), (0.4, P.light, true, 0.95)], fade) }
        }
        if t > 0.3 {
            let a = t - 0.3
            for k in 0..<2 {
                let d = Double(k) * 0.12, aa = a - d
                if aa >= 0 {
                    let r = 20 + 80 * easeOut(aa / 0.6); o.thinRing(fx, fy - 2, r, r * 0.27, 1.8 * (1 - aa / 0.7) + 0.4, k == 0 ? P.mid : P.a2, 0.75 * (1 - easeIn(aa / 0.7)))
                    o.thinRing(cx, cy, r * 0.6, r * 1.1, 1.2, k == 0 ? P.light : P.mid, 0.5 * (1 - easeIn(aa / 0.7)))
                }
            }
            o.g(cx, cy, 70 * (0.5 + easeOut(a / 0.5)), 100 * (0.5 + easeOut(a / 0.5)), P.body, 0.22 * (1 - easeIn(a / 1.0)))
        }
        for i in 0..<46 {
            let tb = 0.3 + 0.9 * frac(i, 1), tt = t - tb
            if !(0 <= tt && tt < 0.7) { continue }
            let x = fx + (frac(i, 2) - 0.5) * 150, y = cy - 150 + tt * (190 + 60 * frac(i, 3)), k = pw(sin(Double.pi * tt / 0.7), 0.8) * fade
            o.e(x, y, 1.2, 8 + 5 * frac(i, 4), 0, [P.light, P.mid, P.a1][i % 3], 0.8 * k); o.g(x, y, 5, 5, P.mid, 0.4 * k)
        }
        for i in 0..<8 {
            let tb = 0.4 + 0.8 * frac(i, 1), tt = t - tb
            if 0 <= tt && tt < 0.4 {
                let ang = frac(i, 2) * 6.283, x = cx + cos(ang) * 28 * frac(i, 3), y = cy + sin(ang) * 50 * frac(i, 4), k = sin(Double.pi * tt / 0.4) * fade
                o.e(x, y, 11, 1.1, 0, P.light, 0.9 * k); o.e(x, y, 11, 1.1, 1.571, P.light, 0.9 * k); o.g(x, y, 7, 7, P.mid, 0.5 * k)
            }
        }
        return o.prims
    }

    static func healStrong(_ t: Double, _ geo: Geometry, _ ti: Int) -> [Prim] {
        var o = Out(); let P = Pal.heal, chest = geo.targets[ti].chest, foot = geo.targets[ti].foot, fx = foot.x, fy = foot.y, cx = chest.x, cy = chest.y
        let fade = 1 - smooth((t - 1.85) / 0.4)
        for q in 0..<4 {
            let dq = Double(q), env = smooth((t - 0.1 - 0.06 * dq) / 0.5) * fade
            var pts: [Pt] = [], ws: [Double] = []
            for j in 0..<50 {
                let u = Double(j) / 49
                pts.append(Pt(fx + (dq - 1.5) * 34 + sin(u * 4 + t * 1.6 + dq * 2) * (14 + 12 * u), fy - 4 - u * (150 + 40 * frac(q, 1)))); ws.append(20 * pw(sin(Double.pi * (u * 0.85 + 0.08)), 0.8) + 2)
            }
            o.k(pts, ws, [P.body, P.a2, P.mid, P.body][q], 0.3 * env, add: true, soft: 10)
            o.k(pts, ws.map { $0 * 0.1 + 0.5 }, q % 2 == 0 ? P.light : P.mid, 0.4 * env, add: true, soft: 1.0)
        }
        for (k, tb) in [0.3, 0.62].enumerated() {
            let a = t - tb
            if a >= 0 {
                let r = 14 + 130 * easeOut(a / 0.6)
                o.thinRing(cx, cy, r * 0.9, r * 1.15, 1.8 * (1 - a / 0.65) + 0.4, k == 0 ? P.light : P.mid, 0.8 * (1 - easeIn(a / 0.65)))
                o.thinRing(fx, fy - 2, r * 1.2, r * 1.2 * 0.27, 1.8 * (1 - a / 0.65) + 0.4, P.mid, 0.7 * (1 - easeIn(a / 0.65)))
                o.g(cx, cy, 60 * (1 - easeIn(a / 0.3)) + 30, 80 * (1 - easeIn(a / 0.3)) + 40, k == 1 ? P.a1 : P.body, 0.35 * (1 - easeIn(a / 0.35)))
            }
        }
        if t > 0.3 && t < 1.5 {
            let env = smooth((t - 0.3) / 0.2) * (1 - smooth((t - 1.1) / 0.4))
            for k in 0..<30 {
                let dk = Double(k), ang = dk * 2 * Double.pi / 30 + t * 0.25, L = 70 + 80 * frac(k, 2), s = 1 + 0.08 * sin(t * 4 + dk)
                o.e(cx + cos(ang) * L * s / 2, cy + sin(ang) * L * s / 2 * 0.95, L * s / 2, 1.1, ang, [P.mid, P.light, P.a2, P.mid][k % 4], 0.4 * env)
            }
        }
        if t > 0.3 && ti == 0 { o.f(P.a1, 0.1 * exp(-(t - 0.3) * 14)) }
        for i in 0..<44 {
            let tb = 0.25 + 0.5 * frac(i, 1), tt = t - tb
            if !(0 <= tt && tt < 1.3) { continue }
            let vx = (frac(i, 2) - 0.5) * 120, vy = -(170 + 100 * frac(i, 3))
            let x = fx + vx * tt, y = fy - 10 + vy * tt + 230 * tt * tt, vyn = vy + 460 * tt
            let k = pw(sin(Double.pi * clamp01(tt / 1.3)), 0.6) * fade, col = [P.light, P.mid, P.a1, P.a2][i % 4]
            let sp = hypot(vx, vyn)
            o.e(x - vx * 0.012, y - vyn * 0.012, max(3, sp * 0.02), 1.2, atan2(vyn, vx), col, 0.85 * k); o.g(x, y, 6, 6, col, 0.5 * k); o.g(x, y, 2.4, 2.4, white, 0.9 * k)
        }
        o.g(cx, cy, 80 + 6 * sin(t * 5), 110 + 6 * sin(t * 5), P.body, 0.14 * smooth((t - 0.3) / 0.4) * fade)
        return o.prims
    }

    // MARK: camera (how the lens answers each skill)

    struct Camera: Equatable { var dx = 0.0, dy = 0.0, zoom = 0.0, rotation = 0.0
        static let zero = Camera()
        static func + (a: Camera, b: Camera) -> Camera { Camera(dx: a.dx + b.dx, dy: a.dy + b.dy, zoom: a.zoom + b.zoom, rotation: a.rotation + b.rotation) }
    }

    /// A damped thump: amplitude `a` at `t0`, decaying at rate `k`, ringing at `w` rad/s.
    private static func thump(_ t: Double, _ t0: Double, _ a: Double, _ k: Double, _ w: Double, _ phase: Double = 0) -> Double {
        let r = t - t0
        return r < 0 ? 0 : a * exp(-r * k) * cos(r * w + phase)
    }

    /// Lens kick in layout units (the same units as `MeadowBattleHitFeel.camera`). `direction` is +1 when the effect travels to the right.
    static func camera(skill id: String, t: Double, direction: Double) -> Camera {
        guard t >= 0, let i = info[id], t < i.duration else { return .zero }
        var c = Camera()
        switch id {
        case "starlightPulse":
            c.zoom = 0.008 * smooth(t / 0.75) * b2d(t < 0.75) + max(0, thump(t, 0.75, 0.024, 7, 0))
            c.dx = direction * thump(t, 0.75, 3.0, 9, 30); c.dy = -thump(t, 0.75, 1.6, 10, 34, 0.6)
        case "dragonSoulWard":
            c.zoom = 0.014 * smooth(t / 0.38) * b2d(t < 0.38) + max(0, thump(t, 0.38, 0.03, 6, 0))
            c.dy = -thump(t, 0.38, 3.0, 8, 34, 0.6); c.rotation = thump(t, 0.38, 0.004, 9, 24)
        case "runeSlash":
            for k in 0..<5 {
                let t0 = 1.048 + 0.06 * Double(k), s: Double = k % 2 == 0 ? 1 : -1
                c.dx += direction * s * thump(t, t0, 3.4, 26, 62); c.dy += -s * thump(t, t0, 1.6, 24, 70, 0.4)
            }
            c.zoom = max(0, thump(t, 1.35, 0.03, 8, 0)); c.rotation = direction * thump(t, 1.35, 0.006, 10, 28)
        case "runeWard":
            c.zoom = max(0, thump(t, 1.12, 0.02, 10, 0)); c.dy = -thump(t, 1.12, 2.2, 12, 40, 0.6); c.zoom += 0.006 * smooth(t / 0.72) * b2d(t < 1.12)
        case "battleRune":
            let r = t - 0.56
            if r >= 0 { c.dx = 2.6 * sin(t * 71) * exp(-r * 2.2); c.dy = 2.0 * sin(t * 83 + 1) * exp(-r * 2.4); c.zoom = max(0, thump(t, 0.56, 0.02, 8, 0)) }
        case "dragonFlame":
            c.dx = direction * thump(t, 0.46, 7.0, 7, 28); c.dy = -thump(t, 0.46, 4.0, 8, 36, 0.6)
            c.zoom = max(0, thump(t, 0.46, 0.045, 6, 0)); c.rotation = direction * thump(t, 0.46, 0.008, 8, 26)
            let r = t - 0.9
            if r >= 0 && r < 1.0 { c.dy += 0.9 * sin(t * 47) * (1 - r) }
        case "dragonScaleWard":
            c.zoom = max(0, thump(t, 0.56, 0.032, 9, 0)); c.dy = -thump(t, 0.56, 3.2, 10, 30, 0.6)
        case "dragonOrder":
            for (k, amp) in [0.02, 0.022, 0.036].enumerated() {
                let t0 = 0.56 + 0.3 * Double(k)
                c.zoom += max(0, thump(t, t0, amp, 12, 0)); c.dy += -thump(t, t0, 1.6 + Double(k), 14, 40, 0.5)
            }
        default:
            c.zoom = 0.006 * sin(Double.pi * t / i.duration)
        }
        return c
    }

    // MARK: ambient light (the stage answers each skill)

    /// 0...1 light level driven by the skill's own phases: it builds into the release, holds, and fades with the effect.
    static func light(skill id: String, t: Double) -> Double {
        guard let i = info[id], t >= 0, t < i.duration else { return 0 }
        let rise = smooth(t / max(0.1, i.release * 0.8))
        let fall = 1 - smooth((t - i.duration * 0.62) / (i.duration * 0.38))
        return clamp01(rise * fall)
    }
}
