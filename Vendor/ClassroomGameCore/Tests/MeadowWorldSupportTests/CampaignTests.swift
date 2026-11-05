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
        let dice=BattleDice.channels(intent.action,actor:before.state.units[id]!,target:before.state.units[id]!,catalog:session.engine.catalog,receipt:encounter.confirmedReceipt)
        XCTAssertFalse(dice.isEmpty)
        for age in stride(from:0.0,through:1.1,by:1.0/60) {
            let anchor=PartyVisual.diceAnchor(actor:id,intent:intent,age:age,diceCount:dice.count)
            XCTAssertTrue(anchor.x.isFinite && anchor.y.isFinite)
        }
        let receipt=try XCTUnwrap(encounter.commit(intent.id))
        XCTAssertGreaterThan(receipt.after.units[id]!.health,12)
    }

    func testCampaignDiceThroughTwoRoundsAndResumedMonsterTurn()throws {
        for seed:UInt64 in [317,318,319] {
            var config=MeadowMapConfiguration.suggested(total:4,seed:seed)
            config.combat=3;config.boss=0;config.reward=0;config.empty=0
            var session=try MeadowCampaignSession.new(layout:MeadowMapGenerator.generate(config))
            let start=session.engine.state.units["p1"]!.nodeID
            try session.beginTravel(to:session.engine.state.map.neighbors(start)[0]);try session.advanceTravel(distance:100000)
            var encounter=try PartyEncounter(engine:session.engine),monsterTurns=0,resumed=false
            for _ in 0..<30 {
                if encounter.round>=3 {break}
                let actor=try XCTUnwrap(encounter.current)
                if session.engine.state.units[actor]?.kind == .player {
                    let intent=try XCTUnwrap(encounter.prepare(.endTurn,target:actor));_ = try encounter.commit(intent.id)
                } else {
                    // Preserve both players for two full rounds; no player
                    // attacks, so every persistent monster reaches its turn.
                    for id in session.playerIDs {
                        let maximum=try GameRules.attributes(session.engine.state.units[id]!,catalog:session.engine.catalog).maximumHealth
                        try session.engine.apply(.editResources(unit:id,value:ResourcePatch(health:maximum,shield:8)))
                    }
                    if !resumed {
                        let archive=session.engine.archive
                        session=try MeadowCampaignSession(save:.decoded(session.snapshot.encoded()))
                        XCTAssertEqual(session.engine.archive,archive)
                        encounter=try PartyEncounter(engine:session.engine);resumed=true
                    }
                    let intent=try XCTUnwrap(encounter.prepareMonsterStep()),before=session.engine.archive
                    let dice=BattleDice.channels(intent.action,actor:before.state.units[intent.actor]!,target:before.state.units[intent.target]!,catalog:session.engine.catalog,receipt:encounter.confirmedReceipt)
                    XCTAssertFalse(dice.isEmpty);XCTAssertTrue(intent.actor.hasPrefix("m-"))
                    for age in stride(from:0.0,through:1.1,by:1.0/60) {
                        let anchor=PartyVisual.diceAnchor(actor:intent.actor,intent:intent,age:age,shielded:true,diceCount:dice.count)
                        XCTAssertTrue(anchor.x.isFinite && anchor.y.isFinite)
                    }
                    XCTAssertEqual(session.engine.archive,before)
                    _ = try encounter.commit(intent.id);XCTAssertNil(try encounter.commit(intent.id));monsterTurns+=1
                }
            }
            XCTAssertTrue(resumed);XCTAssertGreaterThanOrEqual(encounter.round,3)
            XCTAssertGreaterThanOrEqual(monsterTurns,encounter.monsterIDs.count*2)
        }
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

    func testEncounterEditingIsValidatedLoggedAndPersisted()throws {
        var config=MeadowMapConfiguration.suggested(total:4,seed:731)
        config.combat=3;config.boss=0;config.reward=0;config.empty=0;config.extraRoads=0
        let layout=try MeadowMapGenerator.generate(config)
        var stored=Data()
        let session=try MeadowCampaignSession.new(layout:layout,persist:{stored=$0})
        let node=try XCTUnwrap(session.engine.state.map.nodes.first{$0.kind == .combat})
        let receipt=try session.configureEncounter(node:node.id,templates:["meadowElderStag","meadowStag"])
        XCTAssertEqual(receipt.command,.configureNodeEncounter(node:node.id,monsterTemplates:["meadowElderStag","meadowStag"]))
        XCTAssertTrue(receipt.events.contains{$0.kind=="nodeEncounterConfigured"})
        let monsters=session.engine.state.units.values.filter{$0.kind == .monster && $0.nodeID==node.id}
        XCTAssertEqual(monsters.count,2)
        XCTAssertEqual(Set(monsters.map(\.templateID)),Set(["meadowElderStag","meadowStag"]))
        let restored=try MeadowCampaignSession(save:MeadowCampaignSave.decoded(stored))
        XCTAssertEqual(restored.engine.state.units.values.filter{$0.kind == .monster && $0.nodeID==node.id}.count,2)
        XCTAssertEqual(restored.engine.history.last?.events.first{$0.kind=="nodeEncounterConfigured"}?.detail,
                       "node=\(node.id);templates=meadowElderStag,meadowStag")
        let before=restored.engine.archive
        XCTAssertThrowsError(try restored.configureEncounter(node:node.id,templates:[]))
        XCTAssertThrowsError(try restored.configureEncounter(node:node.id,templates:["unknownMonster"]))
        XCTAssertThrowsError(try restored.configureEncounter(node:9999,templates:["meadowStag"]))
        XCTAssertEqual(restored.engine.archive,before)
    }

    func testClaimedRewardEditingRequiresExplicitResetAndPaysUpdatedValueOnce()throws {
        var config=MeadowMapConfiguration.suggested(total:4,seed:732)
        config.combat=0;config.boss=0;config.reward=3;config.empty=0;config.extraRoads=0
        var stored=Data()
        let session=try MeadowCampaignSession.new(layout:MeadowMapGenerator.generate(config),persist:{stored=$0})
        let start=session.engine.state.units["p1"]!.nodeID
        let node=try XCTUnwrap(session.engine.state.map.nodes.first{
            $0.kind == .reward && session.engine.state.map.neighbors(start).contains($0.id)
        })
        _=try session.beginTravel(to:node.id);_=try session.advanceTravel(distance:100_000)
        XCTAssertTrue(session.engine.state.map.nodes.first{$0.id==node.id}!.rewardCompleted)
        let afterOriginalClaim=session.engine.state.units["p1"]!
        let updated=NodeReward(coins:37,score:8,items:["smallPotion":2])
        let edit=try session.configureReward(node:node.id,reward:updated)
        XCTAssertTrue(edit.events.contains{$0.kind=="nodeRewardConfigured"})
        XCTAssertTrue(session.engine.state.map.nodes.first{$0.id==node.id}!.rewardCompleted)
        XCTAssertEqual(session.engine.state.units["p1"]!.coins,afterOriginalClaim.coins)
        XCTAssertEqual(session.engine.state.units["p1"]!.score,afterOriginalClaim.score)
        XCTAssertEqual(session.engine.state.units["p1"]!.inventory,afterOriginalClaim.inventory)
        let restored=try MeadowCampaignSession(save:MeadowCampaignSave.decoded(stored))
        XCTAssertEqual(restored.engine.state.map.nodes.first{$0.id==node.id}!.reward,updated)
        XCTAssertTrue(restored.engine.state.map.nodes.first{$0.id==node.id}!.rewardCompleted)
        let beforeReset=restored.engine.state.units["p1"]!
        let reset=try restored.resetReward(node:node.id)
        XCTAssertTrue(reset.events.contains{$0.kind=="nodeRewardReset"})
        XCTAssertFalse(restored.engine.state.map.nodes.first{$0.id==node.id}!.rewardCompleted)
        XCTAssertEqual(restored.engine.state.units["p1"]!.coins,beforeReset.coins)
        XCTAssertEqual(restored.engine.state.units["p1"]!.score,beforeReset.score)
        XCTAssertEqual(restored.engine.state.units["p1"]!.inventory,beforeReset.inventory)
        try restored.refillExploration();_=try restored.beginTravel(to:start);_=try restored.advanceTravel(distance:100_000)
        let beforeUpdatedClaim=restored.engine.state.units["p1"]!
        try restored.refillExploration();_=try restored.beginTravel(to:node.id);_=try restored.advanceTravel(distance:100_000)
        let afterUpdatedClaim=restored.engine.state.units["p1"]!
        XCTAssertEqual(afterUpdatedClaim.coins,beforeUpdatedClaim.coins+37)
        XCTAssertEqual(afterUpdatedClaim.score,beforeUpdatedClaim.score+8)
        XCTAssertEqual(afterUpdatedClaim.inventory["smallPotion"] ?? 0,(beforeUpdatedClaim.inventory["smallPotion"] ?? 0)+2)
        XCTAssertTrue(restored.engine.state.map.nodes.first{$0.id==node.id}!.rewardCompleted)
        try restored.refillExploration();_=try restored.beginTravel(to:start);_=try restored.advanceTravel(distance:100_000)
        let beforeRepeat=restored.engine.state.units["p1"]!
        try restored.refillExploration();_=try restored.beginTravel(to:node.id);_=try restored.advanceTravel(distance:100_000)
        XCTAssertEqual(restored.engine.state.units["p1"]!.coins,beforeRepeat.coins)
        XCTAssertEqual(restored.engine.state.units["p1"]!.score,beforeRepeat.score)
        XCTAssertEqual(restored.engine.state.units["p1"]!.inventory,beforeRepeat.inventory)
        let saved=try MeadowCampaignSession(save:MeadowCampaignSave.decoded(stored))
        XCTAssertEqual(saved.engine.state.map.nodes.first{$0.id==node.id}!.reward,updated)
        XCTAssertTrue(saved.engine.state.map.nodes.first{$0.id==node.id}!.rewardCompleted)
    }

}
