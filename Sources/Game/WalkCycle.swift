import Foundation

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
        1 + Int(max(0, distance) / 24 * CGFloat(HeroFrames.walkFrameCount)) % HeroFrames.walkFrameCount
    }

    /// Map art uses an elevated camera: depth travel projects shorter than
    /// profile travel. Apply the same metric to simulation, gait and review.
    static func projectedScale(dx: CGFloat, dy: CGFloat) -> CGFloat {
        let screen = hypot(dx, dy)
        return screen > 0.0001 ? screen / hypot(dx, dy * 2) : 1
    }
}
