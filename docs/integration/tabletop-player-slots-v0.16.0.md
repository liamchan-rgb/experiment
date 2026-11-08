# 人物/行程槽、历史与老师席位

## 人物档案/行程槽、历史回退与老师参战 · 课堂v0.16.0/build21（2026-11-07）

用户授权开始旧后两项，新增人物名与自定义外观独立存档。教师游戏“管理→人物档案/行程槽/历史/老师参战”，绘本“存档与历史”；均私有，不进入公开捕获。12人物槽只含姓名和已认可外观/衣装装扮，读取到编辑区再确认应用，不带职业/数值/装备/金币/背包/地图。新行程逐学生读取档案，当前任意玩家含P7也可保存/应用。衣装不提供属性，武器仍按实际装备；独立体型/发型/脸/染色美术未制作，只登记，战斗复用现有骨架。

8完整行程槽沿用原MeadowCampaignSave，保存地图/队伍/背包/各队移动条/道路/镜头/战斗队列/RNG/历史。覆盖确认，读档/回退/新行程覆盖前Recovery唯一备份，提供最近20份恢复入口，旧文件保留。坏槽独立报错不删除，其余槽正常；旧两人档/旧addHost命令/可选外观字段兼容，读战斗槽后暂停。历史列表倒序展开骰值及成员数值变化，回退保留选中条目、撤回后续，新记录含道路/移动/镜头检查点；旧记录无检查点则停止游标且不补满余额。回退后暂停，不重复奖励/掷骰。

老师启用UI填名/职业/队伍，在探索且无道路游标、未结算时加入host=true独立P7；不占6学生，只有一名。7人沿用同一正式战斗、个人AP、组队仓库、GM、绘本状态与持久化，不新建第二引擎。地图/背包/战斗衣装跟随每名档案，按当前成员按需加载并裁减缓存；换装备预载后提交，不清掉其他成员纹理。旧“老师仅API/历史待办”已在本轮实现。

新增24项专项，本地及实际CI完成368规则/后台+6绘本核心零失败，另有本地4Python检查；设备Release实际编译`a14364ba89c44a76bffebe0e6004a019f860c8cd`，run42390402952 attempt1。版本0.16.0/build21，最低iPadOS27.0、SDKiphoneos27.2，CRC/经典ZIP2.0/arm64/755/Metal/568源资源SHA/281编译名称/3挂载数据核验通过，可执行文件不同build20。未运行App/模拟器/实机，真实七人布局/点击/键盘/电视与性能由用户复核。6秒GIF是已有图集的离线流程示意，经主线程四阶段接触表与逐帧解码审核，不是App截图/触摸/性能测试。

源码快照`93a899956222d958d4d257c37990010899590559`与实际编译提交分开，标签`archive-player-slots-meadow-v0.16.0-20261107`。完整源码/Git bundle/IPA/诊断/GIF已存archive-assets，逐文件ZIP/独立bundle恢复与fsck/全部公开分片GET通过，归档run42391019080；main只放索引。直接IPA完整GET200，62573595字节，SHA256`699c2d5b6e90580e6240768d16e6091a9355afc3f3a7b719fb79edbf6b415308`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/b6625c3fbbb9b00ae4d0e03f599fa1ec0db5c3bf/archive-player-slots-meadow-v0.16.0-20261107/ClassroomStage2-v0.16.0-unsigned.ipa) · [正常速度流程示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/b6625c3fbbb9b00ae4d0e03f599fa1ec0db5c3bf/archive-player-slots-meadow-v0.16.0-20261107/player-slots-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/player-slots-meadow-v0.16.0-20261107.json)

experiment本体仍Build95，本轮只同步对接记录。后两步建议：人物/行程槽手动导出导入，方便换机与课堂备份；行程筛选与历史分类，方便长课时查找。不是自动启动新任务。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/player-slots-v0.16.0.md
