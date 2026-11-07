import Foundation

// Checks the floating battle numbers (Sources/Game/MeadowBattleNumber.swift): size, spring, rise and fade. No UIKit, app, simulator or device.
typealias N = MeadowBattleNumber

@main
struct NumberRegression {
    static var failures = 0
    static func check(_ ok: Bool, _ message: @autoclosure () -> String) { if !ok { failures += 1; fputs("FAIL: \(message())\n", stderr) } }

    static func main() {
        let kinds: [N.Kind] = [.damage, .block, .heal, .shield, .buff, .crit]
        // Bigger than the old 24pt labels, and heavier hits are bigger still.
        for k in kinds { for r in 0...2 { check(N.fontSize(kind: k, rank: r) >= 34, "\(k) rank \(r): too small (\(N.fontSize(kind: k, rank: r)))") } }
        check(N.fontSize(kind: .damage, rank: 0) < N.fontSize(kind: .damage, rank: 1) && N.fontSize(kind: .damage, rank: 1) < N.fontSize(kind: .damage, rank: 2), "damage size must grow with the tier")
        for k in kinds {
            for r in 0...2 {
                var t = -0.1, peakScale = 0.0, lastRise = -1.0
                var prevScale = N.scale(age: -0.1, kind: k, rank: r), maxStep = 0.0
                while t <= N.life + 0.2 {
                    let s = N.scale(age: t, kind: k, rank: r), a = N.alpha(age: t), rise = N.rise(age: t, kind: k)
                    check(s.isFinite && a.isFinite && rise.isFinite && s >= 0 && a >= 0 && a <= 1.0001, "\(k) t=\(t): bad values s=\(s) a=\(a)")
                    if t >= 0 { maxStep = max(maxStep, abs(s - prevScale)); check(rise >= lastRise - 1e-9, "\(k) rise must never go back down") }
                    peakScale = max(peakScale, s); prevScale = s
                    if t >= 0 { lastRise = rise }
                    if t >= 0.1 && t <= 1.15 { check(a > 0.99, "\(k) t=\(t): faded too early (\(a))") }
                    t += 1.0 / 120
                }
                // Springs past 1, settles on 1, never snaps (the biggest frame-to-frame step at 120 Hz stays small).
                check(peakScale > 1.05 && peakScale < 1.6, "\(k) rank \(r): overshoot \(peakScale)")
                check(abs(N.scale(age: 1.0, kind: k, rank: r) - 1) < 0.01, "\(k): scale does not settle (\(N.scale(age: 1.0, kind: k, rank: r)))")
                check(maxStep < 0.25, "\(k) rank \(r): scale jumps by \(maxStep) in one 120 Hz step")
                // Born invisible, fully visible while it matters, gone at the end of its life.
                check(N.alpha(age: -0.01) == 0 && N.scale(age: -0.01, kind: k, rank: r) == 0, "\(k): visible before it is born")
                check(N.alpha(age: 0.5) > 0.99 && N.alpha(age: 1.0) > 0.99, "\(k): fades too early")
                check(N.alpha(age: N.life) == 0 && N.alpha(age: N.life + 0.5) == 0, "\(k): still visible after its life")
                check(N.rise(age: 0, kind: k) == 0 && N.rise(age: N.life, kind: k) > 40, "\(k): rise range")
            }
        }
        check(N.life >= 1.6, "numbers must be readable for a while")
        // Support numbers stack without touching each other.
        for k in [N.Kind.heal, .shield, .buff] { check(N.lineHeight(kind: k, rank: 1) >= N.fontSize(kind: k, rank: 1), "\(k): stacked lines overlap") }
        // Sway dies out and stays small.
        for seed in 0..<40 { check(abs(N.sway(age: 2.0, seed: seed)) < 12, "sway seed \(seed) too large") }
        if failures > 0 { fputs("\(failures) failures\n", stderr); exit(1) }
        print("battle numbers: sizes, spring, rise and fade are in range")
    }
}
