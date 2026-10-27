import Foundation

public struct BowPartPose:Codable {
    public let pivot:PartyPoint,offset:PartyPoint
    public let rotation:Double
    public init(_ pivot:PartyPoint,_ moved:PartyPoint,_ rotation:Double) { self.pivot=pivot;offset=PartyPoint(moved.x-pivot.x,moved.y-pivot.y);self.rotation=rotation }
}
/// Native-pixel polygon surfaces; both UIKit and the offline renderer paint these.
public struct BowSurface:Codable {
    public let group:String,color:UInt32,points:[PartyPoint]
}
public struct BowRigSample:Codable {
    public let surfaces:[BowSurface]
    public let parts:[String:BowPartPose]
    public let upperTip:PartyPoint,lowerTip:PartyPoint,stringHand:PartyPoint
    public let arrowTail:PartyPoint,arrowTip:PartyPoint
    public let arrowVisible:Bool
    public let arrowAlpha:Double
}
public struct BowProjectile:Codable {
    public let tail:PartyPoint,tip:PartyPoint,alpha:Double
}
/// Bow-specific continuous sleeve meshes, distinct hand roles, separate bow/string.
public enum BowRig {
    public static let releaseAge=0.86
    public static let releaseProgress=(releaseAge-0.4)/1.2
    static func mix(_ a:Double,_ b:Double,_ t:Double)->Double { a+(b-a)*t }
    static func blend(_ a:PartyPoint,_ b:PartyPoint,_ t:Double)->PartyPoint { PartyPoint(mix(a.x,b.x,t),mix(a.y,b.y,t)) }
    public static func sample(clip:String,progress:Double,lean:Double=0,crouch:Double=0)->BowRigSample {
        let p=min(1,max(0,progress)),attack=clip=="attack"
        let aim=attack ? PartyVisual.smooth(p/0.19)*(1-PartyVisual.smooth((p-0.65)/0.35)):0
        let draw=attack ? PartyVisual.smooth((p-0.19)/0.14):0
        let follow=attack ? PartyVisual.smooth((p-releaseProgress)/0.09)*(1-PartyVisual.smooth((p-0.55)/0.20)):0
        let recoil=attack && p>=releaseProgress ? sin((p-releaseProgress)*100)*exp(-(p-releaseProgress)*45)*0.8:0
        func body(_ q:PartyPoint)->PartyPoint {
            let dx=q.x-132,dy=q.y-167,c=cos(lean),s=sin(lean)
            return PartyPoint(132+dx*c-dy*s,167+dx*s+dy*c+crouch)
        }
        // Pose A: the FAR arm holds the bow, the NEAR arm draws toward the cheek.
        // These are authored bow sleeves, not rotated cutouts of the sword arm.
        let grip=blend(PartyPoint(163,165),PartyPoint(174,144),aim)
        let angle=mix(0.18,0,aim)
        let nearShoulder=PartyPoint(129,150)
        let farShoulder=PartyPoint(136,141)
        func elbow(_ shoulder:PartyPoint,_ hand:PartyPoint,upper:Double=20,fore:Double=19,bend:Double=1)->PartyPoint {
            let dx=hand.x-shoulder.x,dy=hand.y-shoulder.y
            let dist=min(upper+fore-0.001,max(abs(upper-fore)+1e-10,hypot(dx,dy)))
            let a=atan2(dy,dx)+bend*acos(min(1,max(-1,(upper*upper+dist*dist-fore*fore)/(2*upper*dist))))
            return PartyPoint(shoulder.x+upper*cos(a),shoulder.y+upper*sin(a))
        }
        func angles(_ hand:PartyPoint,_ bend:Double)->(Double,Double) {
            let el=elbow(nearShoulder,hand,upper:22,fore:34,bend:bend)
            return (atan2(el.y-nearShoulder.y,el.x-nearShoulder.x),atan2(hand.y-el.y,hand.x-el.x))
        }
        let rest=angles(PartyPoint(142,156),1),reach=angles(PartyPoint(164,134),-1),full=angles(PartyPoint(143,134),-1),after=angles(PartyPoint(140,134),-1)
        let lift=attack ? PartyVisual.smooth(p/0.19):0
        let retire=attack ? PartyVisual.smooth((p-0.65)/0.35):0
        func angleBlend(_ a:Double,_ b:Double,_ t:Double)->Double { a+atan2(sin(b-a),cos(b-a))*t }
        func joint(_ r:Double,_ a:Double,_ b:Double,_ c:Double)->Double {
            let raised=angleBlend(r,a,lift),pulled=angleBlend(raised,b,draw),released=angleBlend(pulled,c,follow)
            return angleBlend(released,r,retire)
        }
        // Interpolate joint angles, not wrist positions: the elbow follows a
        // continuous arc and both bone lengths stay constant during approach.
        let ua=joint(rest.0,reach.0,full.0,after.0),fa=joint(rest.1,reach.1,full.1,after.1)
        let nearElbow=PartyPoint(nearShoulder.x+22*cos(ua),nearShoulder.y+22*sin(ua))
        let near=PartyPoint(nearElbow.x+34*cos(fa),nearElbow.y+34*sin(fa))
        let straight=PartyPoint(grip.x-10+recoil,grip.y-10)
        let engaged=attack && p>=0.19 && p<=releaseProgress
        let spring=attack ? PartyVisual.smooth((p-releaseProgress)/0.055):1
        let nock = !attack || p<0.19 ? straight:engaged ? near:blend(near,straight,spring)
        let tail=engaged ? near:straight
        let farElbow=elbow(farShoulder,grip)
        var parts:[String:BowPartPose]=[:]
        for (prefix,sh,el,hand) in [("near",nearShoulder,nearElbow,near),("far",farShoulder,farElbow,grip)] {
            parts[prefix+"Upper"]=BowPartPose(sh,body(sh),lean+atan2(el.y-sh.y,el.x-sh.x))
            parts[prefix+"Fore"]=BowPartPose(el,body(el),lean+atan2(hand.y-el.y,hand.x-el.x))
            parts[prefix+"Hand"]=BowPartPose(PartyPoint(145.6,163.7),body(hand),lean)
        }
        parts["torso"]=BowPartPose(PartyPoint(132,167),PartyPoint(132,167+crouch),lean)
        parts["bow"]=BowPartPose(PartyPoint(145.6,163.7),body(grip),lean+angle)
        var surfaces:[BowSurface]=[]
        func polygon(_ group:String,_ color:UInt32,_ points:[PartyPoint]) {
            surfaces.append(BowSurface(group:group,color:color,points:points.map { q in let v=body(q);return PartyPoint(v.x.rounded(),v.y.rounded()) }))
        }
        func disc(_ group:String,_ color:UInt32,_ q:PartyPoint,_ r:Double) {
            polygon(group,color,(0..<8).map { i in let a=Double(i)*Double.pi/4;return PartyPoint(q.x+cos(a)*r,q.y+sin(a)*r) })
        }
        func strip(_ group:String,_ color:UInt32,_ a:PartyPoint,_ b:PartyPoint,_ ra:Double,_ rb:Double,_ shift:Double=0) {
            let dx=b.x-a.x,dy=b.y-a.y,l=max(0.01,hypot(dx,dy)),nx = -dy/l,ny=dx/l
            polygon(group,color,[PartyPoint(a.x+nx*(ra+shift),a.y+ny*(ra+shift)),PartyPoint(b.x+nx*(rb+shift),b.y+ny*(rb+shift)),PartyPoint(b.x+nx*(-rb+shift),b.y+ny*(-rb+shift)),PartyPoint(a.x+nx*(-ra+shift),a.y+ny*(-ra+shift))])
        }
        func sleeve(_ group:String,_ sh:PartyPoint,_ el:PartyPoint,_ wrist:PartyPoint,_ far:Bool) {
            let dx=wrist.x-el.x,dy=wrist.y-el.y,l=max(1,hypot(dx,dy))
            let cuff=PartyPoint(wrist.x-dx/l*5,wrist.y-dy/l*5)
            let outer:UInt32=0x192a3d,base:UInt32=far ? 0x294b77:0x3865a0,light:UInt32=far ? 0x365c8a:0x497bb6,shade:UInt32=far ? 0x213b61:0x274a7d
            // Paint one continuous outline, then all fills, so no joint seam.
            strip(group,outer,sh,el,6,6);disc(group,outer,el,6)
            strip(group,outer,el,cuff,6,4.5);disc(group,outer,sh,6)
            strip(group,base,sh,el,5,5);disc(group,base,el,5)
            strip(group,base,el,cuff,5,3.5);disc(group,base,sh,5)
            strip(group,shade,sh,el,1.3,1.3,3.5);strip(group,shade,el,cuff,1,1,3)
            strip(group,light,blend(sh,el,0.35),blend(sh,el,0.80),0.8,0.8,-2.5)
            strip(group,light,el,blend(el,cuff,0.85),1,0.8,-2.2)
            strip(group,outer,cuff,wrist,4.8,4.8)
            strip(group,0xc9b781,blend(cuff,wrist,0.14),wrist,3.7,3.7)
            strip(group,0xf0e4b6,blend(cuff,wrist,0.14),wrist,1.1,1.1,-2)
        }
        func hand(_ group:String,_ q:PartyPoint,_ holding:Bool) {
            func poly(_ color:UInt32,_ pairs:[(Double,Double)]) { polygon(group,color,pairs.map { PartyPoint(q.x+$0.0,q.y+$0.1) }) }
            poly(0x55301e,[(-4,-5),(3,-5),(5,-3),(5,5),(2,7),(-4,5),(-5,1)])
            poly(0xf3b27b,[(-3,-4),(2,-4),(4,-2),(4,4),(1,5),(-3,4),(-4,0)])
            poly(0xffcd99,[(-3,-3),(1,-3),(2,-1),(-1,0),(-3,2)])
            if holding {
                poly(0x98502c,[(0,-2),(4,-2),(4,-1),(0,-1)])
                poly(0xb46c3d,[(0,1),(4,1),(4,2),(0,2)])
                poly(0xffcf9a,[(-4,-2),(-2,-2),(0,1),(-1,3),(-3,2)])
            } else {
                poly(0xb46c3d,[(1,-2),(4,-2),(4,-1),(1,-1)])
                poly(0xd58b53,[(1,1),(4,1),(4,2),(1,2)])
            }
        }
        // Reconstruct the cloth concealed by the old sword sleeve. Original
        // collar and waist pixels are composited above this panel by both views.
        polygon("torso",0x1c3047,[(116.0,137.0),(129,137),(144,144),(145,165),(135,171),(112,165),(113,148)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x315b94,[(117.0,138.0),(129,139),(143,145),(143,164),(134,169),(114,164),(115,148)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x284b7c,[(115.0,145.0),(122,148),(121,160),(130,166),(115,164)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x3d6ca6,[(124.0,141.0),(131,142),(139,147),(138,160),(131,159),(125,151)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x4474ae,[(126.0,143.0),(129,143),(134,146),(132,150),(128,148)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x1f375e,[(141.0,148.0),(144,148),(144,164),(141,164)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0xd4bd80,[(140.0,150.0),(142,150),(142,165),(140,166)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0xf3e6b4,[(140.0,151.0),(141,151),(141,164),(140,164)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x244474,[(123.0,157.0),(128,159),(129,161),(124,160)].map { PartyPoint($0.0,$0.1) })
        polygon("torso",0x3e6ba3,[(128.0,154.0),(134,155),(135,157),(130,157)].map { PartyPoint($0.0,$0.1) })
        sleeve("farArm",farShoulder,farElbow,grip,true)
        sleeve("nearArm",nearShoulder,nearElbow,near,false)
        hand("farHand",grip,true);hand("nearHand",near,false)
        func limb(_ y:Double)->PartyPoint { let c=cos(angle),s=sin(angle);return body(PartyPoint(grip.x-10*c-y*s,grip.y-10*s+y*c)) }
        return BowRigSample(surfaces:surfaces,parts:parts,upperTip:limb(-36),lowerTip:limb(36),stringHand:body(nock),arrowTail:body(tail),arrowTip:body(PartyPoint(grip.x+30,tail.y)),arrowVisible:attack && p>0.24 && p<releaseProgress,arrowAlpha:PartyVisual.smooth((p-0.24)/0.035))
    }

    /// Same local arrow tip used by the actor at the instant of release.
    public static var releaseArrowTip:PartyPoint { sample(clip:"attack",progress:releaseProgress).arrowTip }

    /// The projectile ends at the same point and time used by the atomic hit.
    public static func projectile(age:Double,from:PartyPoint,to:PartyPoint,impact:Double)->BowProjectile? {
        guard age>=releaseAge,age<impact else { return nil }
        let t=(age-releaseAge)/(impact-releaseAge),tip=blend(from,to,t)
        let dx=to.x-from.x,dy=to.y-from.y,length=max(1,hypot(dx,dy)),span=38.0
        return BowProjectile(tail:PartyPoint(tip.x-dx/length*span,tip.y-dy/length*span),tip:tip,alpha:1)
    }
}
