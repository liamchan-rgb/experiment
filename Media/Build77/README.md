# Build77 · 骰子定位崩溃修复，归档等待中

用户报告Build76战斗一轮后闪退，新档同样。旧BattleDice.swift:91的真实m-node-index怪物ID查演练feet字典会强制解包空值，已用旧生产函数复现fatal/signal4并修复演员/目标站位映射。无须清档，原存档、三倍移动、人物/武器/衣装/动作/规则保持。

194项纯Swift测试、四组原回归及真实会话/骰子投影导出通过。新增3项用例和首领再生显示扩展覆盖真实怪物两轮、怪物回合读档、多节点双敌站位和玩家接敌时的骰子血条避让。旧函数失败证据before-fix-reproduction.log与本地通过日志保存在本目录；纯函数复现并非用户设备崩溃日志。

[最新Mac归档任务](https://github.com/liamchan-rgb/experiment/actions/runs/41864553920) · [GitHub官方状态](https://www.githubstatus.com/) · [正常怪物回合GIF](../../Art/Review/Battle/campaign-crashfix-v1/monster-turn-normal.gif) · [完整战斗MP4](../../Art/Review/Battle/campaign-crashfix-v1/encounter-full.mp4) · [原因与修复](../../docs/planning/random-map-v1/build77-monster-dice-crash.md)

截至build-status.json记录时间，GitHub官方报告Actions degraded_performance、Incident with Actions and Pages investigating。Intel与备用Mac池均未开始执行，已请求取消旧尝试，仅保留最新隔离并发组的macos-15归档。**尚无本轮新IPA，不得把Build76改名或作为修复包交付，也不得把测试通过说成设备归档成功。**版本候选1.6.50/77，最终包仍需设备Release成功、核版本/CRC/ZIP/arm64/资源/来源及公开直链完整GET。

主线程亲看238个实际GIF解码帧的4页接触表、命中/翻面/回位及玩家骰子/胜利全场关键图。离线光影/UI近似，不是UIKit/设备录屏；未运行App/模拟器/实机，设备稳定性由用户验证。新美术认可null。

下一步先取得并核验修复IPA；修复交付后原计划两项为M4单节点内容编辑、行程行囊/换装与队伍配置。
