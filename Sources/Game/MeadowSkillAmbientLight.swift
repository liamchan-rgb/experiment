import Foundation

/// How a skill lights its surroundings: a stage-wide colour wash, a pool of light (and a squashed reflection of the
/// effect) on the floor, and glowing motes that drift over the characters. Presentation only; pure Foundation so
/// `scripts/battle-ambient-regression.swift` can compile it without UIKit. Layout units are points of the party stage.
enum MeadowSkillAmbientLight {
    struct Tone: Equatable { let r: Double, g: Double, b: Double }

    /// One glowing speck, relative to the skill's centre. `radius` is the halo radius, `core` the bright pixel size.
    struct Mote: Equatable { let id: Int, dx: Double, dy: Double, radius: Double, core: Double, alpha: Double, hot: Bool }

    static let skillIDs = ["starlightPulse", "rally", "sweep", "dragonSoulWard", "dragonScaleWard"]

    static func tone(for id: String) -> Tone {
        switch id {
        case "starlightPulse": return Tone(r: 0.46, g: 0.40, b: 1.0)
        case "rally": return Tone(r: 1.0, g: 0.76, b: 0.30)
        case "sweep": return Tone(r: 0.42, g: 0.78, b: 1.0)
        case "dragonSoulWard": return Tone(r: 0.29, g: 0.67, b: 1.0)
        default: return Tone(r: 1.0, g: 0.55, b: 0.18)
        }
    }

    static func clamp01(_ x: Double) -> Double { min(1, max(0, x)) }
    static func smooth(_ x: Double) -> Double { let t = clamp01(x); return t * t * (3 - 2 * t) }
    static func fraction(_ i: Int, _ salt: Int) -> Double { Double((i * 73 + salt * 37 + (i * i) * 11) % 101) / 100.0 }

    /// 0...1 light level: eases up to the peak frame, holds briefly, then fades by the end of the effect.
    static func level(age: Double, peak: Double, duration: Double) -> Double {
        guard age >= 0, age < duration else { return 0 }
        let rise = smooth(age / max(0.05, peak * 0.9))
        let fall = 1 - smooth((age - peak - 0.08) / max(0.05, duration - peak - 0.08))
        return clamp01(rise * (age <= peak ? 1 : fall))
    }

    static func moteCount(for id: String) -> Int { id == "sweep" ? 16 : 22 }

    /// Glowing specks; ids are fixed so every frame is a continuation of the previous one.
    static func motes(skill id: String, age: Double, duration: Double, spread: Double) -> [Mote] {
        guard age >= 0, age < duration else { return [] }
        var out: [Mote] = []
        for i in 0..<moteCount(for: id) {
            let born = fraction(i, 1) * duration * 0.55
            let life = 0.45 + 0.5 * fraction(i, 2)
            let t = (age - born) / life
            guard t >= 0, t < 1 else { continue }
            let a0 = fraction(i, 3) * 2 * Double.pi
            let r0 = spread * (0.15 + 0.85 * fraction(i, 4))
            var x = cos(a0) * r0, y = sin(a0) * r0 * 0.6
            var size = 22 + 20 * fraction(i, 5)
            switch id {
            case "starlightPulse":                       // twinkling dust drifting outward
                let push = 1 + 0.35 * t
                x *= push; y *= push; y -= 8 * t
            case "rally", "dragonScaleWard":             // embers lifting off and swaying
                y -= 46 * t * (0.6 + fraction(i, 6)); x += sin(t * 6 + Double(i)) * 6
            case "sweep":                                // spray flung from the arc
                x = spread * (0.2 + 1.0 * t) * (fraction(i, 7) > 0.5 ? 1 : 0.7); y = (fraction(i, 8) - 0.5) * spread * 1.1 + 14 * t * t
            default:                                     // soul ward: droplets circling up
                let th = a0 + t * 3.2
                x = cos(th) * r0; y = sin(th) * r0 * 0.5 - 40 * t
            }
            size *= id == "starlightPulse" ? 0.8 : 1
            var alpha = pow(sin(Double.pi * t), 0.8)
            if id == "starlightPulse" { alpha *= 0.55 + 0.45 * sin(age * 22 + Double(i) * 2) }
            out.append(Mote(id: i, dx: x, dy: y, radius: size, core: 1.5 + 1.5 * fraction(i, 9), alpha: clamp01(alpha), hot: fraction(i, 10) > 0.6))
        }
        return out
    }
}
