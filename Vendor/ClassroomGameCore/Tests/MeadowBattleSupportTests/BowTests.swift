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
            XCTAssertEqual(dist(ns,ne),32,accuracy:1e-8);XCTAssertEqual(dist(ne,nh),44,accuracy:1e-8)
            let fs=position(s.parts["farUpper"]!),fe=position(s.parts["farFore"]!),fh=position(s.parts["farHand"]!)
            XCTAssertEqual(dist(fs,fe),25,accuracy:1e-8);XCTAssertEqual(dist(fe,fh),25,accuracy:1e-8)
            XCTAssertEqual(Set(s.surfaces.map(\.group)),Set(["torso","farArm","nearArm","farHand","nearHand"]))
            for surface in s.surfaces { for p in surface.points {
                XCTAssertEqual(p.x,p.x.rounded());XCTAssertEqual(p.y,p.y.rounded())
                XCTAssertTrue((75...215).contains(p.x));XCTAssertTrue((75...215).contains(p.y))
            } }
        }
        let held=BowRig.sample(clip:"attack",progress:0.35)
        let nearElbow=position(held.parts["nearFore"]!),nearShoulder=position(held.parts["nearUpper"]!)
        XCTAssertLessThan(nearElbow.x,nearShoulder.x-25,"Foreground drawing elbow must point backward")
        let nearHand=position(held.parts["nearHand"]!),farShoulder=position(held.parts["farUpper"]!),farHand=position(held.parts["farHand"]!)
        XCTAssertGreaterThan(farHand.x-nearHand.x,40,"The far hand holds the bow ahead of the drawing hand")
        XCTAssertGreaterThan(farHand.y-nearHand.y,8,"The extended bow arm stays below the drawing hand")
        XCTAssertGreaterThan(hypot(farHand.x-farShoulder.x,farHand.y-farShoulder.y),48,"The held bow arm is almost straight")
        XCTAssertTrue(held.arrowVisible);XCTAssertFalse(BowRig.sample(clip:"attack",progress:0.5).arrowVisible)
    }
    func testReleasedDrawingHandReturnsDownWhileTheBowHandStaysPlanted() {
        func position(_ p:BowPartPose)->PartyPoint { PartyPoint(p.pivot.x+p.offset.x,p.pivot.y+p.offset.y) }
        let start=BowRig.releaseProgress,end=start+0.32/1.2
        let first=BowRig.sample(clip:"attack",progress:start)
        let initialHand=position(first.parts["nearHand"]!),initialGrip=position(first.parts["farHand"]!)
        var previousY=initialHand.y
        for i in 1...120 {
            let sample=BowRig.sample(clip:"attack",progress:start+(end-start)*Double(i)/120)
            let hand=position(sample.parts["nearHand"]!),grip=position(sample.parts["farHand"]!)
            XCTAssertGreaterThanOrEqual(hand.y+1e-8,previousY,"The drawing hand should not bounce upward during recovery")
            XCTAssertEqual(grip.x,initialGrip.x,accuracy:1e-8);XCTAssertEqual(grip.y,initialGrip.y,accuracy:1e-8)
            previousY=hand.y
        }
        XCTAssertGreaterThan(previousY-initialHand.y,18)
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
        let beforeTouch=BowRig.sample(clip:"attack",progress:0.19-1e-7)
        let atTouch=BowRig.sample(clip:"attack",progress:0.19)
        XCTAssertEqual(beforeTouch.stringHand.x,atTouch.stringHand.x,accuracy:1e-3)
        XCTAssertEqual(beforeTouch.stringHand.y,atTouch.stringHand.y,accuracy:1e-3)
        let justReleased=BowRig.sample(clip:"attack",progress:BowRig.releaseProgress+1e-7)
        let releasedGrip=position(justReleased.parts["farHand"]!)
        XCTAssertEqual(justReleased.stringHand.x,releasedGrip.x-10,accuracy:1e-6)
        XCTAssertEqual(justReleased.stringHand.y,releasedGrip.y-6,accuracy:1e-6)
        let returned=BowRig.sample(clip:"attack",progress:1)
        let idle=BowRig.sample(clip:"idle",progress:0)
        XCTAssertEqual(returned.stringHand.x,idle.stringHand.x,accuracy:1e-8)
        XCTAssertEqual(returned.stringHand.y,idle.stringHand.y,accuracy:1e-8)
        XCTAssertEqual(position(returned.parts["nearHand"]!).x,position(idle.parts["nearHand"]!).x,accuracy:1e-8)
        XCTAssertEqual(position(returned.parts["nearHand"]!).y,position(idle.parts["nearHand"]!).y,accuracy:1e-8)
        let after=BowRig.sample(clip:"attack",progress:BowRig.releaseProgress+0.07)
        XCTAssertLessThan(position(after.parts["nearHand"]!).x,position(release.parts["nearHand"]!).x)
        XCTAssertGreaterThan(after.stringHand.x,release.stringHand.x)
    }

}
