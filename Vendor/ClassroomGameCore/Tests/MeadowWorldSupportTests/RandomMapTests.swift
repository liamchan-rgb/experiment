import XCTest
import ClassroomGameCore
@testable import MeadowWorldSupport

final class RandomMapTests: XCTestCase {
    func testSizesSeedsAndGraphContracts() throws {
        for n in 4...30 { for seed in 0..<24 {
            let c=MeadowMapConfiguration.suggested(total:n,seed:UInt64(seed))
            let result=try MeadowMapGenerator.generate(c)
            try result.map.validate()
            XCTAssertEqual(result.map.nodes.count,n)
            XCTAssertEqual(result.map.nodes.filter{$0.kind == .start}.count,1)
            for (kind,count) in [(NodeKind.combat,c.combat),(.boss,c.boss),(.reward,c.reward),(.empty,c.empty)] {
                XCTAssertEqual(result.map.nodes.filter{$0.kind==kind}.count,count)
            }
            XCTAssertEqual(result.roads.count,n-1+c.extraRoads)
            XCTAssertEqual(result.map.roads.count,result.roads.count)
            for road in result.roads {
                let a=result.map.nodes.first{$0.id==road.from}!,b=result.map.nodes.first{$0.id==road.to}!
                XCTAssertEqual(road.points.first!.x,a.x*1280,accuracy:0.000001)
                XCTAssertEqual(road.points.last!.y,b.y*720,accuracy:0.000001)
            }
            XCTAssertTrue(result.map.nodes.allSatisfy{(0...1).contains($0.x) && (0...1).contains($0.y)})
            XCTAssertTrue(result.props.allSatisfy{MeadowMapGenerator.distance(MeadowWorldPoint($0.x,$0.y),to:result.roads)>58})
        } }
    }
    func testExactManualQuotasAndNoBoss() throws {
        var c=MeadowMapConfiguration();c.combat=0;c.boss=0;c.reward=0;c.empty=9
        let r=try MeadowMapGenerator.generate(c)
        XCTAssertEqual(r.map.nodes.filter{$0.kind == .empty}.count,9)
        XCTAssertFalse(r.map.nodes.contains{$0.kind == .boss || $0.kind == .combat})
    }
    func testDeterministicAndDecorationIndependent() throws {
        let c=MeadowMapConfiguration()
        let a=try MeadowMapGenerator.generate(c),b=try MeadowMapGenerator.generate(c)
        XCTAssertEqual(a,b)
        let enc=JSONEncoder();enc.outputFormatting=[.sortedKeys]
        XCTAssertEqual(try enc.encode(a),try enc.encode(b))
        var different=c;different.decorationCount=10
        let d=try MeadowMapGenerator.generate(different)
        XCTAssertEqual(a.map,d.map);XCTAssertEqual(a.roads,d.roads)
        different.seed=777
        XCTAssertNotEqual(a.map,try MeadowMapGenerator.generate(different).map)
    }
    func testInvalidAndImpossibleConstraintsFailWithoutChangingQuota() {
        var c=MeadowMapConfiguration();c.empty=2
        XCTAssertThrowsError(try MeadowMapGenerator.generate(c))
        c.empty = -1;XCTAssertThrowsError(try MeadowMapGenerator.generate(c))
        c=MeadowMapConfiguration.suggested(total:4);c.extraRoads=2
        XCTAssertThrowsError(try MeadowMapGenerator.generate(c))
        c.extraRoads=1;c.minimumBossHops=3
        XCTAssertThrowsError(try MeadowMapGenerator.generate(c)) // 4-cell ring diameter is 2.
        c=MeadowMapConfiguration();c.total=Int.max
        XCTAssertThrowsError(try MeadowMapGenerator.generate(c))
    }
    func testBossHopConstraintAndCodableSnapshot() throws {
        var c=MeadowMapConfiguration();c.minimumBossHops=3
        let r=try MeadowMapGenerator.generate(c),start=r.map.nodes.first{$0.kind == .start}!.id
        XCTAssertTrue(r.map.nodes.filter{$0.kind == .boss}.allSatisfy{r.map.distance(from:start,to:$0.id)!>=3})
        let copy=try JSONDecoder().decode(GeneratedMeadowMap.self,from:JSONEncoder().encode(r))
        XCTAssertEqual(r,copy)
    }
}
