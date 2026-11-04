import XCTest
import ClassroomGameCore
import MeadowBattleSupport
@testable import MeadowWorldSupport

final class CampaignTests:XCTestCase {
    func layout(combat:Bool=false)throws->GeneratedMeadowMap {
        var c=MeadowMapConfiguration.suggested(total:4,seed:317)
        c.combat=combat ? 3:0;c.boss=0;c.reward=combat ? 0:3;c.empty=0;c.extraRoads=0
        return try MeadowMapGenerator.generate(c)
    }
    func testPreviewAndPartialTravelHaveNoEarlySettlement()throws {
        let s=try MeadowCampaignSession.new(layout:layout()),before=s.engine.archive,start=s.engine.state.units["p1"]!.nodeID
        let target=s.engine.state.map.neighbors(start)[0]
        let preview=s.preview(to:target);XCTAssertTrue(preview.allowed);XCTAssertEqual(preview.cost,1)
        XCTAssertEqual(s.engine.archive,before)
        try s.beginTravel(to:target)
        let p=MeadowCampaignSave.road(s.snapshot.layout,from:start,to:target)!,length=MeadowCampaignSave.length(p)
        XCTAssertTrue(try s.advanceTravel(distance:length*0.5).isEmpty)
        XCTAssertEqual(s.engine.archive,before);XCTAssertFalse(s.engine.state.map.revealed.contains(target))
        let receipts=try s.advanceTravel(distance:length*0.5)
        XCTAssertEqual(receipts.count,1);XCTAssertNil(s.travel)
        for id in ["p1","p2"] {XCTAssertEqual(s.engine.state.units[id]?.nodeID,target);XCTAssertEqual(s.engine.state.units[id]?.ap,2);XCTAssertEqual(s.engine.state.units[id]?.coins,10)}
        XCTAssertTrue(s.engine.state.map.nodes.first{$0.id==target}!.rewardCompleted)
    }
    func testEachActualEdgeArrivesAndChargesOnce()throws {
        let s=try MeadowCampaignSession.new(layout:layout()),start=s.engine.state.units["p1"]!.nodeID
        let target=s.engine.state.map.nodes.max{ s.engine.state.map.distance(from:start,to:$0.id)! < s.engine.state.map.distance(from:start,to:$1.id)! }!.id
        let plan=try s.beginTravel(to:target),receipts=try s.advanceTravel(distance:100000)
        XCTAssertEqual(receipts.count,plan.cost)
        XCTAssertEqual(s.engine.state.units["p1"]?.ap,3-plan.cost)
        XCTAssertEqual(s.engine.state.units["p1"]?.coins,10*plan.cost)
        XCTAssertEqual(s.engine.history.count,plan.cost)
        XCTAssertTrue(try s.advanceTravel(distance:100000).isEmpty)
        try s.refillExploration();try s.beginTravel(to:start);try s.advanceTravel(distance:100000)
        try s.refillExploration();try s.beginTravel(to:target);try s.advanceTravel(distance:100000)
        XCTAssertEqual(s.engine.state.units["p1"]?.coins,10*plan.cost)
    }
    func testMidRoadSaveRestoresExactCursorPausedWithoutReroll()throws {
        let s=try MeadowCampaignSession.new(layout:layout()),start=s.engine.state.units["p1"]!.nodeID,target=s.engine.state.map.neighbors(start)[0]
        try s.beginTravel(to:target);try s.advanceTravel(distance:28)
        let p=s.position(of:"p1"),bytes=try s.snapshot.encoded()
        let restored=try MeadowCampaignSession(save:MeadowCampaignSave.decoded(bytes))
        XCTAssertEqual(restored.position(of:"p1"),p);XCTAssertFalse(restored.isMoving)
        let before=restored.engine.archive
        XCTAssertTrue(try restored.advanceTravel(distance:100000).isEmpty);XCTAssertEqual(restored.engine.archive,before)
        try restored.setPaused(false);XCTAssertEqual(try restored.advanceTravel(distance:100000).count,1)
        XCTAssertEqual(restored.engine.state.units["p1"]?.coins,10)
        XCTAssertEqual(restored.engine.state.random,before.state.random)
    }
    func testArrivalSaveFailureDoesNotSpendAPRevealOrReward()throws {
        var fail=false,stored=Data()
        let s=try MeadowCampaignSession.new(layout:layout(),persist:{data in if fail {throw GameError("disk full")};stored=data})
        let start=s.engine.state.units["p1"]!.nodeID,target=s.engine.state.map.neighbors(start)[0]
        try s.beginTravel(to:target);let before=s.engine.archive,old=stored
        fail=true;XCTAssertThrowsError(try s.advanceTravel(distance:100000))
        XCTAssertEqual(s.engine.archive,before);XCTAssertEqual(stored,old);XCTAssertFalse(s.isMoving)
        fail=false;try s.setPaused(false);try s.advanceTravel(distance:100000)
        XCTAssertEqual(s.engine.history.count,1);XCTAssertEqual(s.engine.state.units["p1"]?.coins,10)
    }
    func testEncounterStopsAtFirstEnemyAndPreservesOneEngine()throws {
        var stored=Data();let s=try MeadowCampaignSession.new(layout:layout(combat:true),persist:{stored=$0})
        let start=s.engine.state.units["p1"]!.nodeID,target=s.engine.state.map.nodes.max{s.engine.state.map.distance(from:start,to:$0.id)!<s.engine.state.map.distance(from:start,to:$1.id)!}!.id
        let plan=try s.beginTravel(to:target);XCTAssertEqual(plan.cost,1)
        XCTAssertNil(s.engine.state.battle);XCTAssertEqual(try s.advanceTravel(distance:100000).count,1)
        XCTAssertNotNil(s.engine.state.battle);XCTAssertNil(s.travel)
        let battle=try PartyEncounter(engine:s.engine,sessionID:"real-battle")
        XCTAssertTrue(battle.engine === s.engine)
        for _ in 0..<160 {
            if battle.terminal {break}
            guard let actor=battle.current else {XCTFail("missing actor");break}
            let intent:PartyIntent?
            if s.engine.state.units[actor]?.kind == .monster {intent=battle.prepareMonsterStep()}
            else {
                let foe=battle.monsterIDs.first{s.engine.state.units[$0]?.isAlive==true}!
                intent=battle.prepare(.attack,target:foe) ?? battle.prepare(.endTurn,target:actor)
            }
            let action=try XCTUnwrap(intent),before=s.engine.archive
            XCTAssertEqual(try MeadowCampaignSave.decoded(stored).archive,before)
            let receipt=try XCTUnwrap(battle.commit(action.id))
            XCTAssertTrue(battle.engine === s.engine);XCTAssertEqual(receipt.after,s.engine.state)
            XCTAssertNil(try battle.commit(action.id))
            XCTAssertEqual(try MeadowCampaignSave.decoded(stored).archive,s.engine.archive)
        }
        XCTAssertTrue(battle.terminal)
        let restored=try MeadowCampaignSession(save:.decoded(stored))
        XCTAssertEqual(restored.engine.archive,s.engine.archive)
        XCTAssertEqual(restored.snapshot.layout,s.snapshot.layout)
    }
    func testConfirmedBattleSaveFailureLeavesLiveDiceAndResourcesUnchanged()throws {
        var fail=false
        let s=try MeadowCampaignSession.new(layout:layout(combat:true),persist:{_ in if fail {throw GameError("disk")}})
        let start=s.engine.state.units["p1"]!.nodeID;try s.beginTravel(to:s.engine.state.map.neighbors(start)[0]);try s.advanceTravel(distance:100000)
        let b=try PartyEncounter(engine:s.engine)
        let intent=try XCTUnwrap(s.engine.state.units[b.current!]?.kind == .monster ? b.prepareMonsterStep():b.prepare(.attack,target:b.monsterIDs[0]))
        let before=s.engine.archive;fail=true
        XCTAssertThrowsError(try b.commit(intent.id));XCTAssertEqual(s.engine.archive,before)
        XCTAssertNil(b.pending)
    }
    func testStoreDoesNotReplaceCorruptFilesAndRejectsBadCursor()throws {
        let folder=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer {try? FileManager.default.removeItem(at:folder)}
        let store=MeadowCampaignStore(url:folder.appendingPathComponent("campaign-v1.json"))
        try store.write(Data("invalid".utf8));XCTAssertThrowsError(try store.read())
        XCTAssertEqual(try Data(contentsOf:store.url),Data("invalid".utf8))
        let s=try MeadowCampaignSession.new(layout:layout());var snapshot=s.snapshot;snapshot.formatVersion=999
        XCTAssertThrowsError(try MeadowCampaignSession(save:snapshot))
        let start=s.engine.state.units["p1"]!.nodeID;try s.beginTravel(to:s.engine.state.map.neighbors(start)[0])
        snapshot=s.snapshot;snapshot.travel?.distance = .nan;XCTAssertThrowsError(try snapshot.encoded())
        snapshot=s.snapshot;snapshot.travel?.leg=999;XCTAssertThrowsError(try snapshot.encoded())
    }
    func testBossKeepsOriginalStatsAndChoosesRealRegenerationAI()throws {
        var c=MeadowMapConfiguration.suggested(total:4,seed:317);c.combat=0;c.boss=3;c.reward=0;c.empty=0
        let session=try MeadowCampaignSession.new(layout:MeadowMapGenerator.generate(c))
        let source=try GameCatalog.initial(),boss=try session.engine.catalog.monster("meadowElderStag")
        XCTAssertEqual(boss.attributes,try source.monster("caveTroll").attributes)
        XCTAssertEqual(boss.skills,try source.monster("caveTroll").skills)
        let start=session.engine.state.units["p1"]!.nodeID
        try session.beginTravel(to:session.engine.state.map.neighbors(start)[0]);try session.advanceTravel(distance:100000)
        let encounter=try PartyEncounter(engine:session.engine),id=encounter.monsterIDs[0]
        try session.engine.apply(.editResources(unit:id,value:ResourcePatch(health:12)))
        for _ in 0..<3 where session.engine.state.units[encounter.current ?? ""]?.kind == .player {
            try session.engine.apply(.endTurn(actor:encounter.current!,timedOut:false))
        }
        let before=session.engine.archive,intent=try XCTUnwrap(encounter.prepareMonsterStep())
        XCTAssertEqual(intent.action,.regeneration);XCTAssertEqual(intent.target,id)
        XCTAssertEqual(session.engine.archive,before)
        XCTAssertEqual(PartyVisual.foot(id)?.x,PartyVisual.feet["m1"]?.x)
        XCTAssertEqual(PartyVisual.hitPoint(target:id).x,PartyVisual.hitPoint(target:"m1").x)
        let receipt=try XCTUnwrap(encounter.commit(intent.id))
        XCTAssertGreaterThan(receipt.after.units[id]!.health,12)
    }
    func testVictoryAndNextEncounterDoNotResetHealthOrInventory()throws {
        let session=try MeadowCampaignSession.new(layout:layout(combat:true)),start=session.engine.state.units["p1"]!.nodeID
        try session.engine.apply(.editResources(unit:"p1",value:ResourcePatch(health:11)))
        let target=session.engine.state.map.neighbors(start)[0]
        try session.beginTravel(to:target);try session.advanceTravel(distance:100000)
        let before=session.engine.archive,_=try PartyEncounter(engine:session.engine)
        XCTAssertEqual(session.engine.archive,before)
        for monster in session.engine.state.units.values.filter({$0.kind == .monster && $0.active && $0.isAlive}) {
            try session.engine.apply(.setHealth(unit:monster.id,value:0,killer:"p1"))
        }
        XCTAssertNil(session.engine.state.battle);XCTAssertEqual(session.engine.state.units["p1"]!.health,11)
        let inventory=session.engine.state.units["p1"]!.inventory,coins=session.engine.state.units["p1"]!.coins
        let resumed=try MeadowCampaignSession(save:.decoded(session.snapshot.encoded()))
        XCTAssertEqual(resumed.engine.state.units["p1"]!.health,11)
        XCTAssertEqual(resumed.engine.state.units["p1"]!.inventory,inventory);XCTAssertEqual(resumed.engine.state.units["p1"]!.coins,coins)
        try resumed.refillExploration()
        let next=resumed.engine.state.map.nodes.first{ node in node.kind == .combat && resumed.engine.state.units.values.contains{$0.nodeID==node.id && $0.kind == .monster && $0.isAlive}}!.id
        try resumed.beginTravel(to:next);try resumed.advanceTravel(distance:100000)
        XCTAssertNotNil(resumed.engine.state.battle);XCTAssertEqual(resumed.engine.state.units["p1"]!.health,11)
        XCTAssertEqual(resumed.engine.state.units["p1"]!.inventory,inventory)
    }

}
