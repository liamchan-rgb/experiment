import Foundation

// Checks the party battle formations (Sources/Game/MeadowBattleFormation.swift): every team size from 1 to 7 heroes against 0 to 3
// monsters or another hero team (PvP, mirrored). No UIKit, app, simulator or device.
typealias F = MeadowBattleFormation

@main
struct FormationRegression {
    static var failures = 0
    static func check(_ ok: Bool, _ message: @autoclosure () -> String) { if !ok { failures += 1; fputs("FAIL: \(message())\n", stderr) } }

    static func main() {
        // The classic battle (2 heroes, up to 3 monsters) keeps zoom 1 and exactly its old feet (PartyVisual.classicFeet).
        let classic: [String: (Double, Double)] = ["p1": (165, 420), "p2": (315, 505), "m1": (650, 395), "m2": (835, 510), "m3": (600, 585)]
        for foes in 1...3 {
            let l = F.layout(players: ["p1", "p2"], foes: Array(["m1", "m2", "m3"].prefix(foes)), pvp: false)
            check(l.zoom == 1 && l.mirrored.isEmpty, "2v\(foes): zoom \(l.zoom)")
            for (id, p) in l.feet { check(classic[id].map { $0.0 == p.x && $0.1 == p.y } ?? false, "2v\(foes): \(id) moved to \(p)") }
        }
        var cases = 0
        for pvp in [false, true] {
            for n in 1...F.maxHeroes {
                for k in (pvp ? 1...F.maxHeroes : 0...F.maxMonsters) {
                    cases += 1
                    let players = (1...n).map { "p\($0)" }, foes = k == 0 ? [] : (1...k).map { pvp ? "q\($0)" : "m\($0)" }
                    let l = F.layout(players: players, foes: foes, pvp: pvp), name = "\(pvp ? "PvP " : "")\(n)v\(k)"
                    check(l.feet.count == n + k, "\(name): \(l.feet.count) units placed")
                    check([1.0, 1.25, 1.45].contains(l.zoom), "\(name): zoom \(l.zoom)")
                    check(pvp ? l.mirrored == Set(foes) : l.mirrored.isEmpty, "\(name): mirrored \(l.mirrored)")
                    // On the plates, inside the world, and in view at rest even on a wide pane (aspect 1.6): feet clear of the bottom, heads of the top.
                    let view = F.visibleY(zoom: l.zoom, aspect: 1.6)
                    for (id, p) in l.feet {
                        check(p.x >= 120 && p.x <= l.width - 120, "\(name): \(id) x \(p.x) off the field (width \(l.width))")
                        check(p.y + 20 <= view.upperBound && p.y - 230 >= view.lowerBound, "\(name): \(id) y \(p.y) out of view \(view)")
                        check(p.y - 159 * l.zoom > 0 && p.y < 758 * l.zoom - 40, "\(name): \(id) off the plates")
                    }
                    // No two units on top of each other; the teams keep a clear no-man's-land.
                    let ids = Array(l.feet.keys)
                    for i in 0..<ids.count { for j in (i + 1)..<ids.count {
                        let a = l.feet[ids[i]]!, b = l.feet[ids[j]]!, monsterPair = ids[i].hasPrefix("m") || ids[j].hasPrefix("m")
                        let d = ((a.x - b.x) * (a.x - b.x) + (a.y - b.y) * (a.y - b.y)).squareRoot()
                        check(d >= (monsterPair ? 140 : 100), "\(name): \(ids[i]) and \(ids[j]) only \(Int(d)) apart")
                    } }
                    let left = players.compactMap { l.feet[$0]?.x }.max() ?? 0, right = foes.compactMap { l.feet[$0]?.x }.min() ?? l.width
                    check(right - left >= 200, "\(name): teams only \(Int(right - left)) apart")
                    if pvp {
                        for (i, id) in foes.enumerated() {
                            let a = l.feet[players.indices.contains(i) ? players[i] : players[0]]!, b = l.feet[id]!
                            if players.indices.contains(i) { check(abs(a.x + b.x - l.width) < 1e-9 && a.y == b.y, "\(name): \(id) is not the mirror of slot \(i + 1)") }
                        }
                    }
                }
            }
        }
        // More units than slots: the extras are left out, nothing crashes.
        let over = F.layout(players: (1...9).map { "p\($0)" }, foes: (1...5).map { "m\($0)" }, pvp: false)
        check(over.feet.count == 10 && over.zoom == 1.45, "overflow: \(over.feet.count) placed at zoom \(over.zoom)")
        if failures > 0 { print("battle formation regression: \(failures) failure(s)"); exit(1) }
        print("battle formation regression: \(cases) team sizes passed")
    }
}
