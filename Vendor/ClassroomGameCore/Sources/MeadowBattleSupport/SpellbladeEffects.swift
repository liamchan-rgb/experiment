import Foundation
import ClassroomGameCore

public struct RuneStroke:Codable { public let points:[PartyPoint];public let width:Double,alpha:Double;public let color:String }
public struct RuneGlow:Codable { public let point:PartyPoint;public let rx:Double,ry:Double,alpha:Double;public let color:String }
public struct RuneMote:Codable { public let id:Int;public let point:PartyPoint;public let size:Double,angle:Double,alpha:Double;public let color:String;public let groundAge:Double?;public let ground:PartyPoint }
public struct RuneEffectSample:Codable { public var strokes:[RuneStroke]=[];public var glows:[RuneGlow]=[];public var motes:[RuneMote]=[];public init() {} }
public struct RuneRecipient:Codable,Equatable { public let unitID:String;public var heal:Int=0,shield:Int=0,buff:Int=0 }

/// Catalog scopes, rather than the clicked target, own each effect channel.
public enum SpellbladeEffects {
    public static func recipients(_ intent:PartyIntent,catalog:GameCatalog)->[RuneRecipient] {
        guard intent.action.isRune,let skill=try? catalog.skill(intent.action.rawValue) else { return [] }
        var values:[String:RuneRecipient]=[:]
        for effect in skill.effects where effect.kind != .damage {
            let ids=effect.scope == .caster ? [intent.actor]:intent.targets
            for id in ids {
                var v=values[id] ?? RuneRecipient(unitID:id)
                switch effect.kind { case .heal:v.heal=max(v.heal,effect.amount);case .shield:v.shield=max(v.shield,effect.amount);case .damageBuff:v.buff=max(v.buff,effect.amount);default:break }
                values[id]=v
            }
        }
        return values.values.sorted { $0.unitID<$1.unitID }
    }
    /// Healing4 is the established baseline; stronger healing thickens the helix.
    public static func healingStrength(_ amount:Int)->Double { min(2.2,max(1,sqrt(Double(max(4,amount))/4))) }
    public static func darkness(_ action:PartyAction,age:Double,from:Double)->Double {
        let peak=BattleDice.darkness(action),hold=action.impact+0.28
        return (from+(peak-from)*PartyVisual.smooth(age/0.30))*(1-PartyVisual.smooth((age-hold)/0.78))
    }
    public static func sample(action:PartyAction,age:Double,actor:String,target:String,recipients:[RuneRecipient],weaponID:String?=nil)->RuneEffectSample {
        var result=RuneEffectSample()
        guard action.isRune,age>=0,age<action.duration,let actorFoot=PartyVisual.feet[actor],let targetFoot=PartyVisual.feet[target] else { return result }
        let hit=action.impact,at=PartyVisual.hitPoint(target:target,weaponID:weaponID),source=PartyPoint(actorFoot.x+42,actorFoot.y-73)
        func stroke(_ points:[PartyPoint],_ width:Double,_ alpha:Double,_ color:String) { if alpha>0.00001 { result.strokes.append(.init(points:points,width:width,alpha:min(1,alpha),color:color)) } }
        func glow(_ p:PartyPoint,_ rx:Double,_ ry:Double,_ alpha:Double,_ color:String) { if alpha>0.00001 { result.glows.append(.init(point:p,rx:rx,ry:ry,alpha:min(1,alpha),color:color)) } }
        func rune(_ p:PartyPoint,_ radius:Double,_ angle:Double,_ alpha:Double,_ color:String,_ index:Int) {
            let local:[PartyPoint]=index%3==0 ? [.init(-0.4,-0.8),.init(0.4,0),.init(-0.4,0.8),.init(0,0),.init(-0.4,-0.8)]:index%3==1 ? [.init(-0.5,-0.8),.init(0.5,-0.25),.init(-0.3,0.1),.init(0.5,0.8)]:[.init(-0.6,0.6),.init(0,-0.8),.init(0.6,0.6),.init(-0.6,0.6)]
            let points=local.map { v in PartyPoint(p.x+(v.x*cos(angle)-v.y*sin(angle))*radius,p.y+(v.x*sin(angle)+v.y*cos(angle))*radius) }
            stroke(points,2.6,alpha,color)
        }
        func seal(_ p:PartyPoint,_ radius:Double,_ turn:Double,_ alpha:Double,_ color:String,_ split:Double=0) {
            for side in 0..<2 {
                let points=(0...32).map { i -> PartyPoint in
                    let a=turn+Double(side)*Double.pi+Double(i)/32*Double.pi
                    return .init(p.x+cos(a)*radius+(side==0 ? split:-split),p.y+sin(a)*radius*0.86)
                }
                stroke(points,3.0,alpha*0.70,color)
            }
            for i in 0..<8 {
                let a=turn+Double(i)*Double.pi/4
                rune(.init(p.x+cos(a)*radius*0.74,p.y+sin(a)*radius*0.65),9,a+Double.pi/2,alpha,color,i)
            }
        }
        if action == .runeSlash {
            let build=PartyVisual.smooth(age/(hit*0.80)),shatter=PartyVisual.smooth((age-hit)/0.32)
            let sealAlpha=PartyVisual.smooth(age/0.22)*(1-PartyVisual.smooth((age-hit)/0.38))
            seal(at,42+38*build,0.45*(1-build),sealAlpha*0.88,"violet",shatter*45)
            glow(at,100,100,sealAlpha*0.12,"violet")
            let charge=PartyVisual.pulse(age,0,0.54,hit+0.05)
            seal(source,18+charge*9,-age*0.8,charge*0.65,"cyan")
            glow(source,44,38,charge*0.30,"cyan")
            let flight=(age-0.60)/(hit-0.60)
            if flight>=0,flight<=1 {
                let p=PartyVisual.beam(source,at,flight),trail=(0...16).map { i in PartyVisual.beam(source,at,max(0,flight-0.18+Double(i)/16*0.18)) }
                stroke(trail,6,sin(Double.pi*flight)*0.55,"violet");stroke(trail,1.8,sin(Double.pi*flight)*0.95,"white")
                rune(p,11,flight*2,sin(Double.pi*flight),"cyan",1)
            }
            for side in 0..<2 {
                let t=age-hit-Double(side)*0.075
                let a=PartyVisual.pulse(t,0,0.045,0.57),head=min(1,max(0,t/0.16)),tail=min(1,max(0,(t-0.10)/0.37))
                let points=(0...36).map { i -> PartyPoint in
                    let u=tail+(head-tail)*Double(i)/36
                    return .init(at.x-92+184*u,at.y+(side==0 ? 1:-1)*(87-174*u)+sin(Double.pi*u)*18)
                }
                stroke(points,15,a*0.28,"violet");stroke(points,6,a*0.82,"cyan");stroke(points,2.2,a,"white")
            }
            let burst=PartyVisual.pulse(age,hit,hit+0.045,hit+0.64)
            glow(at,155,145,burst*0.53,"violet");glow(at,55,50,burst*0.75,"white")
            glow(targetFoot,175,29,burst*0.72,"cyan")
            for i in 0..<32 {
                let t=age-hit-Double(i%4)*0.012,life=1.45+Double(i%4)*0.12
                guard t>0,t<life else { continue }
                let vx=(i%2==0 ? 1.0:-1.0)*(42+Double(i%7)*16),vy = -90.0-Double(i%6)*19,g=340.0
                let floor=targetFoot.y-2,contact=(-vy+sqrt(vy*vy+2*g*(floor-at.y)))/g
                let tau=max(0,t-contact),rawY=at.y+vy*t+0.5*g*t*t
                let y=t<contact ? rawY:min(floor,floor-(vy+g*contact)*0.32*tau+0.5*g*tau*tau)
                let p=PartyPoint(at.x+vx*t,y),a=PartyVisual.smooth(t/0.055)*(1-PartyVisual.smooth((t-life*0.48)/(life*0.52)))
                result.motes.append(.init(id:i,point:p,size:i%5==0 ? 10:5,angle:Double(i)*2.399+t*3,alpha:a,color:i%3==0 ? "gold":"cyan",groundAge:t>=contact ? tau:nil,ground:.init(at.x+vx*contact,floor)))
            }
        } else {
            let isWard=action == .runeWard,color=isWard ? "cyan":"gold"
            for (index,v) in recipients.enumerated() {
                guard let foot=PartyVisual.feet[v.unitID] else { continue }
                let chest=PartyPoint(foot.x+5,foot.y-69),build=PartyVisual.smooth(age/hit)
                let opacity=PartyVisual.smooth(age/0.25)*(1-PartyVisual.smooth((age-hit-0.18)/0.85))
                let radius=(isWard ? 42.0:33.0)+(isWard ? 20.0:17.0)*build
                seal(chest,radius,-age*0.75+Double(index)*0.4,opacity*0.68,color)
                if isWard {
                    let diamond=[PartyPoint(chest.x,chest.y-radius*0.8),.init(chest.x+radius*0.63,chest.y),.init(chest.x,chest.y+radius*0.8),.init(chest.x-radius*0.63,chest.y),.init(chest.x,chest.y-radius*0.8)]
                    stroke(diamond,2.2,opacity*0.65,"gold")
                } else {
                    for sign in [-1.0,1.0] {
                        let rise=PartyVisual.smooth((age-0.12)/0.74),p=PartyPoint(chest.x+sign*(48-28*rise),chest.y+26-63*rise)
                        rune(p,19,-sign*age*0.5,opacity,"gold",2)
                    }
                }
                glow(chest,72,100,opacity*0.16,color)
                let contact=PartyVisual.pulse(age,hit,hit+0.06,hit+0.70)
                glow(foot,110,23,contact*0.54,color)
                if v.unitID != actor {
                    let end=PartyPoint(foot.x,foot.y-70),alpha=PartyVisual.pulse(age,0.10,hit*0.65,hit+0.35)
                    stroke((0...40).map { PartyVisual.beam(source,end,Double($0)/40) },2,alpha*0.58,color)
                }
                for i in 0..<22 {
                    let t=age-hit-Double(i%6)*0.025,life=1.15+Double(i%4)*0.09
                    guard t>0,t<life else { continue }
                    let u=t/life,a=Double(i)*2.399+u*2.8,r=(isWard ? 42.0:30.0)*(1-u*0.35),p=PartyPoint(chest.x+cos(a)*r,chest.y+40-u*135)
                    result.motes.append(.init(id:100+index*30+i,point:p,size:i%5==0 ? 8:4,angle:a,alpha:sin(Double.pi*u)*0.88,color:i%4==0 ? "gold":color,groundAge:nil,ground:foot))
                }
            }
        }
        return result
    }
}
