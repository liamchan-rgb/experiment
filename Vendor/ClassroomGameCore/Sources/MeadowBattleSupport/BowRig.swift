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
        // The reviewed release takes 0.32 seconds; retain the recovered pose
        // until the whole actor lowers the bow instead of bouncing back to aim.
        let follow=attack ? PartyVisual.smooth((p-releaseProgress)/(0.32/1.2)):0
        func body(_ q:PartyPoint)->PartyPoint {
            let dx=q.x-132,dy=q.y-167,c=cos(lean),s=sin(lean)
            return PartyPoint(132+dx*c-dy*s,167+dx*s+dy*c+crouch)
        }
        // Pose A: the FAR arm holds the bow, the NEAR arm draws toward the cheek.
        // These are authored bow sleeves, not rotated cutouts of the sword arm.
        let grip=blend(PartyPoint(163,165),PartyPoint(190,148),aim)
        let angle=mix(0.18,0,aim)
        let nearShoulder=PartyPoint(130,145)
        let farShoulder=PartyPoint(141,143)
        func solveElbow(_ shoulder:PartyPoint,_ hand:PartyPoint,_ upper:Double,_ fore:Double)->PartyPoint {
            let dx=hand.x-shoulder.x,dy=hand.y-shoulder.y
            let distance=min(upper+fore-0.001,max(abs(upper-fore)+0.001,hypot(dx,dy)))
            let cosine=min(1,max(-1,(upper*upper+distance*distance-fore*fore)/(2*upper*distance)))
            let a=atan2(dy,dx)+acos(cosine)
            return PartyPoint(shoulder.x+upper*cos(a),shoulder.y+upper*sin(a))
        }
        let lift=attack ? PartyVisual.smooth(p/0.19):0
        let retire=attack ? PartyVisual.smooth((p-0.65)/0.35):0
        func joint(_ rest:PartyPoint,_ reach:PartyPoint,_ held:PartyPoint,_ recovered:PartyPoint)->PartyPoint {
            let raised=blend(rest,reach,lift),pulled=blend(raised,held,draw),released=blend(pulled,recovered,follow)
            return blend(released,rest,retire)
        }
        // The foreground drawing elbow stays behind the shoulder.  Author both
        // joints together so the sleeve remains connected throughout release.
        // The resting drawing hand already touches the string.  It lifts and
        // draws the string toward the cheek as the far arm raises the bow.
        let restHand=PartyPoint(153,159)
        let elbowGuide=joint(solveElbow(nearShoulder,restHand,32,44),PartyPoint(102,134),PartyPoint(99,134),PartyPoint(100,150))
        let handGuide=joint(restHand,PartyPoint(147,137),PartyPoint(143,137),PartyPoint(143,160))
        func pointAlong(_ origin:PartyPoint,_ target:PartyPoint,_ length:Double)->PartyPoint {
            let dx=target.x-origin.x,dy=target.y-origin.y,d=max(0.001,hypot(dx,dy))
            return PartyPoint(origin.x+dx*length/d,origin.y+dy*length/d)
        }
        // Preserve the two visible limb lengths while following the authored
        // elbow and hand paths; the sleeve must not grow while it is raised.
        let nearElbow=pointAlong(nearShoulder,elbowGuide,32)
        let near=pointAlong(nearElbow,handGuide,44)
        let straight=PartyPoint(grip.x-10,grip.y-6)
        let engaged = !attack || p<=releaseProgress
        // On release the string returns to its resting line immediately; do
        // not leave a floating V-shaped bend detached from the hand.
        let nock = engaged ? near:straight
        let tail=engaged ? near:straight
        // Solve the far arm with constant lengths.  In the held pose the
        // almost-straight arm and the grip are one continuous silhouette.
        let farElbow=solveElbow(farShoulder,grip,25,25)
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
            strip(group,far ? base:0x315785,sh,el,5,5);disc(group,base,el,5)
            strip(group,base,el,cuff,5,3.5);disc(group,base,sh,5)
            strip(group,shade,sh,el,1.3,1.3,3.5);strip(group,shade,el,cuff,1,1,3)
            strip(group,light,blend(sh,el,0.35),blend(sh,el,0.80),0.8,0.8,-2.5)
            strip(group,light,el,blend(el,cuff,0.85),1,0.8,-2.2)
            strip(group,outer,cuff,wrist,4.8,4.8)
            strip(group,0xc9b781,blend(cuff,wrist,0.14),wrist,3.7,3.7)
            strip(group,0xf0e4b6,blend(cuff,wrist,0.14),wrist,1.1,1.1,-2)
        }
        // Hands are different silhouettes. The near drawing hand extends
        // forward from its cuff and hooks the string at its fingertips; the
        // far holding hand wraps around the grip.
        func wrist(_ elbow:PartyPoint,_ contact:PartyPoint,_ length:Double)->PartyPoint {
            let dx=contact.x-elbow.x,dy=contact.y-elbow.y,l=max(1,hypot(dx,dy))
            return PartyPoint(contact.x-length*dx/l,contact.y-length*dy/l)
        }
        func hand(_ group:String,_ q:PartyPoint,_ elbow:PartyPoint,_ holding:Bool) {
            let dx=q.x-elbow.x,dy=q.y-elbow.y,l=max(1,hypot(dx,dy)),ux=dx/l,uy=dy/l,nx = -uy,ny=ux
            func poly(_ color:UInt32,_ pairs:[(Double,Double)]) {
                polygon(group,color,pairs.map { PartyPoint(q.x+ux*$0.0+nx*$0.1,q.y+uy*$0.0+ny*$0.1) })
            }
            if holding {
                poly(0x55301e,[(-7,-4),(-4,-6),(1,-6),(4,-5),(5,-3),(5,4),(3,6),(-3,6),(-6,4),(-7,1)])
                poly(0xeea36e,[(-6,-3),(-3,-5),(1,-5),(3,-4),(4,-2),(4,3),(2,5),(-3,5),(-5,3)])
                // Palm and thumb curl around the rear side of the bow grip.
                poly(0xffc993,[(-5,-3),(-3,-4),(0,-4),(0,-1),(-2,0),(-2,3),(-4,3),(-5,1)])
                poly(0xffc993,[(-3,0),(-1,-1),(1,0),(1,2),(-1,3),(-3,2)])
                // Separate curled fingers on the front of the grip.
                poly(0x8f4d2c,[(1,-3),(4,-3),(4,-2),(1,-2)])
                poly(0x9f5932,[(1,0),(4,0),(4,1),(1,1)])
                poly(0xd47d4b,[(1,3),(4,3),(3,4),(1,4)])
            } else {
                // q is the nock at the fingertips, not the middle of a fist.
                poly(0x55301e,[(-14,-3),(-12,-5),(-4,-5),(0,-4),(2,-3),(2,-1),(0,0),(1,2),(-1,4),(-6,5),(-13,4),(-14,2)])
                poly(0xefaa75,[(-13,-2),(-11,-4),(-4,-4),(0,-3),(1,-2),(0,-1),(-2,0),(0,2),(-2,3),(-6,4),(-12,3),(-13,1)])
                poly(0xffcc99,[(-12,-2),(-10,-3),(-4,-3),(-2,-2),(-2,-1),(-5,0),(-12,0)])
                // Two bent fingertips point toward the string, with a thumb
                // beneath the nock. Short dark pixels suggest the separations.
                poly(0xffc893,[(-4,-3),(0,-3),(1,-2),(0,-1),(-4,-1)])
                poly(0xa65e37,[(-3,-1),(0,-1),(0,0),(-3,0)])
                poly(0xffc28c,[(-4,0),(0,0),(1,1),(0,2),(-4,2)])
                poly(0xc17a49,[(-5,2),(-2,2),(-2,3),(-5,3)])
                poly(0xfac08a,[(-11,1),(-7,1),(-3,2),(-4,4),(-9,4),(-12,3)])
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
        sleeve("farArm",farShoulder,farElbow,wrist(farElbow,grip,5),true)
        sleeve("nearArm",nearShoulder,nearElbow,wrist(nearElbow,near,13),false)
        hand("farHand",grip,farElbow,true);hand("nearHand",near,nearElbow,false)
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
