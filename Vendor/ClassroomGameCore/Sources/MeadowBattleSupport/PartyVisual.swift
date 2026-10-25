import Foundation
import ClassroomGameCore
public struct PartyPoint:Codable { public var x:Double;public var y:Double;public init(_ x:Double,_ y:Double) { self.x=x;self.y=y } }
public struct PartyParticle:Codable {
    public let id:Int;public let x:Double;public let y:Double;public let size:Double;public let alpha:Double;public let angle:Double
}
public enum PartyVisual {
    public static let width=1000.0,height=600.0,heroScale=0.83,enemyScale=0.82
    public static let feet:[String:PartyPoint]=["p1":PartyPoint(165,420),"p2":PartyPoint(315,505),"m1":PartyPoint(650,395),"m2":PartyPoint(835,510)]
    public static func smooth(_ x:Double)->Double { let t=min(1,max(0,x));return t*t*(3-2*t) }
    public static func pulse(_ age:Double,_ start:Double,_ peak:Double,_ end:Double)->Double { age<peak ? smooth((age-start)/(peak-start)):1-smooth((age-peak)/(end-peak)) }
    public static func chest(_ id:String)->PartyPoint { let p=feet[id]!;return PartyPoint(p.x+5*heroScale,p.y-70*heroScale) }
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
    public static func travel(_ intent:PartyIntent?,age:Double,shielded:Bool=false)->PartyPoint {
        guard let intent,intent.action.visual=="attack",let from=feet[intent.actor],let to=feet[intent.target] else { return PartyPoint(0,0) }
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
            if intent.action.visual=="attack" {
                clip="attack";let action=max(0,age-0.4);progress=min(1,max(0,action-min(0.1,max(0,action-0.648)))/1.2)
            } else if ["support","rally","guard"].contains(intent.action.visual) { clip="guard";progress=min(1,age/1.4) }
        }
        if let intent,intent.action == .revivalStone,intent.target==unit.id,age>=intent.action.impact { clip="defeat";progress=1-smooth((age-intent.action.impact)/0.6) }
        if let hurtAge,hurtAge<0.7,unit.isAlive { clip=blocked ? "guard":"hit";progress=min(1,hurtAge/0.7) }
        return PartyActorPose(clip:clip,progress:progress)
    }
}
