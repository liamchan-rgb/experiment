import Foundation

// Pure check of MeadowSkillAmbientLight: envelope, determinism, bounds and frame-to-frame continuity of the motes.
@main
struct BattleAmbientRegression {
    static var failures = 0
    static func check(_ ok: @autoclosure () -> Bool, _ message: @autoclosure () -> String) {
        if !ok() { failures += 1; if failures <= 25 { fputs("FAIL: \(message())\n", stderr) } }
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
        if failures > 0 { fputs("\(failures) failures\n", stderr); exit(1) }
        print("battle ambient light regression passed (\(samples) mote samples)")
    }
}
