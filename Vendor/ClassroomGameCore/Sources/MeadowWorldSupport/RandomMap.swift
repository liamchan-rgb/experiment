import Foundation
import ClassroomGameCore

public struct MeadowMapConfiguration: Codable, Equatable {
    public var seed: UInt64 = 31827
    public var total = 10
    public var combat = 4
    public var boss = 1
    public var reward = 3
    public var empty = 1
    public var extraRoads = 1
    public var minimumBossHops = 0
    public var decorationCount = 70
    public init() {}
    public static func suggested(total: Int, seed: UInt64 = 31827) -> Self {
        var c = Self(); c.seed = seed; c.total = total
        guard (4...30).contains(total) else { return c }
        c.combat = Int(floor(Double(total) * 0.4)); c.reward = Int(floor(Double(total) * 0.3))
        c.empty = total - 2 - c.combat - c.reward
        return c
    }
    public func validate() throws {
        guard (4...30).contains(total) else { throw GameError("总节点数须为4—30。") }
        guard [combat,boss,reward,empty].allSatisfy({ (0...30).contains($0) }),
              1 + combat + boss + reward + empty == total else { throw GameError("起点固定1，各类数量须为非负整数，总和须等于总节点数。") }
        guard (0...MeadowMapGenerator.maximumExtraRoads(total: total)).contains(extraRoads) else {
            throw GameError("此规模可增加0—\(MeadowMapGenerator.maximumExtraRoads(total: total))条环路道路。")
        }
        guard (0..<total).contains(minimumBossHops), (0...120).contains(decorationCount) else { throw GameError("Boss距离或装饰数量无效。") }
    }
}

public struct MeadowWorldPoint: Codable, Equatable {
    public var x: Double
    public var y: Double
    public init(_ x: Double, _ y: Double) { self.x=x; self.y=y }
}
public struct MeadowWorldRoad: Codable, Equatable {
    public let from: Int
    public let to: Int
    public let width: Double
    public let points: [MeadowWorldPoint]
}
public struct MeadowWorldProp: Codable, Equatable {
    public let asset: String
    public let x: Double
    public let y: Double
    public let width: Double
    public let wind: Double
}
public struct GeneratedMeadowMap: Codable, Equatable {
    public let generatorVersion: Int
    public let configuration: MeadowMapConfiguration
    public let map: GameMap
    public let roads: [MeadowWorldRoad]
    public let props: [MeadowWorldProp]
    public let spawn: MeadowWorldPoint
}

// Stable SplitMix64 streams; no Swift hashValue, process random seed or dice RNG.
private struct MapRandom {
    var state: UInt64
    mutating func next() -> UInt64 {
        state &+= 0x9e3779b97f4a7c15
        var z=state; z=(z ^ (z >> 30)) &* 0xbf58476d1ce4e5b9
        z=(z ^ (z >> 27)) &* 0x94d049bb133111eb
        return z ^ (z >> 31)
    }
    mutating func value(_ low: Double, _ high: Double) -> Double {
        low + (high-low) * Double(next() >> 11) / 9007199254740992
    }
    mutating func shuffle<T>(_ values: inout [T]) {
        guard values.count > 1 else { return }
        for i in stride(from: values.count-1, through: 1, by: -1) {
            values.swapAt(i, Int(next() % UInt64(i+1)))
        }
    }
}

public enum MeadowMapGenerator {
    public static let version = 1
    private static func columns(_ n: Int) -> Int { Int(sqrt(Double(n)*1.35).rounded()) }
    private static func candidates(_ n: Int) -> [(Int,Int)] {
        let cols=columns(n)
        return (0..<n).flatMap { i -> [(Int,Int)] in
            var result:[(Int,Int)]=[]
            if i % cols != cols-1 && i+1<n { result.append((i,i+1)) }
            if i+cols<n { result.append((i,i+cols)) }
            return result
        }
    }
    public static func maximumExtraRoads(total: Int) -> Int {
        guard (4...30).contains(total) else { return 0 }
        return candidates(total).count-total+1
    }
    public static func generate(_ c: MeadowMapConfiguration) throws -> GeneratedMeadowMap {
        try c.validate()
        // Grid-neighbor corridors preserve topology when laid out as curved paths.
        // Random spanning tree, loop choice, jitter, reflection and contents vary.
        for attempt in 0..<64 {
            var topology=MapRandom(state:c.seed ^ 0x544f504f &+ UInt64(attempt))
            var edges=candidates(c.total); topology.shuffle(&edges)
            var groups=Array(0..<c.total), tree:[(Int,Int)]=[], spare:[(Int,Int)]=[]
            for (a,b) in edges {
                let ga=groups[a], gb=groups[b]
                if ga != gb {
                    tree.append((a,b)); groups=groups.map { $0==gb ? ga : $0 }
                } else { spare.append((a,b)) }
            }
            tree += spare.prefix(c.extraRoads)
            tree.sort { $0.0 == $1.0 ? $0.1 < $1.1 : $0.0 < $1.0 }
            var layout=MapRandom(state:c.seed ^ 0x4c41594f5554)
            let cols=columns(c.total), rows=Int(ceil(Double(c.total)/Double(cols)))
            let flipX=layout.next() & 1 == 0, flipY=layout.next() & 1 == 0
            let positions=(0..<c.total).map { i -> MeadowWorldPoint in
                let x=100 + Double(i%cols)*1080/Double(max(1,cols-1)) + layout.value(-13,13)
                let y=85 + Double(i/cols)*550/Double(max(1,rows-1)) + layout.value(-10,10)
                return MeadowWorldPoint(flipX ? 1280-x : x,flipY ? 720-y : y)
            }
            let start=positions.indices.min { positions[$0].x-positions[$0].y < positions[$1].x-positions[$1].y }!
            var distance=Array(repeating:-1,count:c.total); distance[start]=0
            var queue=[start], cursor=0
            while cursor<queue.count {
                let u=queue[cursor]; cursor+=1
                for (a,b) in tree {
                    let v=a==u ? b : b==u ? a : -1
                    if v>=0 && distance[v]<0 { distance[v]=distance[u]+1; queue.append(v) }
                }
            }
            var remaining=Array(0..<c.total).filter { $0 != start }; topology.shuffle(&remaining)
            remaining.sort { distance[$0] > distance[$1] }
            let bosses=Array(remaining.prefix(c.boss))
            if bosses.contains(where:{ distance[$0]<c.minimumBossHops }) { continue }
            var kinds=Array(repeating:NodeKind.empty,count:c.total); kinds[start] = .start
            for id in bosses { kinds[id] = .boss }
            remaining.removeAll { bosses.contains($0) }; topology.shuffle(&remaining)
            let contents=Array(repeating:NodeKind.combat,count:c.combat) + Array(repeating:NodeKind.reward,count:c.reward) + Array(repeating:NodeKind.empty,count:c.empty)
            for (id,kind) in zip(remaining,contents) { kinds[id]=kind }
            let titles:[NodeKind:String]=[.start:"起点营地",.combat:"林间战斗",.boss:"首领地点",.reward:"补给地点",.empty:"林间空地"]
            let nodes=(0..<c.total).map { id in
                MapNode(id:id,name:"\(titles[kinds[id]]!) · \(id+1)",kind:kinds[id],x:positions[id].x/1280,y:positions[id].y/720,
                        reward:kinds[id] == .reward ? NodeReward() : nil)
            }
            let map=GameMap(nodes:nodes,roads:tree.map { MapRoad($0.0,$0.1) },seed:c.seed,revealed:[start])
            try map.validate()
            var curves=MapRandom(state:c.seed ^ 0x524f414453)
            let roads=tree.map { a,b -> MeadowWorldRoad in
                let p=positions[a],q=positions[b], dx=q.x-p.x,dy=q.y-p.y, length=hypot(dx,dy)
                let bend=curves.value(-5,5)
                let points=[p,MeadowWorldPoint(p.x+dx/3-dy/length*bend,p.y+dy/3+dx/length*bend),
                            MeadowWorldPoint(p.x+dx*2/3-dy/length*bend,p.y+dy*2/3+dx/length*bend),q]
                return MeadowWorldRoad(from:a,to:b,width:22,points:points)
            }
            let props=decorate(c,positions:positions,roads:roads,start:start)
            return GeneratedMeadowMap(generatorVersion:version,configuration:c,map:map,roads:roads,props:props,spawn:positions[start])
        }
        throw GameError("当前环路与Boss距离要求无法同时满足，请减少环路或降低Boss最短距离。节点数量未被修改。")
    }

    public static func distance(_ p: MeadowWorldPoint, to roads: [MeadowWorldRoad]) -> Double {
        roads.flatMap { road in zip(road.points,road.points.dropFirst()).map { a,b -> Double in
            let dx=b.x-a.x,dy=b.y-a.y
            let t=max(0,min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/max(0.001,dx*dx+dy*dy)))
            return hypot(p.x-a.x-t*dx,p.y-a.y-t*dy)
        } }.min() ?? .infinity
    }

    private static func decorate(_ c: MeadowMapConfiguration,positions:[MeadowWorldPoint],roads:[MeadowWorldRoad],start:Int) -> [MeadowWorldProp] {
        var rng=MapRandom(state:c.seed ^ 0x50524f5053), props:[MeadowWorldProp]=[]
        // Reserve physical footprints, not image alpha bounds. Extra margin also
        // covers the road smoother's bounded 5px bow between control points.
        let spawn=positions[start]
        for offset in [(0.0,-90.0),(-105,0),(105,0),(0,90)] {
            let p=MeadowWorldPoint(spawn.x+offset.0,spawn.y+offset.1)
            if distance(p,to:roads)>68 && positions.allSatisfy({hypot($0.x-p.x,$0.y-p.y)>78}) {
                props.append(MeadowWorldProp(asset:"CampTent",x:p.x,y:p.y,width:105,wind:0)); break
            }
        }
        let assets=["OakA","OakB","Pines","RockLow","RockHigh","RockSmall","Shrub","Flowers"]
        for _ in 0..<1400 {
            if props.count>=c.decorationCount+1 { break }
            let p=MeadowWorldPoint(rng.value(-70,1350),rng.value(-80,820))
            guard distance(p,to:roads)>58,
                  positions.allSatisfy({hypot($0.x-p.x,$0.y-p.y)>76}),
                  props.allSatisfy({hypot($0.x-p.x,$0.y-p.y)>max(42,$0.width*0.6)}) else { continue }
            let asset=assets[Int(rng.next()%UInt64(assets.count))]
            let width=asset=="Flowers" ? rng.value(14,23) : asset=="Shrub" ? rng.value(25,35) : rng.value(50,76)
            props.append(MeadowWorldProp(asset:asset,x:p.x,y:p.y,width:width,wind:asset.hasPrefix("Rock") ? 0 : 1))
        }
        return props
    }
}
