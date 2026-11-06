import Foundation
#if canImport(CoreGraphics)
import CoreGraphics
#endif

/// Distance, rather than the atmospheric clock, drives planted-foot cadence.
struct WalkCycle {
    private(set) var distance: CGFloat = 0
    private(set) var facing = 0
    private(set) var moving = false
    private(set) var frame = 0
    var phase: CGFloat { distance.truncatingRemainder(dividingBy: 24) / 24 }
    // The authored contact and passing frames already contain their leg lift.
    // Adding a whole-body bob raises every contact sole off the trail.
    var lift: CGFloat { 0 }

    // Clockwise from screen-down. Art rows retain the original cardinal order.
    private static let rows = [0, 4, 3, 7, 2, 6, 1, 5]
    private var heading: CGFloat?

    mutating func advance(from old: CGPoint, to new: CGPoint) {
        let dx = new.x - old.x, dy = new.y - old.y
        let movement = hypot(dx, dy)
        moving = movement > 0.001
        guard moving else {
            // Idle is pose 0. Clear the distance phase too, so resuming from
            // idle begins at the first walk pose instead of jumping back into
            // the stale mid-cycle pose from before the pause.
            distance = 0
            frame = 0
            return
        }
        distance += movement / Self.projectedScale(dx: dx, dy: dy)
        let angle = atan2(dx, dy)
        let sector = .pi / CGFloat(4)
        let difference = heading.map { atan2(sin(angle - $0), cos(angle - $0)) }
        // Five degrees of hysteresis prevent artwork flickering on curved roads.
        if difference == nil || abs(difference!) > sector / 2 + .pi / 36 {
            let index = (Int((angle / sector).rounded()) + 8) % 8
            facing = Self.rows[index]
            heading = CGFloat(index) * sector
        }
        frame = Self.frame(at: distance)
    }

    static func frame(at distance: CGFloat) -> Int {
        // Projected diagonal travel can land a few ulps below an exact tick.
        1 + Int(floor(max(0, distance) / 24 * CGFloat(HeroFrames.walkFrameCount) + 0.000000001)) % HeroFrames.walkFrameCount
    }

    /// Map art uses an elevated camera: depth travel projects shorter than
    /// profile travel. Apply the same metric to simulation, gait and review.
    static func projectedScale(dx: CGFloat, dy: CGFloat) -> CGFloat {
        let screen = hypot(dx, dy)
        return screen > 0.0001 ? screen / hypot(dx, dy * 2) : 1
    }
}

/// Distance windows for the eight authored walk poses, per facing. Uniform is
/// 3 units per pose (24 per cycle). Foot-locked windows give each pose the
/// distance its planted sole actually travels in the art, so the foot stays
/// put instead of stalling and then sliding. The cycle stays 24 units and the
/// frame space stays the shared 24-tick clock, so shadows and rigs agree.
struct GaitTiming: Equatable {
    static let poseCount = 8
    static let cycle: CGFloat = 24
    /// [facing][pose] distance; every row sums to `cycle`.
    let windows: [[CGFloat]]

    static let uniform = GaitTiming(windows: Array(repeating: Array(repeating: cycle / CGFloat(poseCount), count: poseCount), count: 8))

    /// Screen travel per facing row (art rows: down, left, up, right, then
    /// down-right, down-left, up-left, up-right). +y is screen-down.
    static let travel: [CGPoint] = [CGPoint(x: 0, y: 1), CGPoint(x: -1, y: 0), CGPoint(x: 0, y: -1), CGPoint(x: 1, y: 0),
                                    CGPoint(x: 1, y: 1), CGPoint(x: -1, y: 1), CGPoint(x: -1, y: -1), CGPoint(x: 1, y: -1)]

    /// - Parameters:
    ///   - soles: [facing][pose] two sole points in world points (sprite space).
    ///   - minimumStride: below this planted travel per cycle the art cannot
    ///     be foot-locked by timing alone; keep that facing uniform.
    ///   - strength: 0 = uniform, 1 = fully foot-locked.
    static func footLocked(soles: [[[CGPoint]]], minimumStride: CGFloat = 12, strength: CGFloat = 0.6) -> GaitTiming {
        precondition(soles.count == 8 && soles.allSatisfy { poses in poses.count == poseCount && poses.allSatisfy { pair in pair.count == 2 } })
        let rows = (0..<8).map { facing -> [CGFloat] in
            let v = travel[facing], length = hypot(v.x, v.y)
            let unit = CGPoint(x: v.x / length, y: v.y / length)
            let metric = hypot(unit.x, unit.y * 2)   // WalkCycle.projectedScale's inverse
            let planted = (0..<poseCount).map { pose -> CGFloat in
                let a = soles[facing][pose], b = soles[facing][(pose + 1) % poseCount]
                // The planted sole moves backward relative to the body.
                let back = (0..<2).map { -((b[$0].x - a[$0].x) * unit.x + (b[$0].y - a[$0].y) * unit.y) }
                return max(0, back.max()!) * metric
            }
            let total = planted.reduce(0, +)
            guard total >= minimumStride else { return Array(repeating: cycle / CGFloat(poseCount), count: poseCount) }
            let average = total / CGFloat(poseCount)
            let clamped = planted.map { min(max($0, average * 0.45), average * 1.8) }
            let scaled = clamped.map { $0 * cycle / clamped.reduce(0, +) }
            let blended = scaled.map { cycle / CGFloat(poseCount) + ($0 - cycle / CGFloat(poseCount)) * strength }
            let sum = blended.reduce(0, +)
            return blended.map { $0 * cycle / sum }
        }
        return GaitTiming(windows: rows)
    }

    /// P1 sole points per facing and walk pose, in sprite world points, from
    /// hero-gait.json `heroes[0]` (the same data the shadow caster reads).
    /// Pose p is sampled at tick 1 + 3p of the shared 24-tick clock.
    static func p1Soles(rigJSON data: Data, spriteSize: CGFloat = 64) -> [[[CGPoint]]]? {
        guard let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let heroes = object["heroes"] as? [Any], let p1 = heroes.first as? [Any], p1.count == 8 else { return nil }
        var result: [[[CGPoint]]] = []
        for direction in p1 {
            guard let ticks = direction as? [[String: Any]], ticks.count >= 1 + 3 * poseCount else { return nil }
            var poses: [[CGPoint]] = []
            for pose in 0..<poseCount {
                guard let feet = ticks[1 + 3 * pose]["feet"] as? [[Double]], feet.count == 2,
                      feet.allSatisfy({ $0.count >= 2 }) else { return nil }
                poses.append(feet.map { CGPoint(x: CGFloat($0[0]) * spriteSize, y: CGFloat($0[1]) * spriteSize) })
            }
            result.append(poses)
        }
        return result
    }

    /// Cycle distance at which `pose` (0...8, 8 = full cycle) begins.
    func poseStart(facing: Int, pose: Int) -> CGFloat {
        windows[facing].prefix(max(0, min(Self.poseCount, pose))).reduce(0, +)
    }

    /// Same 1...24 frame space as `WalkCycle.frame(at:)`: pose p covers ticks
    /// 3p+1...3p+3, subdivided by progress through its window.
    func frame(at distance: CGFloat, facing: Int) -> Int {
        let row = windows[facing]
        // Uniform rows keep the exact original sampling, ulp handling included.
        if row.allSatisfy({ $0 == Self.cycle / CGFloat(Self.poseCount) }) { return WalkCycle.frame(at: distance) }
        var local = max(0, distance).truncatingRemainder(dividingBy: Self.cycle) + 0.000000001
        for pose in 0..<Self.poseCount {
            if local < row[pose] || pose == Self.poseCount - 1 {
                let ticks = HeroFrames.walkFrameCount / Self.poseCount
                let sub = min(ticks - 1, Int(floor(min(1, local / max(row[pose], 0.000001)) * CGFloat(ticks))))
                return 1 + pose * ticks + sub
            }
            local -= row[pose]
        }
        return 1
    }
}

/// Plays only authored entry/exit paths. Travel still owns the walk phase.
/// On arrival, finish the current cycle at its designated exit before stop art.
struct AuthoredLocomotion {
    struct Plan: Decodable {
        struct Direction: Decodable { let entryPhase: Int; let exitPhase: Int }
        let walkPhaseCount: Int
        let frameMs: Double
        let finishSpeed: CGFloat
        let startFrames: [Int]
        let stopFrames: [Int]
        let directions: [Direction]
    }
    enum State: String { case idle, starting, walking, settling, stopping }
    let plan: Plan?
    /// Per-facing pose windows; uniform unless the caller supplies foot-locked timing.
    let timing: GaitTiming
    private(set) var state = State.idle
    private(set) var frame = 0
    private(set) var facing = 0
    private(set) var distance: CGFloat = 0
    private var heading = WalkCycle()
    private var elapsed: TimeInterval = 0
    private var remaining: CGFloat = 0
    var phase: CGFloat { distance.truncatingRemainder(dividingBy: 24) / 24 }

    init(plan: Plan?, timing: GaitTiming = .uniform) {
        if let plan {
            precondition(plan.walkPhaseCount == 8 && plan.frameMs > 0 && plan.finishSpeed > 0)
            precondition(plan.startFrames.count == 2 && plan.stopFrames.count == 2 && plan.directions.count == 8)
            precondition(plan.directions.allSatisfy { (0..<8).contains($0.entryPhase) && (0..<8).contains($0.exitPhase) })
        }
        self.plan = plan
        self.timing = timing
    }

    func allowsTravel(requested: Bool) -> Bool {
        plan == nil || state == .idle || state == .walking || (state == .settling && requested)
    }

    mutating func reset() { self = AuthoredLocomotion(plan: plan, timing: timing) }

    mutating func advance(from old: CGPoint, to new: CGPoint, seconds: TimeInterval,
                          requested: Bool, headingHint: CGPoint = .zero) {
        let dx = new.x - old.x, dy = new.y - old.y, movement = hypot(dx, dy)
        if movement > 0.001 { heading.advance(from: old, to: new) }
        else if requested && hypot(headingHint.x, headingHint.y) > 0.001 {
            heading.advance(from: .zero, to: headingHint)
        }
        guard let plan else {
            if movement <= 0.001 { heading.advance(from: old, to: new) }
            facing = heading.facing; frame = heading.frame; distance = heading.distance
            state = heading.moving ? .walking : .idle
            return
        }
        let dt = max(0, seconds), duration = plan.frameMs / 1000
        switch state {
        case .idle:
            guard requested else { return }
            facing = heading.facing; state = .starting; elapsed = 0
            frame = plan.startFrames[0]
        case .starting:
            elapsed += dt
            if elapsed + 0.000000001 < duration * 2 {
                frame = plan.startFrames[min(1, Int((elapsed + 0.000000001) / duration))]
            } else {
                // The first walk pose is this direction's ORIGINAL walk01.
                // Do not substitute global phase0 after cyclic normalization.
                distance = timing.poseStart(facing: facing, pose: plan.directions[facing].entryPhase)
                frame = timing.frame(at: distance, facing: facing); state = .walking
            }
        case .walking:
            distance += movement / WalkCycle.projectedScale(dx: dx, dy: dy)
            if requested {
                facing = heading.facing
                frame = timing.frame(at: distance, facing: facing)
            } else {
                let exitEnd = timing.poseStart(facing: facing, pose: plan.directions[facing].exitPhase + 1)
                remaining = (exitEnd - distance.truncatingRemainder(dividingBy: 24) + 24)
                    .truncatingRemainder(dividingBy: 24)
                // At an exit boundary the visible pose is already the next
                // phase; finish one cycle rather than teleporting backwards.
                if remaining < 0.000001 { remaining = 24 }
                state = .settling
            }
        case .settling:
            if requested {
                state = .walking; facing = heading.facing
                distance += movement / WalkCycle.projectedScale(dx: dx, dy: dy)
                frame = timing.frame(at: distance, facing: facing)
            } else {
                let step = plan.finishSpeed * CGFloat(dt)
                if step + 0.000001 < remaining {
                    distance += step; remaining -= step; frame = timing.frame(at: distance, facing: facing)
                } else {
                    // Exit pose has had its full interval; stop01 follows it.
                    distance += remaining; elapsed = Double(max(0, step - remaining) / plan.finishSpeed)
                    state = .stopping; frame = plan.stopFrames[min(1, Int(elapsed / duration))]
                }
            }
        case .stopping:
            elapsed += dt
            if elapsed + 0.000000001 < duration * 2 { frame = plan.stopFrames[min(1, Int((elapsed + 0.000000001) / duration))] }
            else { state = .idle; distance = 0; frame = 0; elapsed = 0 }
        }
    }
}
