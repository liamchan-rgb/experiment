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
    public var decorationCount = 100
    public init() {}
    public static func suggested(total: Int, seed: UInt64 = 31827) -> Self {
        var c = Self(); c.seed = seed; c.total = total
        guard (4...30).contains(total) else { return c }
        c.combat = Int(floor(Double(total) * 0.4)); c.reward = Int(floor(Double(total) * 0.3))
        c.empty = total - 2 - c.combat - c.reward
        return c
    }
    public func changingTotal(to value: Int) throws -> Self {
        guard (4...30).contains(value) else { throw GameError("总节点数须为4—30。") }
        var c=Self.suggested(total:value,seed:seed)
        c.extraRoads=min(extraRoads,MeadowMapGenerator.maximumExtraRoads(total:value))
        c.minimumBossHops=min(minimumBossHops,value-1);c.decorationCount=decorationCount
        try c.validate();return c
    }
    /// Field order: combat, boss, reward, empty. Preserve the edited value;
    /// consume empty slots first, then other categories in stable order.
    public func changingCount(field: Int, to value: Int) throws -> Self {
        try validate()
        guard (0...3).contains(field) else { throw GameError("节点分类无效。") }
        var values=[combat,boss,reward,empty]
        values[field]=min(total-1,max(0,value))
        let difference=total-1-values.reduce(0,+)
        if difference>=0 { values[field==3 ? 0:3]+=difference }
        else {
            var remaining = -difference
            for index in [3,0,2,1] where index != field {
                let take=min(values[index],remaining);values[index]-=take;remaining-=take
            }
        }
        var c=self;c.combat=values[0];c.boss=values[1];c.reward=values[2];c.empty=values[3]
        try c.validate();return c
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
    public var nodeID: Int? = nil
}
public struct GeneratedMeadowMap: Codable, Equatable {
    public let generatorVersion: Int
    public let configuration: MeadowMapConfiguration
    public let map: GameMap
    public let roads: [MeadowWorldRoad]
    public let props: [MeadowWorldProp]
    public let coordinateHeight: Double
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
    public static let version = 2
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
            var layout=MapRandom(state:c.seed ^ 0x4c41594f5554 &+ UInt64(attempt))
            let cols=columns(c.total), rows=Int(ceil(Double(c.total)/Double(cols)))
            let coordinateHeight:Double=max(720,440+Double(rows-1)*220)
            let flipX=layout.next() & 1 == 0, flipY=layout.next() & 1 == 0
            let positions=(0..<c.total).map { i -> MeadowWorldPoint in
                let x=100 + Double(i%cols)*1000/Double(max(1,cols-1)) + layout.value(-12,12)
                let y=220 + Double(i/cols)*(coordinateHeight-440)/Double(max(1,rows-1)) + layout.value(-12,12)
                return MeadowWorldPoint(flipX ? 1280-x : x,flipY ? coordinateHeight-y : y)
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
                MapNode(id:id,name:"\(titles[kinds[id]]!) · \(id+1)",kind:kinds[id],x:positions[id].x/1280,y:positions[id].y/coordinateHeight,
                        reward:kinds[id] == .reward ? NodeReward() : nil)
            }
            let map=GameMap(nodes:nodes,roads:tree.map { MapRoad($0.0,$0.1) },seed:c.seed,revealed:[start])
            try map.validate()
            var curves=MapRandom(state:c.seed ^ 0x524f414453)
            let roads=tree.map { a,b -> MeadowWorldRoad in
                let p=positions[a],q=positions[b], dx=q.x-p.x,dy=q.y-p.y, length=hypot(dx,dy)
                let limit=min(18,length*0.06)
                let bend=curves.value(-limit,limit)
                let points=[p,MeadowWorldPoint(p.x+dx/3-dy/length*bend,p.y+dy/3+dx/length*bend),
                            MeadowWorldPoint(p.x+dx*2/3-dy/length*bend,p.y+dy*2/3+dx/length*bend),q]
                return MeadowWorldRoad(from:a,to:b,width:22,points:points)
            }
            guard let props=decorate(c,positions:positions,roads:roads,kinds:kinds,height:coordinateHeight) else { continue }
            return GeneratedMeadowMap(generatorVersion:version,configuration:c,map:map,roads:roads,props:props,coordinateHeight:coordinateHeight,spawn:positions[start])
        }
        throw GameError("在64次尝试内未能满足道路、Boss距离与建筑空间要求。请更换种子或减少环路，节点数量未被修改。")
    }

    public static func distance(_ p: MeadowWorldPoint, to roads: [MeadowWorldRoad]) -> Double {
        roads.flatMap { road in zip(road.points,road.points.dropFirst()).map { a,b -> Double in
            let dx=b.x-a.x,dy=b.y-a.y
            let t=max(0,min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/max(0.001,dx*dx+dy*dy)))
            return hypot(p.x-a.x-t*dx,p.y-a.y-t*dy)
        } }.min() ?? .infinity
    }

    private static func decorate(_ c: MeadowMapConfiguration,positions:[MeadowWorldPoint],roads:[MeadowWorldRoad],kinds:[NodeKind],height:Double) -> [MeadowWorldProp]? {
        var rng=MapRandom(state:c.seed ^ 0x50524f5053), props:[MeadowWorldProp]=[]
        let catalog:[NodeKind:(String,Double)]=[.start:("CampTent",105),.combat:("NodeCombatOutpost",90),.boss:("NodeBossSanctum",104),.reward:("NodeRewardCache",86),.empty:("NodeWaystone",74)]
        // Every node owns one landmark. Reserve both its ground footprint and
        // visible image rectangle; no missing building is silently accepted.
        var options=[[MeadowWorldProp]]()
        for id in positions.indices {
            let node=positions[id],(asset,width)=catalog[kinds[id]]!,radius=width*0.42
            var candidates=[MeadowWorldProp]()
            for offset in [(85.0,-85.0),(-85,-85),(0,-106),(76,-72),(-76,-72),(85,-76),(-85,-76),(92,-92),(-92,-92),(112,-50),(-112,-50),(112,50),(-112,50),(76,72),(-76,72),(85,76),(-85,76),(88,92),(-88,92),(0,110),(120,0),(-120,0),(145,-80),(-145,-80),(145,80),(-145,80),(70,-140),(-70,-140),(70,140),(-70,140)] {
                let p=MeadowWorldPoint(node.x+offset.0,node.y+offset.1)
                guard (width*0.46+10...(1280-width*0.46-10)).contains(p.x),(max(110,width*0.9+35)...(height-15)).contains(p.y),distance(p,to:roads)>max(60,radius+25) else { continue }
                guard positions.allSatisfy({ q in
                    hypot(q.x-p.x,q.y-p.y)>radius+30 &&
                    (q.x+18 < p.x-width*0.46 || q.x-18 > p.x+width*0.46 || q.y+8 < p.y-width*0.86 || q.y-42 > p.y+width*0.06)
                }) else { continue }
                candidates.append(MeadowWorldProp(asset:asset,x:p.x,y:p.y,width:width,wind:0,nodeID:id))
            }
            guard !candidates.isEmpty else { return nil }
            options.append(candidates)
        }
        var assigned=[Int:MeadowWorldProp](),budget=1000
        func fits(_ a:MeadowWorldProp,_ b:MeadowWorldProp) -> Bool {
            if (a.asset=="CampTent" || b.asset=="CampTent") && hypot(a.x-b.x,a.y-b.y)<=150 { return false }
            return abs(a.x-b.x)>(a.width+b.width)*0.5+10 ||
                a.y+a.width*0.08+8 < b.y-b.width*0.92 || b.y+b.width*0.08+8 < a.y-a.width*0.92
        }
        func place() -> Bool {
            if assigned.count==positions.count { return true }
            if budget<=0 { return false }
            var selected = -1, available=[MeadowWorldProp]()
            // Place the most constrained parcel first, instead of letting an
            // early flexible parcel occupy the only slot of a later building.
            for id in positions.indices where assigned[id]==nil {
                let valid=options[id].filter { candidate in assigned.values.allSatisfy{fits(candidate,$0)} }
                if valid.isEmpty { return false }
                if selected<0 || valid.count<available.count { selected=id;available=valid }
            }
            for candidate in available {
                budget-=1;assigned[selected]=candidate
                if place() { return true }
                assigned.removeValue(forKey:selected)
                if budget<=0 { return false }
            }
            return false
        }
        guard place() else { return nil }
        props=positions.indices.map{assigned[$0]!}
        let landmarkCount=props.count
        let assets=["OakA","OakB","Pines","RockLow","RockHigh","RockSmall","Shrub","Flowers"]
        for _ in 0..<1400 {
            if props.count>=c.decorationCount+landmarkCount { break }
            let p=MeadowWorldPoint(rng.value(-70,1350),rng.value(-80,height+100))
            guard distance(p,to:roads)>58,
                  positions.allSatisfy({hypot($0.x-p.x,$0.y-p.y)>76}),
                  props.allSatisfy({hypot($0.x-p.x,$0.y-p.y)>($0.nodeID != nil ? ($0.asset == "CampTent" ? 150 : 110) : max(42,$0.width*0.6))}) else { continue }
            let asset=assets[Int(rng.next()%UInt64(assets.count))]
            let width=asset=="Flowers" ? rng.value(14,23) : asset=="Shrub" ? rng.value(25,35) : (asset.hasPrefix("Rock") ? rng.value(76,108) : rng.value(60,88))
            props.append(MeadowWorldProp(asset:asset,x:p.x,y:p.y,width:width,wind:asset.hasPrefix("Rock") ? 0 : 1))
        }
        return props
    }
}
