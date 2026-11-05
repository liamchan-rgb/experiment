import UIKit
import MeadowWorldSupport
import MeadowBattleSupport
import ClassroomGameCore

/// Configure a map, inspect its scenery, or create/resume a persistent expedition.
final class MeadowMapSettingsViewController: UIViewController {
    private let fields = ["总节点数","普通战斗","Boss","奖励","空地点","额外道路","随机种子"]
    private var inputs: [UITextField] = []
    private var sliders: [UISlider] = []
    private var lastValid = MeadowMapConfiguration()
    private let status = UILabel()
    private let generateButton = UIButton(type:.system)
    private let enterButton = UIButton(type:.system)
    private let preview = MeadowMapThumbnail()
    private let startCampaignButton=UIButton(type:.system)

    private let campaignClass=UISegmentedControl(items:["冒险者","魔剑士","龙骑士"])
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
        let heading=UILabel();heading.text="建筑与道路预览";heading.font = .boldSystemFont(ofSize:22);heading.textColor=gold
        let note=UILabel();note.text="数量与滑块联动。可先预览建筑道路，再开始双人探索；探索会保存生命、背包、已领取奖励与途中位置。"
        note.font = .systemFont(ofSize:17,weight:.medium);note.textColor = .white;note.numberOfLines=0
        status.textColor=gold;status.numberOfLines=0;status.font = .boldSystemFont(ofSize:17)
        generateButton.configuration=button("生成道路预览",action:#selector(generate)).configuration
        generateButton.addTarget(self,action:#selector(generate),for:.touchUpInside)
        enterButton.configuration=button("进入林地预览",action:#selector(enter)).configuration
        enterButton.addTarget(self,action:#selector(enter),for:.touchUpInside)
        right.addArrangedSubview(heading);right.addArrangedSubview(note);right.addArrangedSubview(preview)
        right.addArrangedSubview(status);right.addArrangedSubview(generateButton);right.addArrangedSubview(enterButton)
        startCampaignButton.configuration=button("开始新行程",action:#selector(startCampaign)).configuration
        startCampaignButton.addTarget(self,action:#selector(startCampaign),for:.touchUpInside)
        let classLabel=UILabel();classLabel.text="P1职业 · P2沿用游侠";classLabel.font = .boldSystemFont(ofSize:17);classLabel.textColor=gold
        campaignClass.selectedSegmentIndex=1;campaignClass.setTitleTextAttributes([.foregroundColor:UIColor.white],for:.normal);campaignClass.selectedSegmentTintColor=UIColor(red:0.35,green:0.35,blue:0.15,alpha:1)
        right.addArrangedSubview(classLabel);right.addArrangedSubview(campaignClass)
        right.addArrangedSubview(startCampaignButton)
        right.addArrangedSubview(button("继续已保存行程",action:#selector(continueCampaign)))
        right.addArrangedSubview(button("历史结算",action:#selector(showCompletedCampaigns)))
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
        revision+=1;result=nil;preview.map=nil;enterButton.isEnabled=false;startCampaignButton.isEnabled=false
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
                    self.result=map;self.preview.map=map;self.enterButton.isEnabled=true;self.startCampaignButton.isEnabled=true
                    self.status.text="\(map.map.nodes.count)个节点 · \(map.roads.count)条道路 · \(config.extraRoads)条环路\n种子 \(config.seed)"
                case .failure(let error): self.status.text=error.localizedDescription
                }
            }
        }
    }
    static func campaignStore()->MeadowCampaignStore {
        let base=FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask)[0]
        return MeadowCampaignStore(url:base.appendingPathComponent("MeadowExpedition/campaign-v1.json"))
    }
    @objc private func startCampaign() {
        guard let result else{return}
        let create={ [weak self] in
            guard let self else{return}
            do {
                let store=Self.campaignStore(),base=FileManager.default.urls(for:.applicationSupportDirectory,in:.userDomainMask)[0]
                let campStore=CampSaveStore(url:base.appendingPathComponent("MeadowCamp/camp-v1.json"))
                var units:[String:ClassroomGameCore.GameUnit]?,appearance="forester"
                if let bytes=try campStore.read() {
                    let save=try JSONDecoder().decode(CampSave.self,from:bytes)
                    try save.validate(appearances:["forester","wayfarer"],equipment:Set(["trainingSword","huntingBow","greatSword","legendaryStaff","leatherArmor","runeArmor","powerBadge","actionRing"]))
                    units=save.archive.state.units;appearance=save.appearanceID
                }
                try store.preserveCompletedCampaign()
                let session=try MeadowCampaignSession.new(layout:result,appearanceID:appearance,playerClassID:["adventurer","spellblade","dragonKnight"][max(0,self.campaignClass.selectedSegmentIndex)],loadouts:units,persist:store.write)
                self.presentCampaign(session)
            } catch {self.status.text="未开始新行程："+error.localizedDescription}
        }
        if FileManager.default.fileExists(atPath:Self.campaignStore().url.path) {
            let alert=UIAlertController(title:"开始新行程？",message:"这会替换当前探索存档。营地衣装与装备存档会保留。",preferredStyle:.alert)
            alert.addAction(UIAlertAction(title:"取消",style:.cancel))
            alert.addAction(UIAlertAction(title:"开始新行程",style:.destructive,handler:{_ in create()}));present(alert,animated:true)
        } else {create()}
    }
    @objc private func continueCampaign() {
        do {
            let store=Self.campaignStore()
            guard let save=try store.read() else{status.text="还没有已保存行程。先生成地图并开始新行程。";return}
            presentCampaign(try MeadowCampaignSession(save:save,persist:store.write))
        } catch {status.text="无法读取行程，原存档已保留："+error.localizedDescription}
    }
    @objc private func showCompletedCampaigns(){
        do{
            let saves=try Self.campaignStore().completedCampaigns()
            guard !saves.isEmpty else{status.text="还没有已结算行程。";return}
            let menu=UIAlertController(title:"历史结算",message:"选择行程查看已保存结果",preferredStyle:.actionSheet)
            let format=DateFormatter();format.dateFormat="MM-dd HH:mm"
            for save in saves {
                guard let result=save.completion else{continue}
                menu.addAction(UIAlertAction(title:format.string(from:result.completedAt)+" · "+(result.outcome=="victory" ? "通关":"队伍倒地")+" · 种子\(save.layout.configuration.seed)",style:.default){[weak self] _ in
                    let screen=MeadowCampaignResultsViewController(result:result,catalog:save.archive.catalog,seed:save.layout.configuration.seed);self?.present(screen,animated:true)
                })
            }
            menu.addAction(UIAlertAction(title:"取消",style:.cancel));menu.popoverPresentationController?.sourceView=preview;menu.popoverPresentationController?.sourceRect=preview.bounds;present(menu,animated:true)
        }catch{status.text="历史结算读取失败，原文件已保留："+error.localizedDescription}
    }
    private func presentCampaign(_ session:MeadowCampaignSession) {
        let controller=GameViewController(campaign:session);controller.modalPresentationStyle = .fullScreen
        present(controller,animated:true)
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
        for prop in map.props.filter({$0.nodeID != nil}).sorted(by:{$0.y<$1.y}) {
            let p=point(prop.x,prop.y),width=CGFloat(prop.width)*scale
            if let image=UIImage(named:prop.asset) {
                let height=width*image.size.height/image.size.width,anchor:CGFloat=prop.asset=="CampTent" ? 0.10:0.08
                image.draw(in:CGRect(x:p.x-width/2,y:p.y-height*(1-anchor),width:width,height:height))
            }
            guard let node=map.map.nodes.first(where:{$0.id==prop.nodeID}) else { continue }
            let badge=point(prop.x,prop.y-Double(SceneDefinition.landmarkBadgeRise(asset:prop.asset,width:CGFloat(prop.width)))),r:CGFloat=5
            colors[node.kind.rawValue]?.setFill();UIBezierPath(ovalIn:CGRect(x:badge.x-r,y:badge.y-r,width:r*2,height:r*2)).fill()
            let text=names[node.kind.rawValue] ?? "?"
            (text as NSString).draw(in:CGRect(x:badge.x-4,y:badge.y-5,width:10,height:11),withAttributes:[.font:UIFont.boldSystemFont(ofSize:8),.foregroundColor:UIColor.black])
        }
    }
}

final class MeadowCampaignResultsViewController:UIViewController {
    let result:MeadowCampaignCompletion,catalog:GameCatalog,seed:UInt64
    var onReturnSettings:(()->Void)?
    private let scroll=UIScrollView(),stack=UIStackView()
    private let close=MeadowPreviewPalette.button("返回查看"),settings=MeadowPreviewPalette.button("保存并返回设置")
    init(result:MeadowCampaignCompletion,catalog:GameCatalog,seed:UInt64){self.result=result;self.catalog=catalog;self.seed=seed;super.init(nibName:nil,bundle:nil);modalPresentationStyle = .fullScreen;isModalInPresentation=true}
    required init?(coder:NSCoder){fatalError("init(coder:) has not been implemented")}
    override var prefersStatusBarHidden:Bool{true}
    override var supportedInterfaceOrientations:UIInterfaceOrientationMask{.landscape}
    override func viewDidLoad(){
        super.viewDidLoad();view.backgroundColor=MeadowPreviewPalette.panel
        view.addSubview(scroll);scroll.addSubview(stack);view.addSubview(close);view.addSubview(settings)
        stack.axis = .vertical;stack.spacing=14;stack.translatesAutoresizingMaskIntoConstraints=false
        NSLayoutConstraint.activate([stack.topAnchor.constraint(equalTo:scroll.contentLayoutGuide.topAnchor,constant:12),stack.bottomAnchor.constraint(equalTo:scroll.contentLayoutGuide.bottomAnchor,constant:-12),stack.leadingAnchor.constraint(equalTo:scroll.contentLayoutGuide.leadingAnchor,constant:16),stack.trailingAnchor.constraint(equalTo:scroll.contentLayoutGuide.trailingAnchor,constant:-16),stack.widthAnchor.constraint(equalTo:scroll.frameLayoutGuide.widthAnchor,constant:-32)])
        func text(_ value:String,_ size:CGFloat=18){let label=MeadowPreviewPalette.label(value,size:size);label.numberOfLines=0;stack.addArrangedSubview(label)}
        text(result.outcome=="victory" ? "行程完成":"行程结束 · 队伍倒地",30)
        let date=DateFormatter();date.dateStyle = .medium;date.timeStyle = .short
        text(date.string(from:result.completedAt)+" · 地图种子 \(seed)",16)
        text("探索 \(result.exploredNodes)/\(result.totalNodes) 地点  ·  清理 \(result.clearedEncounters)/\(result.totalEncounters) 战斗地点  ·  补给 \(result.collectedRewards)/\(result.totalRewards)")
        text("累计移动 \(Int(result.distance.rounded())) 距离  ·  移动购买花费 \(result.movementCoins) 金币")
        for player in result.players {
            let attributes=(try? GameRules.attributes(player,catalog:catalog)) ?? player.baseAttributes
            text(player.name,23)
            let health=MeadowBattleResourceBar();health.show("生命",value:player.health,maximum:attributes.maximumHealth,color:.systemGreen);health.heightAnchor.constraint(equalToConstant:44).isActive=true;stack.addArrangedSubview(health)
            text("持有金币 \(player.coins)  ·  积分 \(player.score)")
            let equipment=player.equipment.itemIDs.map{(try? catalog.item($0).name) ?? $0}.joined(separator:"、")
            text("装备："+(equipment.isEmpty ? "未装备":equipment),17)
            let items=player.inventory.keys.sorted().map{((try? catalog.item($0).name) ?? $0)+" ×\(player.inventory[$0]!)"}.joined(separator:"、")
            text("行囊："+(items.isEmpty ? "空":items),17)
        }
        text("以上为已保存的最终结果，金币和物品已经按行程中的实际操作结算。",16)
        close.addAction(UIAction{[weak self] _ in self?.dismiss(animated:true)},for:.touchUpInside)
        settings.isHidden=onReturnSettings==nil
        settings.addAction(UIAction{[weak self] _ in guard let self else{return};self.dismiss(animated:true){self.onReturnSettings?()}},for:.touchUpInside)
    }
    override func viewDidLayoutSubviews(){
        super.viewDidLayoutSubviews();let inset=view.safeAreaInsets,left=max(16,inset.left+12),right=view.bounds.width-max(16,inset.right+12),bottom=view.bounds.height-max(12,inset.bottom+8)
        scroll.frame=CGRect(x:left,y:max(10,inset.top+8),width:right-left,height:max(1,bottom-74-max(10,inset.top+8)))
        let width=(right-left-12)/2
        close.frame=CGRect(x:left,y:bottom-52,width:onReturnSettings==nil ? right-left:width,height:44);settings.frame=CGRect(x:left+width+12,y:bottom-52,width:width,height:44)
    }
}
