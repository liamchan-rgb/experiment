# Meadow Journey 1.6.18 / build44

护盾0.46秒展开后生效；回血去翻面/固定星点ID；目标60Hz时钟与真60Hz死亡图集，缓存光池/投影、共用粒子计算、异步预热。大粗衬线字和原深绿金边语言，HP/盾/AP条、三技能卡；护盾方框悬停/焦点/点按查看详情。强击5、恢复4、盾4、敌攻4与原人物/步态/运镜不变。

源码1236b9010352db5417665432066b079c7ff6b7fc；[设备Release归档40182000958](https://github.com/liamchan-rgb/experiment/actions/runs/40182000958)，五项纯Swift检查通过，无App/模拟器/实机执行。IPA与摘要见package.json；直接IPA见Downloads/MeadowJourney-b44.ipa，沿原SideStore重签流程。

[离线美术预览](../../Art/Review/Battle/smooth-status-demo-v1/)为正常50fps共享资源/生产Swift轨迹、光照/字体/UI近似，非设备录屏，不作为60fps性能验收。新图集解码约83.6MiB，真实内存/主线程/GPU性能未测。App在动作完成/关闭时异步写Documents/BattleFrameTiming.json，记录实际display-link间隔和更新CPU，不冒充GPU计时。设备测试由用户反馈。
