import Foundation

// Pure check of MeadowSkillAmbientLight: envelope, determinism, bounds and frame-to-frame continuity of the motes.
@main
struct BattleAmbientRegression {
    static var failures = 0
    static func check(_ ok: @autoclosure () -> Bool, _ message: @autoclosure () -> String) {
        if !ok() { failures += 1; if failures <= 25 { fputs("FAIL: \(message())\n", stderr) } }
    }

    /// Charge-up, target reaction and afterglow: bounds, expiry, direction of travel and frame-to-frame continuity.
    static func checkStagecraft(_ samples: inout Int) {
        typealias L = MeadowSkillAmbientLight
        for id in L.skillIDs {
            check(L.charge(skill: id, progress: 0) == nil && L.charge(skill: id, progress: 1.01) == nil, "\(id) charge outside 0...1")
            let early = L.charge(skill: id, progress: 0.1)!, late = L.charge(skill: id, progress: 0.9)!
            func mean(_ c: L.Charge) -> Double { c.motes.map { hypot($0.dx, $0.dy) }.reduce(0, +) / Double(c.motes.count) }
            check(mean(late) < mean(early), "\(id) charge motes converge on the caster")
            check(late.ringRadius < early.ringRadius && late.level > early.level, "\(id) charge ring contracts and light grows")
            var prev: [L.Mote] = []
            var p = 1.0 / 30
            while p <= 1 {
                let c = L.charge(skill: id, progress: p)!
                for m in c.motes {
                    samples += 1
                    check(m.alpha >= 0 && m.alpha <= 1 && abs(m.dx) < 200 && abs(m.dy) < 200, "\(id) charge mote range")
                    if let a = prev.first(where: { $0.id == m.id }) { check(hypot(a.dx - m.dx, a.dy - m.dy) < 30, "\(id) charge mote \(m.id) jump at \(p)") }
                }
                check(c.level >= 0 && c.level <= 1 && c.ringAlpha >= 0 && c.ringAlpha <= 1, "\(id) charge level range")
                prev = c.motes; p += 1.0 / 30
            }
            let life = L.isWard(id) ? L.wardReactionLife : L.reactionLife
            check(L.reaction(skill: id, age: -0.01) == nil && L.reaction(skill: id, age: life + 0.01) == nil, "\(id) reaction window")
            check(L.reaction(skill: id, age: 0.05) != nil, "\(id) reacts at impact")
            if L.isWard(id) {
                check(L.reaction(skill: id, age: 0.6)!.aura > 0.9, "\(id) ward aura holds")
                check(L.reaction(skill: id, age: 1.6)!.aura < 0.2, "\(id) ward aura fades out")
            } else {
                check(L.reaction(skill: id, age: 0.01)!.glow > L.reaction(skill: id, age: 0.3)!.glow, "\(id) strike flash decays")
            }
            var prevR: [L.Mote] = [], t = 0.0
            while t < life {
                if let r = L.reaction(skill: id, age: t) {
                    check(r.glow >= 0 && r.glow <= 1 && r.aura >= 0 && r.aura <= 1, "\(id) reaction range")
                    for m in r.motes {
                        samples += 1
                        check(m.alpha >= 0 && m.alpha <= 1 && abs(m.dx) < 120 && abs(m.dy) < 120, "\(id) reaction mote range")
                        if let a = prevR.first(where: { $0.id == m.id }) { check(hypot(a.dx - m.dx, a.dy - m.dy) < 14, "\(id) reaction mote \(m.id) jump at \(t)") }
                    }
                    prevR = r.motes
                }
                t += 1.0 / 60
            }
            check(L.afterglow(skill: id, age: -0.01, spread: 90) == nil && L.afterglow(skill: id, age: L.afterglowLife + 0.01, spread: 90) == nil, "\(id) afterglow window")
            check(L.afterglow(skill: id, age: 0.05, spread: 90)!.pool > L.afterglow(skill: id, age: 0.8, spread: 90)!.pool, "\(id) afterglow decays")
        }
    }

    static func main() {
        let specs: [String: (peak: Double, duration: Double, width: Double)] = [
            "starlightPulse": (12.0 / 16, 20.0 / 16, 344), "rally": (14.0 / 12, 20.0 / 12, 256),
            "sweep": (9.0 / 20, 20.0 / 20, 339), "dragonSoulWard": (12.0 / 12, 20.0 / 12, 256),
            "dragonScaleWard": (12.0 / 20, 20.0 / 20, 256)]
        var samples = 0
        for id in MeadowSkillAmbientLight.skillIDs {
            let s = specs[id]!
            check(MeadowSkillAmbientLight.level(age: -0.01, peak: s.peak, duration: s.duration) == 0, "\(id) level before start")
            check(MeadowSkillAmbientLight.level(age: s.duration, peak: s.peak, duration: s.duration) == 0, "\(id) level after end")
            check(MeadowSkillAmbientLight.level(age: s.peak, peak: s.peak, duration: s.duration) > 0.95, "\(id) level at peak")
            let tone = MeadowSkillAmbientLight.tone(for: id)
            check([tone.r, tone.g, tone.b].allSatisfy { $0 >= 0 && $0 <= 1 }, "\(id) tone range")
            var previous: [MeadowSkillAmbientLight.Mote] = []
            var step = 0.0
            var sawMotes = false
            while step < s.duration {
                let level = MeadowSkillAmbientLight.level(age: step, peak: s.peak, duration: s.duration)
                check(level >= 0 && level <= 1, "\(id) level range at \(step)")
                let motes = MeadowSkillAmbientLight.motes(skill: id, age: step, duration: s.duration, spread: s.width * 0.36)
                check(motes == MeadowSkillAmbientLight.motes(skill: id, age: step, duration: s.duration, spread: s.width * 0.36), "\(id) deterministic")
                check(motes.count <= MeadowSkillAmbientLight.moteCount(for: id), "\(id) mote cap")
                for m in motes {
                    samples += 1
                    check(m.alpha >= 0 && m.alpha <= 1 && m.radius > 0 && m.core > 0, "\(id) mote values")
                    check(abs(m.dx) <= s.width && abs(m.dy) <= s.width, "\(id) mote stays near the skill (\(m.dx), \(m.dy))")
                }
                sawMotes = sawMotes || !motes.isEmpty
                // Continuity: a mote alive in two consecutive 1/60 s samples never jumps more than a few points.
                for b in motes {
                    if let a = previous.first(where: { $0.id == b.id }) { check(hypot(a.dx - b.dx, a.dy - b.dy) < 12, "\(id) mote \(b.id) jump at \(step)") }
                }
                previous = motes
                step += 1.0 / 60
            }
            check(sawMotes, "\(id) produces motes")
            check(MeadowSkillAmbientLight.motes(skill: id, age: s.duration + 0.1, duration: s.duration, spread: 100).isEmpty, "\(id) no motes after end")
        }
        checkStagecraft(&samples)
        if failures > 0 { fputs("\(failures) failures\n", stderr); exit(1) }
        print("battle ambient light regression passed (\(samples) mote samples)")
    }
}
