import Foundation

public struct BowPartPose:Codable {
    public let pivot:PartyPoint,offset:PartyPoint
    public let rotation:Double
    public init(_ pivot:PartyPoint,_ moved:PartyPoint,_ rotation:Double) { self.pivot=pivot;offset=PartyPoint(moved.x-pivot.x,moved.y-pivot.y);self.rotation=rotation }
}
public struct BowRigSample:Codable {
    public let parts:[String:BowPartPose]
    public let upperTip:PartyPoint,lowerTip:PartyPoint,stringHand:PartyPoint
    public let arrowTail:PartyPoint,arrowTip:PartyPoint
    public let arrowVisible:Bool
    public let arrowAlpha:Double
}
public struct BowProjectile:Codable {
    public let tail:PartyPoint,tip:PartyPoint,alpha:Double
}
/// Registered arm bones and separate bow/string; reused art never stretches.
public enum BowRig {
    public static let releaseAge=0.86
    public static let releaseProgress=(releaseAge-0.4)/1.2
    static func mix(_ a:Double,_ b:Double,_ t:Double)->Double { a+(b-a)*t }
    static func blend(_ a:PartyPoint,_ b:PartyPoint,_ t:Double)->PartyPoint { PartyPoint(mix(a.x,b.x,t),mix(a.y,b.y,t)) }
    public static func sample(clip:String,progress:Double,lean:Double=0,crouch:Double=0)->BowRigSample {
        let p=min(1,max(0,progress)),attack=clip=="attack"
        let aim=attack ? PartyVisual.smooth(p/0.25)*(1-PartyVisual.smooth((p-0.68)/0.32)):0
        let pull=attack ? PartyVisual.smooth((p-0.18)/0.16)*(1-PartyVisual.smooth((p-releaseProgress)/0.055)):0
        let handPull=attack ? PartyVisual.smooth((p-0.18)/0.16)*(1-PartyVisual.smooth((p-releaseProgress-0.03)/0.15)):0
        let recoil=attack && p>=releaseProgress ? sin((p-releaseProgress)*100)*exp(-(p-releaseProgress)*45)*1.3:0
        func body(_ q:PartyPoint)->PartyPoint {
            let dx=q.x-132,dy=q.y-167,c=cos(lean),s=sin(lean)
            return PartyPoint(132+dx*c-dy*s,167+dx*s+dy*c+crouch)
        }
        let near=blend(PartyPoint(145.6,163.7),PartyPoint(154,138),aim)
        let far=blend(PartyPoint(108,173),PartyPoint(mix(145,132,handPull),138),aim)
        var parts:[String:BowPartPose]=[:]
        func arm(prefix:String,shoulder:PartyPoint,hand:PartyPoint,bend:Double) {
            let upper:Double=hypot(11.0,17.0),fore:Double=hypot(17.6,5.7)
            let dx=hand.x-shoulder.x,dy=hand.y-shoulder.y,dist=min(upper+fore-0.001,max(abs(upper-fore)+0.001,hypot(dx,dy)))
            let cosine:Double=(upper*upper+dist*dist-fore*fore)/(2*upper*dist)
            let a:Double=atan2(dy,dx)+bend*acos(min(1.0,max(-1.0,cosine)))
            let elbow=PartyPoint(shoulder.x+upper*cos(a),shoulder.y+upper*sin(a))
            let upperAngle=a-atan2(17.0,11.0),foreAngle=atan2(hand.y-elbow.y,hand.x-elbow.x)-atan2(5.7,17.6)
            parts[prefix+"Upper"]=BowPartPose(PartyPoint(117,141),body(shoulder),lean+upperAngle)
            parts[prefix+"Fore"]=BowPartPose(PartyPoint(128,158),body(elbow),lean+foreAngle)
            parts[prefix+"Hand"]=BowPartPose(PartyPoint(145.6,163.7),body(hand),lean+(prefix=="near" ? -aim*0.16:foreAngle))
        }
        arm(prefix:"near",shoulder:PartyPoint(117,141),hand:near,bend:1)
        arm(prefix:"far",shoulder:PartyPoint(128,141),hand:far,bend:1)
        parts["bow"]=BowPartPose(PartyPoint(145.6,163.7),body(near),lean+0.45)
        func limb(_ y:Double)->PartyPoint { let c=cos(0.45),s=sin(0.45);return body(PartyPoint(near.x-10*c-y*s,near.y-10*s+y*c)) }
        return BowRigSample(parts:parts,upperTip:limb(-36),lowerTip:limb(36),stringHand:body(PartyPoint(near.x-10-13*pull+recoil,near.y)),arrowTail:body(PartyPoint(near.x-10-13*pull,near.y-1)),arrowTip:body(PartyPoint(near.x+26,near.y-1)),arrowVisible:attack && p>0.06 && p<releaseProgress,arrowAlpha:PartyVisual.smooth((p-0.06)/0.06))
    }
    /// The projectile ends at the same point and time used by the atomic hit.
    public static func projectile(age:Double,from:PartyPoint,to:PartyPoint,impact:Double)->BowProjectile? {
        guard age>=releaseAge,age<impact else { return nil }
        let t=(age-releaseAge)/(impact-releaseAge),tip=blend(from,to,t)
        let dx=to.x-from.x,dy=to.y-from.y,length=max(1,hypot(dx,dy)),span=38.0
        return BowProjectile(tail:PartyPoint(tip.x-dx/length*span,tip.y-dy/length*span),tip:tip,alpha:1)
    }
}
