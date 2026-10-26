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
    func testRegisteredBonesStayConnectedAndUnstretchedThroughDrawingAndRelease() {
        for i in 0...600 {
            let s=BowRig.sample(clip:"attack",progress:Double(i)/600)
            for side in ["near","far"] {
                let u=s.parts[side+"Upper"]!,f=s.parts[side+"Fore"]!,h=s.parts[side+"Hand"]!
                func transformed(_ x:Double,_ y:Double,_ q:BowPartPose)->PartyPoint { let dx=x-q.pivot.x,dy=y-q.pivot.y;return PartyPoint(q.pivot.x+q.offset.x+dx*cos(q.rotation)-dy*sin(q.rotation),q.pivot.y+q.offset.y+dx*sin(q.rotation)+dy*cos(q.rotation)) }
                let elbow=transformed(128,158,u);XCTAssertEqual(elbow.x,128+f.offset.x,accuracy:1e-8);XCTAssertEqual(elbow.y,158+f.offset.y,accuracy:1e-8)
                let wrist=transformed(145.6,163.7,f);XCTAssertEqual(wrist.x,145.6+h.offset.x,accuracy:1e-8);XCTAssertEqual(wrist.y,163.7+h.offset.y,accuracy:1e-8)
            }
        }
        let held=BowRig.sample(clip:"attack",progress:0.35)
        XCTAssertTrue(held.arrowVisible);XCTAssertLessThan(held.stringHand.x,held.upperTip.x)
        XCTAssertFalse(BowRig.sample(clip:"attack",progress:0.5).arrowVisible)
    }
}
