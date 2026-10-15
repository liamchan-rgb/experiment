import Foundation

/// Distance, rather than the atmospheric clock, drives planted-foot cadence.
struct WalkCycle {
    private(set) var distance: CGFloat = 0
    private(set) var facing = 0
    private(set) var moving = false
    private(set) var frame = 0
    var phase: CGFloat { distance.truncatingRemainder(dividingBy: 24) / 24 }
    var lift: CGFloat { moving ? abs(sin(phase * 2 * .pi)) * 1.35 : 0 }

    mutating func advance(from old: CGPoint, to new: CGPoint) {
        let dx = new.x - old.x, dy = new.y - old.y
        let movement = hypot(dx, dy)
        moving = movement > 0.001
        guard moving else { frame = 0; return }
        distance += movement
        let currentlyVertical = facing == 0 || facing == 2
        let directionDeadband: CGFloat = 1.08
        if currentlyVertical {
            if abs(dx) > abs(dy) * directionDeadband { facing = dx < 0 ? 1 : 3 }
        } else if abs(dy) > abs(dx) * directionDeadband {
            facing = dy < 0 ? 2 : 0
        }
        frame = Self.frame(at: distance)
    }

    static func frame(at distance: CGFloat) -> Int {
        [1, 2, 3, 2][Int(max(0, distance) / 24 * 4) % 4]
    }
}
