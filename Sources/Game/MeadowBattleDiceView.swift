import UIKit
import MeadowBattleSupport

/// Shared by single and party scenes. Clock samples are analytic, never a frame timer.
final class MeadowBattleDiceView:UIView {
    var dice:[BattleDie]=[]
    var time=0.0,visibleAge=0.0
    var resolvedAge:Double?,exitAge:Double?
    override init(frame:CGRect) { super.init(frame:frame);backgroundColor = .clear;isOpaque=false;isUserInteractionEnabled=false;accessibilityIdentifier="battleHeadDice" }
    required init?(coder:NSCoder) { fatalError("init(coder:) has not been implemented") }
    override func draw(_ rect:CGRect) {
        guard let ctx=UIGraphicsGetCurrentContext(),!dice.isEmpty else { return }
        for (index,die) in dice.enumerated() {
            let p=BattleDice.pose(time:time,index:index,resolvedAge:resolvedAge,visibleAge:visibleAge,exitAge:exitAge)
            guard p.alpha>0 else { continue }
            let colors:[String:UIColor]=["red":UIColor(red:0.78,green:0.16,blue:0.14,alpha:1),"yellow":UIColor(red:0.85,green:0.63,blue:0.16,alpha:1),"green":UIColor(red:0.13,green:0.58,blue:0.32,alpha:1),"blue":UIColor(red:0.12,green:0.44,blue:0.8,alpha:1)]
            let color=colors[die.color] ?? .gray
            let cx=bounds.midX+(CGFloat(index)-CGFloat(dice.count-1)/2)*62
            ctx.saveGState();ctx.setAlpha(CGFloat(p.alpha));ctx.translateBy(x:cx,y:bounds.midY+CGFloat(p.offsetY)-7);ctx.rotate(by:CGFloat(p.angle));ctx.scaleBy(x:CGFloat(p.scale),y:CGFloat(p.scale))
            ctx.setShadow(offset:CGSize(width:0,height:3),blur:4,color:UIColor.black.withAlphaComponent(0.55).cgColor)
            let side=UIBezierPath();side.move(to:CGPoint(x:19,y:-21));side.addLine(to:CGPoint(x:27,y:-15));side.addLine(to:CGPoint(x:27,y:22));side.addLine(to:CGPoint(x:19,y:27));side.close();color.withAlphaComponent(0.7).setFill();side.fill()
            let top=UIBezierPath();top.move(to:CGPoint(x:-21,y:-21));top.addLine(to:CGPoint(x:-13,y:-27));top.addLine(to:CGPoint(x:27,y:-27));top.addLine(to:CGPoint(x:19,y:-21));top.close();color.setFill();top.fill()
            let face=UIBezierPath(roundedRect:CGRect(x:-23,y:-23,width:46,height:46),cornerRadius:7);color.setFill();face.fill();MeadowPreviewPalette.ink.withAlphaComponent(0.95).setStroke();face.lineWidth=1.8;face.stroke();ctx.setShadow(offset:.zero,blur:0,color:nil)
            func text(_ value:String,_ y:CGFloat,_ size:CGFloat,_ alpha:Double) {
                let attrs:[NSAttributedString.Key:Any]=[.font:MeadowPreviewPalette.font(size,.heavy),.foregroundColor:MeadowPreviewPalette.ink.withAlphaComponent(CGFloat(alpha)),.strokeColor:UIColor.black.withAlphaComponent(0.35),.strokeWidth:-2]
                let s=NSAttributedString(string:value,attributes:attrs);s.draw(at:CGPoint(x:-s.size().width/2,y:y))
            }
            text(die.sides>0 ? String(p.face):"?",-19,30,1-p.resultMix)
            if let v=die.value { text(String(v),-19,30,p.resultMix) }
            text(die.label,30,14,1)
            ctx.restoreGState()
        }
    }
}
