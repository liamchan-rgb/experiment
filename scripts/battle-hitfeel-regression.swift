import Foundation

// Pure check: the Swift hit-feel port must reproduce the Python reference (scripts/battle-hitfeel/hitfeel.py)
// sample for sample. No UIKit, app, simulator or device.
@main
struct BattleHitFeelRegression {
    static var failures = 0
    static func check(_ ok: @autoclosure () -> Bool, _ message: @autoclosure () -> String) {
        if !ok() { failures += 1; if failures <= 25 { fputs("FAIL: \(message())\n", stderr) } }
    }
    static func near(_ a: Double, _ b: Double) -> Bool { abs(a - b) <= 1e-9 * max(1, abs(b)) }
    static func numbers(_ value: Any?) -> [Double]? { (value as? [Any])?.compactMap { ($0 as? NSNumber)?.doubleValue } }

    static func main() throws {
        let data = try Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1]))
        let golden = try JSONSerialization.jsonObject(with: data) as! [String: Any]
        var samples = 0

        for entry in golden["classify"] as! [[String: Any]] {
            let damage = (entry["damage"] as! NSNumber).intValue, killed = (entry["killed"] as! NSNumber).boolValue
            let expected = entry["tier"] as! String
            check(MeadowBattleHitTier.classify(damage: damage, killed: killed).name == expected, "classify \(damage) \(killed)")
        }
        let tiers = golden["tiers"] as! [String: Any]
        for tier in MeadowBattleHitTier.allCases {
            let block = tiers[tier.name] as! [String: Any]
            let constants = block["constants"] as! [String: Any]
            check(near(tier.intensity, (constants["intensity"] as! NSNumber).doubleValue), "\(tier.name) intensity")
            check(near(tier.flareRadius, (constants["flareRadius"] as! NSNumber).doubleValue), "\(tier.name) flareRadius")
            check(tier.sparkCount == (constants["sparkCount"] as! NSNumber).intValue, "\(tier.name) sparkCount")
            check(tier.leafCount == (constants["leafCount"] as! NSNumber).intValue, "\(tier.name) leafCount")
            let haptic = block["haptic"] as! [Any]
            let h = MeadowBattleHitFeel.haptic(tier: tier)
            check(h.style.rawValue == (haptic[0] as! String) && near(h.intensity, (haptic[1] as! NSNumber).doubleValue), "\(tier.name) haptic")

            for row in block["rows"] as! [[String: Any]] {
                let age = (row["age"] as! NSNumber).doubleValue
                let label = "\(tier.name)@\(age)"
                for direction in [1.0, -1.0] {
                    let key = direction > 0 ? "1" : "-1"
                    let c = MeadowBattleHitFeel.camera(age: age, tier: tier, direction: direction)
                    let ec = numbers((row["camera"] as! [String: Any])[key])!
                    check(near(c.dx, ec[0]) && near(c.dy, ec[1]) && near(c.zoom, ec[2]) && near(c.rotation, ec[3]), "camera \(label) \(key)")
                    let sparks = MeadowBattleHitFeel.sparks(age: age, tier: tier, direction: direction)
                    let es = (row["sparks"] as! [String: Any])[key] as! [[Double]]
                    check(sparks.count == es.count, "spark count \(label) \(key): \(sparks.count) vs \(es.count)")
                    for (s, e) in zip(sparks, es) {
                        check(near(s.headX, e[0]) && near(s.headY, e[1]) && near(s.tailX, e[2]) && near(s.tailY, e[3])
                              && near(s.width, e[4]) && near(s.alpha, e[5]) && near(s.heat, e[6]), "spark \(label) \(key)")
                    }
                    let leaves = MeadowBattleHitFeel.leaves(age: age, tier: tier, direction: direction)
                    let el = (row["leaves"] as! [String: Any])[key] as! [[Double]]
                    check(leaves.count == el.count, "leaf count \(label) \(key)")
                    for (l, e) in zip(leaves, el) {
                        check(near(l.x, e[0]) && near(l.y, e[1]) && near(l.rotation, e[2]) && near(l.size, e[3])
                              && near(l.alpha, e[4]) && l.tone == Int(e[5]), "leaf \(label) \(key)")
                    }
                    samples += 1
                }
                check(near(MeadowBattleHitFeel.knockback(age: age, tier: tier), (row["knockback"] as! NSNumber).doubleValue), "knockback \(label)")
                check(near(MeadowBattleHitFeel.knockback(age: age, tier: tier, canvasWidth: 1000), (row["knockback1000"] as! NSNumber).doubleValue), "knockback1000 \(label)")
                let q = MeadowBattleHitFeel.squash(age: age, tier: tier), eq = numbers(row["squash"])!
                check(near(q.x, eq[0]) && near(q.y, eq[1]), "squash \(label)")
                check(near(MeadowBattleHitFeel.flash(age: age), (row["flash"] as! NSNumber).doubleValue), "flash \(label)")
                if let e = numbers(row["flare"]) {
                    let f = MeadowBattleHitFeel.flare(age: age, tier: tier)
                    check(f != nil && near(f!.radius, e[0]) && near(f!.alpha, e[1]), "flare \(label)")
                } else { check(MeadowBattleHitFeel.flare(age: age, tier: tier) == nil, "flare nil \(label)") }
                if let e = numbers(row["ring"]) {
                    let r = MeadowBattleHitFeel.ring(age: age, tier: tier)
                    check(r != nil && near(r!.radius, e[0]) && near(r!.width, e[1]) && near(r!.alpha, e[2]), "ring \(label)")
                } else { check(MeadowBattleHitFeel.ring(age: age, tier: tier) == nil, "ring nil \(label)") }
                let dust = MeadowBattleHitFeel.dust(age: age, tier: tier), ed = row["dust"] as! [[Double]]
                check(dust.count == ed.count, "dust count \(label)")
                for (d, e) in zip(dust, ed) { check(near(d.dx, e[0]) && near(d.rx, e[1]) && near(d.ry, e[2]) && near(d.alpha, e[3]), "dust \(label)") }
                if let e = numbers(row["number"]) {
                    let n = MeadowBattleHitFeel.number(age: age, tier: tier)
                    check(n != nil && near(n!.scale, e[0]) && near(n!.yOffset, e[1]) && near(n!.alpha, e[2]) && near(n!.fontSize, e[3]), "number \(label)")
                } else { check(MeadowBattleHitFeel.number(age: age, tier: tier) == nil, "number nil \(label)") }
                samples += 1
            }
        }

        // Behavioural guarantees the presentation depends on.
        for tier in MeadowBattleHitTier.allCases {
            check(MeadowBattleHitFeel.camera(age: 0.099, tier: tier).dx == 0, "camera frozen during the stop (\(tier.name))")
            check(MeadowBattleHitFeel.knockback(age: 0.099, tier: tier) == 0, "monster frozen during the stop (\(tier.name))")
            check(MeadowBattleHitFeel.knockback(age: 0.6, tier: tier) < MeadowBattleHitFeel.knockback(age: 0.16, tier: tier), "knockback settles back (\(tier.name))")
            check(MeadowBattleHitFeel.knockback(age: 0.16, tier: tier) > 0, "knockback pushes away (\(tier.name))")
            check(MeadowBattleHitFeel.flash(age: 0.2) == 0 && MeadowBattleHitFeel.flash(age: 0.01) == 1, "flash envelope (\(tier.name))")
        }
        check(MeadowBattleHitFeel.knockback(age: 0.2, tier: .heavy) > MeadowBattleHitFeel.knockback(age: 0.2, tier: .light), "heavy pushes further than light")
        check(MeadowBattleHitFeel.sparks(age: 0.02, tier: .heavy).count > MeadowBattleHitFeel.sparks(age: 0.02, tier: .light).count, "heavy throws more sparks")
        check(MeadowBattleHitFeel.camera(age: 0.0, tier: .medium) == .zero, "camera starts at rest")
        check(MeadowBattleHitFeel.sparks(age: 1, tier: .heavy).isEmpty && MeadowBattleHitFeel.flare(age: 1, tier: .heavy) == nil, "all graphics end")

        if failures > 0 { fputs("FAILED: \(failures) mismatches\n", stderr); exit(1) }
        print("PASS: hit-feel Swift port matches the reference on \(samples) samples across 3 tiers")
    }
}
