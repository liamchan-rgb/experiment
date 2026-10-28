import Foundation
import ClassroomGameCore
public struct PartyPoint:Codable { public var x:Double;public var y:Double;public init(_ x:Double,_ y:Double) { self.x=x;self.y=y } }
public struct PartyParticle:Codable {
    public let id:Int;public let x:Double;public let y:Double;public let size:Double;public let alpha:Double;public let angle:Double
}
public struct PartyAfterimage:Codable { public let offset:PartyPoint;public let progress:Double;public let alpha:Double }
public struct PartySlash:Codable { public let points:[PartyPoint];public let alpha:Double }
public enum PartyVisual {
    public static let width=1000.0,height=600.0,heroScale=0.83,enemyScale=0.82
    public static let feet:[String:PartyPoint]=["p1":PartyPoint(165,420),"p2":PartyPoint(315,505),"m1":PartyPoint(650,395),"m2":PartyPoint(835,510)]
    public static func smooth(_ x:Double)->Double { let t=min(1,max(0,x));return t*t*(3-2*t) }
    public static func pulse(_ age:Double,_ start:Double,_ peak:Double,_ end:Double)->Double { age<peak ? smooth((age-start)/(peak-start)):1-smooth((age-peak)/(end-peak)) }
    public static func chest(_ id:String)->PartyPoint { let p=feet[id]!;return PartyPoint(p.x+5*heroScale,p.y-70*heroScale) }
    public static func hitPoint(target:String,shielded:Bool=false)->PartyPoint {
        let foot=feet[target]!
        return PartyPoint(foot.x+(target.hasPrefix("m") ? -80:shielded ? (5+240*0.41)*heroScale:10),foot.y-(target.hasPrefix("m") ? 72:65))
    }
    public static func damageLabelOrigin(at:PartyPoint,width:Double,height:Double,age:Double)->PartyPoint {
        PartyPoint(at.x-width/2,at.y-height/2-max(0,age)*26)
    }
    public static func beam(_ from:PartyPoint,_ to:PartyPoint,_ t:Double)->PartyPoint {
        let u=1-t;return PartyPoint(u*u*from.x+2*u*t*((from.x+to.x)/2)+t*t*to.x,u*u*from.y+2*u*t*(min(from.y,to.y)-90)+t*t*to.y)
    }
    public static func trail(age:Double,from:PartyPoint,to:PartyPoint)->[PartyParticle] {
        guard age>=0,age<1.65 else { return [] }
        return (0..<28).compactMap { i in
            let delay=Double(i)*0.018;let t=(age-delay)/0.55
            guard t>=0,t<=1 else { return nil };let p=beam(from,to,t)
            return PartyParticle(id:i,x:p.x,y:p.y+sin(Double(i)*2.399+t*7)*4,size:i%5==0 ? 11:5,alpha:sin(Double.pi*t)*0.95,angle:t*3+Double(i))
        }
    }
    public static func rally(age:Double,at:PartyPoint)->[PartyParticle] {
        guard age>=0,age<1.8 else { return [] }
        return (0..<22).compactMap { i in
            let local=age-Double(i%6)*0.045
            guard local>=0,local<1.35 else { return nil }
            let t=local/1.35;let angle=Double(i)*2.399
            return PartyParticle(id:i,x:at.x+cos(angle)*(24+13*t),y:at.y+30-t*125,size:Double(i%4==0 ? 12:6),alpha:sin(Double.pi*t)*0.9,angle:-Double.pi/2)
        }
    }
    public static func ambushProgress(_ age:Double)->Double {
        if age<0.24 { return 0.18*smooth(age/0.24) }
        if age<0.72 { return 0.18+0.36*smooth((age-0.24)/0.48) }
        if age<0.84 { return 0.54+0.10*smooth((age-0.72)/0.12) }
        return 0.64+0.36*smooth((age-0.84)/0.58)
    }
    public static func afterimages(_ intent:PartyIntent?,age:Double)->[PartyAfterimage] {
        guard let intent,intent.action == .ambush,age>=0.22,age<1.0 else { return [] }
        return (1...3).map { i in
            let past=max(0,age-Double(i)*0.065)
            return PartyAfterimage(offset:travel(intent,age:past),progress:ambushProgress(past),alpha:pulse(age,0.22,0.48,1.0)*(0.26-Double(i)*0.045))
        }
    }
    /// Two visual strokes, one atomic hit. Sweep heads and tails continuously.
    public static func ambushSlashes(age:Double,at:PartyPoint)->[PartySlash] {
        (0..<2).compactMap { i in
            let local=age-0.72-Double(i)*0.065
            guard local>=0,local<0.42 else { return nil }
            let head=min(1,local/0.16),tail=max(0,(local-0.10)/0.32),alpha=pulse(local,0,0.035,0.42)
            let points=(0...24).map { j -> PartyPoint in
                let t=tail+(head-tail)*Double(j)/24,x = -72+144*t
                return PartyPoint(at.x+x,at.y+(i==0 ? 1.0:-1.0)*(62-124*t)+sin(Double.pi*t)*20)
            }
            return PartySlash(points:points,alpha:alpha)
        }
    }
    public static func travel(_ intent:PartyIntent?,age:Double,shielded:Bool=false)->PartyPoint {
        guard let intent,intent.action.isOffensive,let from=feet[intent.actor],let to=feet[intent.target] else { return PartyPoint(0,0) }
        if intent.ranged { return PartyPoint(0,0) }
        if intent.action == .ambush {
            let p=age<0.72 ? smooth((age-0.22)/0.50):1-smooth((age-0.84)/0.58)
            return PartyPoint((to.x-140-from.x)*p,(to.y-12-from.y)*p)
        }
        let t=intent.enemy ? age/0.96 : max(0,age-0.4-min(0.1,max(0,age-1.048)))/1.2
        let p=t<0.4 ? smooth((t-0.12)/0.28) : t<0.66 ? 1:1-smooth((t-0.66)/0.34)
        if intent.enemy { let move=pulse(age,0.08,0.46,0.96);return PartyPoint((to.x+(178.5-42)*enemyScale+(shielded ? (5+240*0.41)*heroScale:0)-from.x)*move,(to.y-from.y)*move) }
        return PartyPoint((to.x-140-from.x)*p,(to.y-12-from.y)*p)
    }
}

public struct PartyActorPose:Codable { public let clip:String;public let progress:Double }
extension PartyVisual {
    public static func pose(unit:GameUnit,intent:PartyIntent?,age:Double,time:Double,hurtAge:Double?=nil,blocked:Bool=false,downAge:Double?=nil)->PartyActorPose {
        var clip=unit.isAlive ? "idle":"defeat"
        var progress=unit.isAlive ? time.truncatingRemainder(dividingBy:2.4)/2.4:(downAge.map { smooth($0/0.6) } ?? 1)
        if let intent,intent.actor==unit.id,unit.isAlive {
            if intent.action == .ambush {
                clip="attack";progress=ambushProgress(age)
            } else if intent.action.visual=="attack" {
                clip="attack"
                if intent.ranged && unit.equipment.weapon=="huntingBow" { progress=BowRig.progress(age:age) }
                else { let action=max(0,age-0.4);progress=min(1,max(0,action-min(0.1,max(0,action-0.648)))/1.2) }
            } else if ["support","rally","guard"].contains(intent.action.visual) { clip="guard";progress=min(1,age/1.4) }
        }
        if let intent,intent.action == .revivalStone,intent.target==unit.id,age>=intent.action.impact { clip="defeat";progress=1-smooth((age-intent.action.impact)/0.6) }
        if let hurtAge,hurtAge<0.7,unit.isAlive { clip=blocked ? "guard":"hit";progress=min(1,hurtAge/0.7) }
        return PartyActorPose(clip:clip,progress:progress)
    }
}
