import XCTest
import ClassroomGameCore
@testable import MeadowBattleSupport
final class PartyTests:XCTestCase {
    func testSupportAtomicAndReplay() throws {
        let p=try PartyEncounter(seed:17,sessionID:"support-test")
        let before=p.state
        for _ in 0..<40 { XCTAssertTrue(p.preview(.support,target:"p1").allowed) }
        XCTAssertEqual(before,p.state)
        let intent=try XCTUnwrap(p.prepare(.support,target:"p1"));XCTAssertEqual(p.state,before)
        let r=try XCTUnwrap(p.commit(intent.id));XCTAssertEqual(r.after.units["p1"]?.health,12);XCTAssertEqual(r.after.units["p1"]?.shield,4)
        XCTAssertEqual(r.after.units["p2"]?.ap,2);XCTAssertNil(try p.commit(intent.id));XCTAssertEqual(p.engine.history.count,1)
        XCTAssertEqual(try p.engine.apply(intent.command,id:intent.id),r)
    }
    func testGroupBuffAndMaxShieldAndCancellation() throws {
        let p=try PartyEncounter(seed:18)
        let start=p.state;_ = p.prepare(.support,target:"p1");p.cancel();XCTAssertEqual(start,p.state)
        let a=try XCTUnwrap(p.prepare(.support,target:"p1"));_ = try p.commit(a.id)
        let b=try XCTUnwrap(p.prepare(.support,target:"p1"));_ = try p.commit(b.id)
        XCTAssertEqual(p.state.units["p1"]?.shield,4)
        let c=try XCTUnwrap(p.prepare(.rally,target:"p1"));let r=try XCTUnwrap(p.commit(c.id))
        XCTAssertEqual(c.targets,["p1","p2"])
        for id in ["p1","p2"] { XCTAssertEqual(r.after.units[id]?.damageBuff?.amount,2);XCTAssertEqual(r.after.units[id]?.damageBuff?.roundsLeft,1) }
        XCTAssertFalse(p.preview(.rally,target:"m1").allowed)
    }
    func testSourceDefinitionsAndItems() throws {
        let p=try PartyEncounter(seed:19),source=try GameCatalog.initial()
        XCTAssertEqual(p.engine.catalog.skills,source.skills);XCTAssertEqual(p.engine.catalog.items,source.items)
        XCTAssertFalse(p.preview(.smallPotion,target:"m1").allowed)
        let i=try XCTUnwrap(p.prepare(.largePotion,target:"p1"));let r=try XCTUnwrap(p.commit(i.id))
        XCTAssertEqual(r.after.units["p1"]?.health,12);XCTAssertEqual(r.after.units["p2"]?.inventory["largePotion"],nil)
    }
    func testRevivalConsumesOnceAndRetainsDownedPlayer() throws {
        let p=try PartyEncounter(seed:21)
        try p.engine.apply(.editResources(unit:"p1",value:ResourcePatch(health:0)))
        let down=p.state.units["p1"]!;XCTAssertFalse(down.isAlive)
        XCTAssertEqual(PartyVisual.pose(unit:down,intent:nil,age:0,time:0,downAge:0).progress,0)
        let falling=PartyVisual.pose(unit:down,intent:nil,age:0.3,time:0.3,downAge:0.3)
        XCTAssertGreaterThan(falling.progress,0);XCTAssertLessThan(falling.progress,1)
        XCTAssertFalse(p.preview(.smallPotion,target:"p1").allowed)
        let intent=try XCTUnwrap(p.prepare(.revivalStone,target:"p1"))
        let before=PartyVisual.pose(unit:down,intent:intent,age:0.71,time:0.71)
        XCTAssertEqual(before.clip,"defeat");XCTAssertEqual(before.progress,1)
        let receipt=try XCTUnwrap(p.commit(intent.id))
        let risen=try XCTUnwrap(receipt.after.units["p1"])
        XCTAssertEqual(risen.health,6);XCTAssertEqual(risen.canActFromRound,2)
        XCTAssertEqual(receipt.after.units["p2"]?.ap,1)
        XCTAssertNil(receipt.after.units["p2"]?.inventory["revivalStone"])
        XCTAssertNil(try p.commit(intent.id))
        let mid=PartyVisual.pose(unit:risen,intent:intent,age:1.02,time:1.02)
        XCTAssertGreaterThan(mid.progress,0);XCTAssertLessThan(mid.progress,1)
    }
    func testBuffDamageAndActualRoundExpiry() throws {
        let p=try PartyEncounter(seed:22)
        let rally=try XCTUnwrap(p.prepare(.rally,target:"p1"));_ = try p.commit(rally.id)
        try p.engine.apply(.endTurn(actor:"p2",timedOut:false))
        let strike=try XCTUnwrap(p.prepare(.attack,target:"m1"));let hit=try XCTUnwrap(p.commit(strike.id))
        XCTAssertEqual(18-(hit.after.units["m1"]?.health ?? 0),hit.dice.first!.total+2)
        for targetRound in [2,3] {
            var guardCount=0
            while p.round<targetRound {
                guardCount += 1;XCTAssertLessThan(guardCount,20)
                try p.engine.apply(.endTurn(actor:p.current!,timedOut:false))
            }
            for id in ["p1","p2"] { XCTAssertEqual(p.state.units[id]?.damageBuff == nil,targetRound==3) }
        }
    }
    func testImpactCadencesAndStaleCancellation() throws {
        for fps in [15,30,60,120] {
            let p=try PartyEncounter(seed:23)
            let intent=try XCTUnwrap(p.prepare(.support,target:"p1"));let before=p.state
            var elapsed=0.0,commits=0
            while elapsed<1.8 {
                elapsed += 1/Double(fps)
                if elapsed>=intent.action.impact,let _=try p.commit(intent.id) { commits += 1;XCTAssertLessThanOrEqual(elapsed-intent.action.impact,1/Double(fps)+1e-8) }
                if elapsed<intent.action.impact { XCTAssertEqual(p.state,before) }
            }
            XCTAssertEqual(commits,1);XCTAssertEqual(p.state.units["p1"]?.health,12)
            let other=try XCTUnwrap(p.prepare(.support,target:"p1"));let snapshot=p.state;p.cancel()
            XCTAssertNil(try p.commit(other.id));XCTAssertEqual(p.state,snapshot)
        }
    }

}
