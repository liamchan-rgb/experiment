# 桌游 demo 对接核查与建议（2026-11-06）

本轮仅只读核查 `liamchan-rgb/classroom-boardgame`，未修改该库、未编译或运行桌游App，也未读取教师设备资料。main核对提交 `1e9100c4c18364ea64b3ec974fe957ba4ef42f6f`；战斗分支 `feat/side-view-battle-scene-v0.11` 提交 `a0427b83d9233f1a83178b3c47d3fab39eed664e`。两分支的 App.swift、PVEAppSession.swift、PublicProjection.swift 相同，GameCore源码树相同。不是已完成接入的声明。

## 现有入口与可复用部分

- `native/ClassroomProbe/App.swift`：TeacherHostController承载教师界面；PublicSceneDelegate创建外接公开窗口。保留既有场景注册和系统/SDK要求，接入阶段以原项目实际设置验证，不把Meadow的iOS15部署目标等同其外接屏能力。
- `TeacherSession.swift`：PPT、笔记、公开图片、暂停状态及独立PVE会话；不可用新游戏壳替掉这些已有功能。
- `PVEAppSession.swift`：唯一操作入口perform/apply、计时/AI/保存、PresentationLedger；publish把publicFrame+pending presentations写入display.playFrame。
- `Views.swift / PublicSurface`：已有PVEPublicView(frame:image:showingBook:)切入点，教师笔记不在此公开接口。
- `native/Packages/GameCore`：与experiment的Vendor同源。当前Meadow已扩展命令、MapNode可选字段、行程/商店与表现支持，不能再当作两份源码字节相同；UPSTREAM.json记录的是最初快照指纹，不是当前一致性承诺。正式内容表仍由各自源文件摘要核对。
- 现有默认demo为p1/p2双人森林；工厂实际支持1—6学生+最多1主持人，角色ID可自定。不能把当前Meadow固定p1/p2、最多3敌人的画面直接当作支持全部课堂编队。

## 推荐路线：原桌游程序作主壳，先接画面

```mermaid
flowchart LR
  T[教师控制台/PPT] --> H[PVEAppSession 单一权威会话]
  H --> E[统一版本 GameCore / 原子保存]
  E --> P[公开投影与 PresentationLedger]
  P --> R[Meadow只读画面适配层]
  R --> S[PublicSurface / 外接公开窗口]
```

不先搭网络服务器，也不把整个GameViewController塞进公开端。已有同进程publicFrame发布链足够做首版。把地图/战斗/特效渲染抽为可嵌入组件，由原教师端负责操作；公开端只收脱敏帧与表现数据，不拥有第二个GameEngine、RNG、AI或决策计时器。

### 必须先解决的边界

1. **结算与演出**：原主demo先apply并提交PresentationLedger；Meadow演练有prepare隔离求值、命中commit的路径。首版采用主demo已提交账本模式，新画面只播放真实receipt/骰子，不能再次prepare/apply/commit、再次扣AP或重掷。命中前后的数字显隐由账本时序驱动，不能把已提交后的快照直接闪现为受击前画面。
2. **公开/私有数据**：沿用PublicGameSnapshot的未揭示节点/怪物过滤；不把完整GameState、掉落概率、未公开库存或教师笔记传给公开视图。当前PublicGameUnit没有完整装备与buff表现数据，应新增专用公开视觉描述（unitID、可见外观/武器/服装ID与公开状态），不能为省事把整个单位对象泄露过去。
3. **角色ID/容量**：建立真实unitID到视觉槽的映射，不改原存档ID、不伪装全部学生为p1/p2。先验证现有默认双人森林，再扩展全部课堂编队和目标选择；多角色外观缺图按用户要求标注、可用现有人物占位，容量和ID正确性不能靠缺图跳过。
4. **规则模式**：原森林是按AP移动、抵达自动开战；Meadow是距离移动条、主动交互。首个视觉适配保留主demo原规则。随机行程/服务编辑作为后续明确的行程模式接入，不能悄悄替换全局移动规则或重建旧局。
5. **存档/撤销**：原AtomicGameStore保存GameArchive，MeadowCampaignSave还含布局/道路游标/移动条/配置。不能直接覆盖对方保存文件。教师撤销要恢复同一事务的核心和行程侧状态，避免只回滚金币而保留事件完成标记/移动扣除；先提供只读检查与备份，再做明确转换。
6. **资源与宿主**：抽出资源解析接口，区分当前UIImage(named:)主Bundle查找与Swift Package资源Bundle；保留原App外接屏/PPT切换、暂停、重连及键盘路由。不得以镜像教师主屏代替独立公开画面。

## 分步交付与可检查标准

1. 在experiment中先做只读PublicPlayFrame适配样例：输入固定的原demo默认双人森林公开帧和已提交回执；显示真实ID、地图、HP/AP、骰子与受击时序。相同帧重复投递不重播已完成receipt、不改变任何规则状态。覆盖隐藏怪、取消/暂停、死亡和一次结算。此步不动桌游仓库主分支。
2. 通过后在桌游库新源码分支接入PublicSurface开关：旧画面可回退，保留教师/PPT；统一GameCore版本、移植全部原测试，追加差异/存档/计时/撤销测试。先默认双人，再全部课堂容量。接入该库时遵守其AGENTS的唯一标签、可恢复存档和archive-assets归档规则，本轮只读核查不创建该库标签/归档。
3. 视觉桥确认后，再接随机行程与地点编辑：独立模式/版本化保存、单一权威命令入口、资源表现缺口清单。最终分别检查源码/设备Release/IPA来源，公开链接完整GET与SHA256；App/实机运行继续由用户负责。

建议下一项先完成第1步适配样例，而不是把两边的完整App目录互相覆盖。本轮只交付方案与证据，不声称双库共享运行状态、真实设备连接或存档转换已实现。
