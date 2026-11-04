import UIKit
import MeadowWorldSupport

/// Preparation/preview only; generated places do not spend AP or grant rewards.
final class MeadowMapSettingsViewController: UIViewController {
    private let fields = ["总节点数","普通战斗","Boss","奖励","空地点","额外道路","随机种子"]
    private var inputs: [UITextField] = []
    private var sliders: [UISlider] = []
    private var lastValid = MeadowMapConfiguration()
    private let status = UILabel()
    private let generateButton = UIButton(type:.system)
    private let enterButton = UIButton(type:.system)
    private let preview = MeadowMapThumbnail()
    private var result: GeneratedMeadowMap?
    private var revision = 0
    private let gold = UIColor(red:0.91,green:0.77,blue:0.43,alpha:1)

    override var supportedInterfaceOrientations: UIInterfaceOrientationMask { .landscape }
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red:0.055,green:0.09,blue:0.065,alpha:1)
        let scroll=UIScrollView(), rightScroll=UIScrollView(), form=UIStackView(), right=UIStackView()
        form.axis = .vertical; form.spacing=10; right.axis = .vertical; right.spacing=12
        let title=UILabel();title.text="随机林地";title.font = .boldSystemFont(ofSize:26);title.textColor=gold
        form.addArrangedSubview(title)
        let defaults=["10","4","1","3","1","1","31827"]
        for (index,name) in fields.enumerated() {
            let row=UIStackView();row.spacing=8;row.alignment = .center
            let label=UILabel();label.text=name;label.font = .boldSystemFont(ofSize:17);label.textColor = .white
            label.widthAnchor.constraint(equalToConstant:90).isActive=true
            let field=UITextField();field.text=defaults[index];field.tag=index
            field.font = .monospacedDigitSystemFont(ofSize:19,weight:.semibold);field.textColor=gold
            field.backgroundColor=UIColor(white:1,alpha:0.07);field.borderStyle = .roundedRect
            field.keyboardType = .numberPad;field.accessibilityLabel=name
            field.addTarget(self,action:#selector(inputChanged(_:)),for:.editingChanged)
            inputs.append(field);row.addArrangedSubview(label);row.addArrangedSubview(field)
            row.heightAnchor.constraint(equalToConstant:40).isActive=true
            form.addArrangedSubview(row)
            if index<6 {
                let slider=UISlider();slider.tag=index;slider.minimumValue=index==0 ? 4:0
                slider.maximumValue=index==0 ? 30:index==5 ? Float(MeadowMapGenerator.maximumExtraRoads(total:10)):9
                slider.value=Float(defaults[index]) ?? 0;slider.minimumTrackTintColor=gold;slider.isContinuous=true
                slider.accessibilityLabel=name+"滑块"
                slider.addTarget(self,action:#selector(slid(_:)),for:.valueChanged)
                sliders.append(slider);form.addArrangedSubview(slider)
            }
        }
        let fixed=UILabel();fixed.text="起点固定 1 · 总数与各分类自动匹配";fixed.textColor=gold;fixed.font = .boldSystemFont(ofSize:15)
        fixed.numberOfLines=0;form.addArrangedSubview(fixed)
        let suggest=button("恢复建议分配",action:#selector(suggested));form.addArrangedSubview(suggest)
        let seed=button("换个种子",action:#selector(newSeed));form.addArrangedSubview(seed)
        let close=button("返回原地图",action:#selector(close));form.addArrangedSubview(close)
        let heading=UILabel();heading.text="道路预览";heading.font = .boldSystemFont(ofSize:22);heading.textColor=gold
        let note=UILabel();note.text="输入或拖动总数会自动分配各类节点。调整某类时优先用空地点补差。林地预览暂不结算战斗与奖励。"
        note.font = .systemFont(ofSize:17,weight:.medium);note.textColor = .white;note.numberOfLines=0
        status.textColor=gold;status.numberOfLines=0;status.font = .boldSystemFont(ofSize:17)
        generateButton.configuration=button("生成道路预览",action:#selector(generate)).configuration
        generateButton.addTarget(self,action:#selector(generate),for:.touchUpInside)
        enterButton.configuration=button("进入林地预览",action:#selector(enter)).configuration
        enterButton.addTarget(self,action:#selector(enter),for:.touchUpInside)
        right.addArrangedSubview(heading);right.addArrangedSubview(note);right.addArrangedSubview(preview)
        right.addArrangedSubview(status);right.addArrangedSubview(generateButton);right.addArrangedSubview(enterButton)
        preview.heightAnchor.constraint(equalToConstant:200).isActive=true
        scroll.addSubview(form);rightScroll.addSubview(right);view.addSubview(scroll);view.addSubview(rightScroll)
        for v in [scroll,rightScroll,form,right] { v.translatesAutoresizingMaskIntoConstraints=false }
        let guide=view.safeAreaLayoutGuide
        NSLayoutConstraint.activate([
            scroll.leadingAnchor.constraint(equalTo:guide.leadingAnchor,constant:18),scroll.topAnchor.constraint(equalTo:guide.topAnchor,constant:14),
            scroll.bottomAnchor.constraint(equalTo:guide.bottomAnchor,constant:-14),scroll.widthAnchor.constraint(equalTo:guide.widthAnchor,multiplier:0.39),
            form.leadingAnchor.constraint(equalTo:scroll.contentLayoutGuide.leadingAnchor),form.trailingAnchor.constraint(equalTo:scroll.contentLayoutGuide.trailingAnchor),
            form.topAnchor.constraint(equalTo:scroll.contentLayoutGuide.topAnchor),form.bottomAnchor.constraint(equalTo:scroll.contentLayoutGuide.bottomAnchor),
            form.widthAnchor.constraint(equalTo:scroll.frameLayoutGuide.widthAnchor),
            rightScroll.leadingAnchor.constraint(equalTo:scroll.trailingAnchor,constant:22),rightScroll.trailingAnchor.constraint(equalTo:guide.trailingAnchor,constant:-18),
            rightScroll.topAnchor.constraint(equalTo:guide.topAnchor,constant:16),rightScroll.bottomAnchor.constraint(equalTo:guide.bottomAnchor,constant:-14),
            right.leadingAnchor.constraint(equalTo:rightScroll.contentLayoutGuide.leadingAnchor),right.trailingAnchor.constraint(equalTo:rightScroll.contentLayoutGuide.trailingAnchor),
            right.topAnchor.constraint(equalTo:rightScroll.contentLayoutGuide.topAnchor),right.bottomAnchor.constraint(equalTo:rightScroll.contentLayoutGuide.bottomAnchor),
            right.widthAnchor.constraint(equalTo:rightScroll.frameLayoutGuide.widthAnchor)
        ])
        changed()
    }
    private func button(_ title:String,action:Selector) -> UIButton {
        let b=UIButton(type:.system);var c=UIButton.Configuration.filled();c.title=title
        c.baseBackgroundColor=gold;c.baseForegroundColor=UIColor(red:0.12,green:0.17,blue:0.12,alpha:1)
        c.contentInsets=NSDirectionalEdgeInsets(top:9,leading:10,bottom:9,trailing:10);b.configuration=c
        b.addTarget(self,action:action,for:.touchUpInside);return b
    }
    private func configuration() throws -> MeadowMapConfiguration {
        guard let total=Int(inputs[0].text ?? ""),let combat=Int(inputs[1].text ?? ""),let boss=Int(inputs[2].text ?? ""),
              let reward=Int(inputs[3].text ?? ""),let empty=Int(inputs[4].text ?? ""),let roads=Int(inputs[5].text ?? ""),
              let seed=UInt64(inputs[6].text ?? "") else { throw NSError(domain:"地图",code:1,userInfo:[NSLocalizedDescriptionKey:"请输入完整的非负整数。总数范围4—30。种子为0—18446744073709551615。"]) }
        var c=MeadowMapConfiguration();c.total=total;c.combat=combat;c.boss=boss;c.reward=reward;c.empty=empty;c.extraRoads=roads;c.seed=seed
        try c.validate();return c
    }
    private func applyCounts(_ c: MeadowMapConfiguration) {
        inputs[0].text=String(c.total)
        for (index,value) in [c.combat,c.boss,c.reward,c.empty].enumerated() { inputs[index+1].text=String(value) }
        inputs[5].text=String(c.extraRoads)
        lastValid=c
    }
    @objc private func inputChanged(_ field: UITextField) {
        if let value=Int(field.text ?? "") {
            if field.tag==0,let c=try? lastValid.changingTotal(to:value) { applyCounts(c) }
            else if (1...4).contains(field.tag),value>=0,let c=try? lastValid.changingCount(field:field.tag-1,to:value) { applyCounts(c) }
        }
        changed()
    }
    @objc private func slid(_ slider: UISlider) {
        let value=Int(slider.value.rounded());slider.value=Float(value)
        inputs[slider.tag].text=String(value)
        inputChanged(inputs[slider.tag])
    }
    private func changed() {
        revision+=1;result=nil;preview.map=nil;enterButton.isEnabled=false
        do {
            let c=try configuration();lastValid=c
            for slider in sliders {
                slider.maximumValue=slider.tag==0 ? 30:slider.tag==5 ? Float(MeadowMapGenerator.maximumExtraRoads(total:c.total)):Float(c.total-1)
                slider.value=Float(inputs[slider.tag].text ?? "") ?? 0
            }
            status.text="起点1 + 战斗\(c.combat) + Boss\(c.boss) + 奖励\(c.reward) + 空地\(c.empty) = \(c.total)\n数量正确，可生成。"
            generateButton.isEnabled=true
        } catch {
            var detail=error.localizedDescription
            let numbers=inputs.prefix(5).compactMap{Int($0.text ?? "")}
            if numbers.count==5,numbers.allSatisfy({(0...30).contains($0)}) {
                let allocated=1+numbers.dropFirst().reduce(0,+),difference=numbers[0]-allocated
                if difference != 0 { detail="已分配 \(allocated) / 总数 \(numbers[0])，"+(difference>0 ? "还差 \(difference) 个。" : "超出 \(-difference) 个。")+"\n"+detail }
            }
            status.text=detail;generateButton.isEnabled=false
        }
    }
    @objc private func suggested() {
        guard let n=Int(inputs[0].text ?? ""),(4...30).contains(n) else { changed();return }
        if let c=try? lastValid.changingTotal(to:n) { applyCounts(c) }
        changed()
    }
    @objc private func newSeed() { inputs[6].text=String(UInt64.random(in:0...UInt64.max));changed() }
    @objc private func generate() {
        view.endEditing(true)
        guard let config=try? configuration() else { changed();return }
        let token=revision;generateButton.isEnabled=false;status.text="正在生成林地…"
        DispatchQueue.global(qos:.userInitiated).async { [weak self] in
            let output=Result { try MeadowMapGenerator.generate(config) }
            DispatchQueue.main.async {
                guard let self,self.revision==token else { return }
                self.generateButton.isEnabled=true
                switch output {
                case .success(let map):
                    self.result=map;self.preview.map=map;self.enterButton.isEnabled=true
                    self.status.text="\(map.map.nodes.count)个节点 · \(map.roads.count)条道路 · \(config.extraRoads)条环路\n种子 \(config.seed)"
                case .failure(let error): self.status.text=error.localizedDescription
                }
            }
        }
    }
    @objc private func enter() {
        guard let result else { return }
        let controller=GameViewController(previewMap:result);controller.modalPresentationStyle = .fullScreen
        present(controller,animated:true)
    }
    @objc private func close() { dismiss(animated:true) }
}

private final class MeadowMapThumbnail: UIView {
    var map: GeneratedMeadowMap? { didSet { setNeedsDisplay() } }
    override func draw(_ rect:CGRect) {
        UIColor(red:0.1,green:0.19,blue:0.13,alpha:1).setFill();UIBezierPath(roundedRect:bounds,cornerRadius:12).fill()
        guard let map else { return }
        let scale=min((bounds.width-24)/1280,(bounds.height-24)/CGFloat(map.coordinateHeight))
        func point(_ x:Double,_ y:Double) -> CGPoint { CGPoint(x:bounds.midX+CGFloat(x-640)*scale,y:bounds.midY+CGFloat(y-map.coordinateHeight/2)*scale) }
        UIColor(red:0.6,green:0.52,blue:0.32,alpha:1).setStroke()
        for road in map.roads {
            let path=UIBezierPath();path.lineWidth=3;path.move(to:point(road.points[0].x,road.points[0].y))
            for p in road.points.dropFirst() { path.addLine(to:point(p.x,p.y)) };path.stroke()
        }
        let colors:[String:UIColor]=["start":.systemYellow,"combat":.systemRed,"boss":.systemPurple,"reward":.systemGreen,"empty":.lightGray]
        let names=["start":"起","combat":"战","boss":"首","reward":"奖","empty":"空"]
        for node in map.map.nodes {
            let p=point(node.x*1280,node.y*map.coordinateHeight),r:CGFloat=10
            colors[node.kind.rawValue]?.setFill();UIBezierPath(ovalIn:CGRect(x:p.x-r,y:p.y-r,width:r*2,height:r*2)).fill()
            let text=names[node.kind.rawValue] ?? "?"
            (text as NSString).draw(in:CGRect(x:p.x-7,y:p.y-8,width:16,height:18),withAttributes:[.font:UIFont.boldSystemFont(ofSize:13),.foregroundColor:UIColor.black])
        }
    }
}
