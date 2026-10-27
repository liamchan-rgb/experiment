import XCTest
import ClassroomGameCore
@testable import MeadowBattleSupport
final class BowTests:XCTestCase {
    func testBowInventoryTransferAndRealD8SingleAtomicHit() throws {
        let gear=try TrainingLoadout();try gear.equip("huntingBow")
        XCTAssertEqual(gear.units["p1"]?.inventory["trainingSword"],1);XCTAssertNil(gear.units["p1"]?.inventory["huntingBow"])
        let party=try PartyEncounter(seed:47,loadouts:gear.units);try party.engine.apply(.endTurn(actor:"p2",timedOut:false))
        let before=party.state,intent=try XCTUnwrap(party.prepare(.attack,target:"m1"))
        XCTAssertTrue(intent.ranged);XCTAssertEqual(before,party.state)
        let die=try XCTUnwrap(party.confirmedReceipt?.dice.first);XCTAssertEqual(die.formula.sides,8)
        for age in stride(from:0.0,through:1.7,by:0.01) { let p=PartyVisual.travel(intent,age:age);XCTAssertEqual(p.x,0);XCTAssertEqual(p.y,0) }
        let result=try XCTUnwrap(party.commit(intent.id));XCTAssertNil(try party.commit(intent.id));XCTAssertEqual(before.units["m1"]!.health-result.after.units["m1"]!.health,die.total)
        try gear.equip("trainingSword");XCTAssertEqual(gear.units["p1"]?.inventory["huntingBow"],1);XCTAssertNil(gear.units["p1"]?.inventory["trainingSword"])
    }
    func testProjectileVisibleOnlyAfterReleaseAndArrivesAtAtomicHitPoint() {
        let from=PartyPoint(212.31,362.73),to=PartyVisual.hitPoint(target:"m1")
        XCTAssertNil(BowRig.projectile(age:0.859,from:from,to:to,impact:1.048))
        let first=BowRig.projectile(age:0.86,from:from,to:to,impact:1.048)!
        XCTAssertEqual(first.tip.x,from.x,accuracy:1e-9);XCTAssertEqual(first.tip.y,from.y,accuracy:1e-9)
        let last=BowRig.projectile(age:1.048-1e-9,from:from,to:to,impact:1.048)!
        XCTAssertEqual(last.tip.x,to.x,accuracy:0.00001);XCTAssertEqual(last.tip.y,to.y,accuracy:0.00001)
        XCTAssertNil(BowRig.projectile(age:1.048,from:from,to:to,impact:1.048))
    }
    func testBowSleevesHaveStableJointsThroughDrawReleaseAndReturn() {
        func position(_ p:BowPartPose)->PartyPoint { PartyPoint(p.pivot.x+p.offset.x,p.pivot.y+p.offset.y) }
        var last:[String:PartyPoint]=[:]
        for i in 0...600 {
            let s=BowRig.sample(clip:"attack",progress:Double(i)/600)
            for key in ["nearUpper","nearFore","nearHand","farUpper","farFore","farHand"] {
                let q=position(s.parts[key]!)
                if let old=last[key] { XCTAssertLessThan(hypot(q.x-old.x,q.y-old.y),1.0,"No sudden joint jumps") }
                last[key]=q
            }
            func dist(_ a:PartyPoint,_ b:PartyPoint)->Double { hypot(a.x-b.x,a.y-b.y) }
            let ns=position(s.parts["nearUpper"]!),ne=position(s.parts["nearFore"]!),nh=position(s.parts["nearHand"]!)
            XCTAssertEqual(dist(ns,ne),22,accuracy:1e-8);XCTAssertEqual(dist(ne,nh),34,accuracy:1e-8)
            XCTAssertEqual(Set(s.surfaces.map(\.group)),Set(["torso","farArm","nearArm","farHand","nearHand"]))
            for surface in s.surfaces { for p in surface.points {
                XCTAssertEqual(p.x,p.x.rounded());XCTAssertEqual(p.y,p.y.rounded())
                XCTAssertTrue((75...215).contains(p.x));XCTAssertTrue((75...215).contains(p.y))
            } }
        }
        let held=BowRig.sample(clip:"attack",progress:0.35)
        let nearElbow=position(held.parts["nearFore"]!),nearShoulder=position(held.parts["nearUpper"]!)
        XCTAssertLessThan(nearElbow.x,nearShoulder.x-12,"Foreground drawing elbow must point backward")
        XCTAssertTrue(held.arrowVisible);XCTAssertFalse(BowRig.sample(clip:"attack",progress:0.5).arrowVisible)
    }
    func testDrawingHandMeetsStringBeforeArrowAppearsAndBowSharesHoldingWrist() {
        func position(_ p:BowPartPose)->PartyPoint { PartyPoint(p.pivot.x+p.offset.x,p.pivot.y+p.offset.y) }
        for clip in ["idle","attack","guard","hit","victory","defeat"] {
            for i in 0...600 {
                let p=Double(i)/600,pose=BowRig.sample(clip:clip,progress:p)
                let grip=position(pose.parts["farHand"]!),bow=position(pose.parts["bow"]!)
                XCTAssertEqual(grip.x,bow.x,accuracy:1e-9);XCTAssertEqual(grip.y,bow.y,accuracy:1e-9)
                if pose.arrowVisible {
                    let hand=position(pose.parts["nearHand"]!)
                    XCTAssertEqual(hand.x,pose.stringHand.x,accuracy:1e-8)
                    XCTAssertEqual(hand.y,pose.stringHand.y,accuracy:1e-8)
                    XCTAssertEqual(pose.arrowTail.x,pose.stringHand.x,accuracy:1e-8)
                    XCTAssertEqual(pose.arrowTail.y,pose.stringHand.y,accuracy:1e-8)
                }
                if clip=="attack" && p<=0.21 { XCTAssertFalse(pose.arrowVisible) }
            }
        }
        let release=BowRig.sample(clip:"attack",progress:BowRig.releaseProgress)
        XCTAssertEqual(BowRig.releaseArrowTip.x,release.arrowTip.x,accuracy:1e-9)
        XCTAssertEqual(BowRig.releaseArrowTip.y,release.arrowTip.y,accuracy:1e-9)
        let after=BowRig.sample(clip:"attack",progress:BowRig.releaseProgress+0.07)
        XCTAssertLessThan(position(after.parts["nearHand"]!).x,position(release.parts["nearHand"]!).x)
        XCTAssertGreaterThan(after.stringHand.x,release.stringHand.x)
    }

}
