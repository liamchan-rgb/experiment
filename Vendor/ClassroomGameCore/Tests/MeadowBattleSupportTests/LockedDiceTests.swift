import XCTest
import ClassroomGameCore
@testable import MeadowBattleSupport
final class LockedDiceTests:XCTestCase {
    func testConfirmationResolvesOnceWithoutApplyingDamageUntilImpact() throws {
        let p=try PartyEncounter(seed:50),before=p.state,history=p.engine.history.count
        let i=try XCTUnwrap(p.prepare(.ambush,target:"m1")),r=try XCTUnwrap(p.confirmedReceipt)
        XCTAssertEqual(r.dice.first?.values.count,2);XCTAssertEqual(p.state,before);XCTAssertEqual(p.engine.history.count,history)
        let d=BattleDice.channels(.ambush,actor:before.units["p2"]!,target:before.units["m1"]!,catalog:p.engine.catalog,receipt:r)
        XCTAssertEqual(d.filter { $0.sides>0 }.compactMap(\.value),r.dice.first?.values)
        let committed=try XCTUnwrap(p.commit(i.id));XCTAssertEqual(committed.after,r.after);XCTAssertEqual(p.state,r.after)
        XCTAssertEqual(p.engine.history.count,history+1);XCTAssertNil(try p.commit(i.id));XCTAssertNil(p.confirmedReceipt)
    }
    func testCancelAndStaleReservationDoNotConsumeOrOverwriteState() throws {
        let p=try PartyEncounter(seed:50),before=p.state
        let first=try XCTUnwrap(p.prepare(.ambush,target:"m1")),values=p.confirmedReceipt?.dice.first?.values
        p.cancel();XCTAssertEqual(p.state,before);XCTAssertNil(try p.commit(first.id))
        let second=try XCTUnwrap(p.prepare(.ambush,target:"m1"));XCTAssertEqual(p.confirmedReceipt?.dice.first?.values,values)
        try p.engine.apply(.editResources(unit:"p1",value:ResourcePatch(health:7)))
        let changed=p.state;XCTAssertThrowsError(try p.commit(second.id));XCTAssertEqual(p.state,changed);XCTAssertNil(p.pending)
    }
    func testLockedDiceAreImmediatelyStationaryAndDamageIsCenteredOnContact() {
        let die=BattleDie("red",sides:8,value:7)
        let a=PolyhedralDice.sample(die:die,time:1,index:0,count:4,resolvedAge:nil,visibleAge:1,locked:true)
        let b=PolyhedralDice.sample(die:die,time:2,index:0,count:4,resolvedAge:nil,visibleAge:2,locked:true)
        XCTAssertEqual(a.resultMix,1);XCTAssertEqual(a.offsetY,0);XCTAssertEqual(a.orientation.w,b.orientation.w);XCTAssertEqual(a.orientation.x,b.orientation.x)
        XCTAssertEqual(a.faces.max { $0.depth<$1.depth }?.value,7)
        for id in ["p1","m1"] {
            let hit=PartyVisual.hitPoint(target:id),origin=PartyVisual.damageLabelOrigin(at:hit,width:40,height:30,age:0)
            XCTAssertEqual(origin.x+20,hit.x);XCTAssertEqual(origin.y+15,hit.y)
            XCTAssertLessThan(PartyVisual.damageLabelOrigin(at:hit,width:40,height:30,age:0.5).y,origin.y)
        }
    }
}
