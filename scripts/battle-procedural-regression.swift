import Foundation

// Pure check: the Swift port of the procedural skills must reproduce the Python reference (scripts/battle-vfx/procfx.py)
// sample for sample (primitive counts, per-kind counts, the sum of every number, and the first primitives in full).
// Also checks the camera and the ambient light level. No UIKit, app, simulator or device.
@main
struct BattleProceduralRegression {
    typealias M = MeadowSkillProcedural
    static var failures = 0
    static func check(_ ok: @autoclosure () -> Bool, _ message: @autoclosure () -> String) {
        if !ok() { failures += 1; if failures <= 30 { fputs("FAIL: \(message())\n", stderr) } }
    }
    static func num(_ v: Any?) -> Double { (v as? NSNumber)?.doubleValue ?? .nan }
    static func pt(_ v: Any?) -> M.Pt { let a = v as! [Any]; return M.Pt(num(a[0]), num(a[1])) }

    static func flat(_ p: M.Prim) -> (kind: Int, values: [Double]) {
        switch p {
        case let .glow(x, y, rx, ry, c, a): return (0, [0, x, y, rx, ry, c.r, c.g, c.b, a])
        case let .ring(x, y, rx, ry, w, c, a, rot): return (1, [1, x, y, rx, ry, w, c.r, c.g, c.b, a, rot])
        case let .streak(x, y, rx, ry, ang, c, a): return (2, [2, x, y, rx, ry, ang, c.r, c.g, c.b, a])
        case let .arc(x, y, rx, ry, a0, a1, w, c, a): return (3, [3, x, y, rx, ry, a0, a1, w, c.r, c.g, c.b, a])
        case let .ribbon(pts, ws, c, a, add, soft):
            return (4, [4, Double(pts.count)] + pts.flatMap { [$0.x, $0.y] } + ws + [c.r, c.g, c.b, a, add ? 1 : 0, soft])
        case let .flash(c, a): return (5, [5, c.r, c.g, c.b, a])
        }
    }

    static func main() throws {
        let data = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
        let golden = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        let g = golden["geometry"] as! [String: Any]
        let targets = (g["targets"] as! [Any]).map { t -> M.Target in let a = t as! [Any]; return M.Target(chest: pt(a[0]), foot: pt(a[1])) }
        let geo = M.Geometry(caster: pt(g["caster"]), casterFoot: pt(g["casterFoot"]), targets: targets, ground: num(g["ground"]))
        var samples = 0
        let skills = golden["skills"] as! [String: Any]
        check(Set(skills.keys) == Set(M.skillIDs), "skill list \(skills.keys.sorted()) vs \(M.skillIDs.sorted())")
        for id in M.skillIDs {
            for s in skills[id] as! [[String: Any]] {
                let t = num(s["t"]); samples += 1
                let flats = M.primitives(skill: id, t: t, geo: geo).map(flat)
                check(flats.count == (s["count"] as! NSNumber).intValue, "\(id) t=\(t): \(flats.count) primitives, expected \(s["count"]!)")
                var kinds = [Int](repeating: 0, count: 6)
                for f in flats { kinds[f.kind] += 1 }
                check(kinds == (s["kinds"] as! [NSNumber]).map { $0.intValue }, "\(id) t=\(t): kinds \(kinds) expected \(s["kinds"]!)")
                let total = flats.reduce(0.0) { $0 + $1.values.reduce(0, +) }, expected = num(s["sum"])
                check(abs(total - expected) <= 1e-7 * max(1, abs(expected)), "\(id) t=\(t): sum \(total) expected \(expected)")
                for (i, head) in (s["head"] as! [[NSNumber]]).enumerated() where i < flats.count {
                    let want = head.map { $0.doubleValue }, got = flats[i].values
                    check(want.count == got.count && zip(want, got).allSatisfy { abs($0 - $1) <= 1e-6 * max(1, abs($0)) }, "\(id) t=\(t): primitive \(i) \(got) expected \(want)")
                }
            }
            // The effect is finite and well-formed at a dense sweep of times.
            guard let info = M.info[id] else { check(false, "\(id) missing from the table"); continue }
            var t = 0.0
            while t < info.duration + 0.2 {
                for p in M.primitives(skill: id, t: t, geo: geo) {
                    let f = flat(p).values
                    check(f.allSatisfy { $0.isFinite }, "\(id) t=\(t): non-finite value in \(p)")
                    if case let .ribbon(pts, ws, _, _, _, _) = p { check(pts.count == ws.count && pts.count >= 2, "\(id) t=\(t): ribbon with \(pts.count) points and \(ws.count) widths") }
                }
                let cam = M.camera(skill: id, t: t, direction: 1)
                check(abs(cam.dx) <= 24 && abs(cam.dy) <= 24 && abs(cam.zoom) <= 0.12 && abs(cam.rotation) <= 0.05, "\(id) t=\(t): camera out of range \(cam)")
                let lit = M.light(skill: id, t: t)
                check(lit >= 0 && lit <= 1, "\(id) t=\(t): light \(lit)")
                t += 1.0 / 30
            }
            // Every target gets the effect: something is drawn centred on each target's chest while the effect is at full strength.
            func centres(_ p: M.Prim) -> [Double] {
                switch p {
                case let .glow(x, _, _, _, _, _), let .ring(x, _, _, _, _, _, _, _), let .streak(x, _, _, _, _, _, _), let .arc(x, _, _, _, _, _, _, _, _): return [x]
                case let .ribbon(pts, _, _, _, _, _): return pts.map { $0.x }
                case .flash: return []
                }
            }
            for probe in [info.release + 0.45, info.release + 0.8] where !id.hasPrefix("proj") {
                let prims = M.primitives(skill: id, t: probe, geo: geo)
                for (i, tg) in geo.targets.enumerated() {
                    check(prims.contains { centres($0).contains { abs($0 - tg.chest.x) < 45 } }, "\(id) t=\(probe): target \(i) at x=\(tg.chest.x) gets no effect")
                }
            }
            // Caster-side parts (charge-up, seal under the caster) are drawn once, not once per target.
            if ["starlightPulse", "runeSlash", "dragonFlame", "dragonOrder"].contains(id) {
                let one = M.Geometry(caster: geo.caster, casterFoot: geo.casterFoot, targets: [geo.targets[0]], ground: geo.ground)
                let before = info.release * 0.5, withTwo = M.primitives(skill: id, t: before, geo: geo).count, withOne = M.primitives(skill: id, t: before, geo: one).count
                check(withOne > 0 && withTwo < 2 * withOne, "\(id): the charge-up is duplicated per target (\(withTwo) vs \(withOne))")
            }
            check(M.camera(skill: id, t: -0.1, direction: 1) == .zero && M.camera(skill: id, t: info.duration + 0.5, direction: 1) == .zero, "\(id) camera outside the effect")
            check(M.primitives(skill: id, t: info.duration + 1.5, geo: geo).count < 400, "\(id) draws too much after the end")
        }
        // The camera answers the release: a heavy skill kicks harder than a heal.
        func peak(_ id: String) -> Double {
            var m = 0.0, t = 0.0
            while t < 2.4 { let c = M.camera(skill: id, t: t, direction: 1); m = max(m, abs(c.dx) + abs(c.dy) + 200 * abs(c.zoom)); t += 1.0 / 60 }
            return m
        }
        // The director shot: every combat skill pushes in on its caster, swings to the targets, and lets go again.
        for id in M.skillIDs where !id.hasPrefix("heal") && !M.isBlow(id) && id != "natural20" {
            guard let info = M.info[id] else { continue }
            var maxWeight = 0.0, maxZoom = 0.0, t = 0.0, firstFocus: Double? = nil, lastFocus = 0.0
            while t < info.duration {
                let s = M.shot(skill: id, t: t, geo: geo)
                check(s.weight >= 0 && s.weight <= 1.0001 && s.zoom >= -1e-9 && s.zoom <= 0.35 && s.focusX.isFinite && s.focusY.isFinite, "\(id) t=\(t): shot out of range \(s)")
                if firstFocus == nil, s.weight > 0.05 { firstFocus = s.focusX }
                if s.weight > 0.05 { lastFocus = s.focusX }
                maxWeight = max(maxWeight, s.weight); maxZoom = max(maxZoom, s.zoom); t += 1.0 / 60
            }
            check(maxWeight > 0.95 && maxZoom > 0.25, "\(id): the close-up never happens (weight \(maxWeight), zoom \(maxZoom))")
            check(M.shot(skill: id, t: -0.1, geo: geo) == .idle && M.shot(skill: id, t: info.duration + 0.2, geo: geo) == .idle, "\(id) shot outside the effect")
            // Starts on the caster, ends nearer the targets.
            let caster = geo.caster.x, tx = geo.targets.map { $0.chest.x }.reduce(0, +) / Double(geo.targets.count)
            if abs(tx - caster) > 60 { check(abs((firstFocus ?? 0) - caster) < abs((firstFocus ?? 0) - tx) && abs(lastFocus - tx) < abs(lastFocus - caster), "\(id): the shot does not travel from caster to targets") }
            // Damage scaling only touches the part after the release.
            let before = info.release * 0.5, after = info.release + 0.3
            check(M.scaled(M.camera(skill: id, t: before, direction: 1), skill: id, t: before, power: 1.45) == M.camera(skill: id, t: before, direction: 1), "\(id): damage power must not change the build-up")
            let c1 = M.camera(skill: id, t: after, direction: 1), c2 = M.scaled(c1, skill: id, t: after, power: 1.45), c3 = M.scaled(c1, skill: id, t: after, power: 0.7)
            check(abs(c2.dx) + abs(c2.dy) + 200 * abs(c2.zoom) >= abs(c3.dx) + abs(c3.dy) + 200 * abs(c3.zoom) - 1e-9, "\(id): heavier hits should shake at least as hard")
        }
        // The natural 20 pushes straight in on the target and holds; plain blows have no director shot and no lens work of their own.
        var n20w = 0.0, n20z = 0.0, t20 = 0.0
        while t20 < 2.8 { let s = M.shot(skill: "natural20", t: t20, geo: geo); n20w = max(n20w, s.weight); n20z = max(n20z, s.zoom); t20 += 1.0 / 60 }
        check(n20w > 0.95 && n20z > 0.3, "natural20: the push-in is too weak (\(n20w), \(n20z))")
        for id in M.skillIDs where M.isBlow(id) { check(M.shot(skill: id, t: 0.3, geo: geo) == .idle && M.camera(skill: id, t: 0.3, direction: 1) == .zero, "\(id) must not move the lens") }
        for id in ["healMicro", "healStandard", "healStrong"] { check(M.shot(skill: id, t: 0.3, geo: geo) == .idle, "\(id) must not move the lens") }
        check(peak("dragonFlame") > peak("healMicro") * 4, "dragon flame should kick harder than a micro heal")
        check(peak("dragonScaleWard") > 0.5 && peak("runeSlash") > 0.5 && peak("dragonOrder") > 0.5, "weighty skills must move the lens")
        if failures > 0 { fputs("\(failures) failures\n", stderr); exit(1) }
        print("battle procedural skills match the Python reference (\(samples) samples)")
    }
}
