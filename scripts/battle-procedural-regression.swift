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
            check(M.camera(skill: id, t: -0.1, direction: 1) == .zero && M.camera(skill: id, t: info.duration + 0.5, direction: 1) == .zero, "\(id) camera outside the effect")
            check(M.primitives(skill: id, t: info.duration + 1.5, geo: geo).count < 400, "\(id) draws too much after the end")
        }
        // The camera answers the release: a heavy skill kicks harder than a heal.
        func peak(_ id: String) -> Double {
            var m = 0.0, t = 0.0
            while t < 2.4 { let c = M.camera(skill: id, t: t, direction: 1); m = max(m, abs(c.dx) + abs(c.dy) + 200 * abs(c.zoom)); t += 1.0 / 60 }
            return m
        }
        check(peak("dragonFlame") > peak("healMicro") * 4, "dragon flame should kick harder than a micro heal")
        check(peak("dragonScaleWard") > 0.5 && peak("runeSlash") > 0.5 && peak("dragonOrder") > 0.5, "weighty skills must move the lens")
        if failures > 0 { fputs("\(failures) failures\n", stderr); exit(1) }
        print("battle procedural skills match the Python reference (\(samples) samples)")
    }
}
