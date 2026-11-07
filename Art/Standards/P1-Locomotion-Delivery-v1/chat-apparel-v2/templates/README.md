# 给Chat的母版模板

- `starlightArmor-master.json.template`、`dragonArmor-master.json.template`：每件五view×四层，共20项，ID独立。
- `master-delivery-plan-40.csv`：两件共40项静态母版，owner=Chat。按实际进度填写，不是已经做好。
- `handoff-record.json`：选型、能力、C阶段、真实文件、缺项、自查与认可。默认未开始，不填假pass。

母版清单kind为`p1-apparel-masters`，不是运行时asset.json。只登记静态母版与存在的源文件。模板中的目标PNG/源稿尚未制作，不能改扩展名就当成交付；可编辑格式与清单同步成实际ORA/PSD/SVG。

无护裙时在该view的`transparentLayers`声明原因，仍提供透明PNG；不能用空白替代缺失袖子/衣身。需要时最多补三个右向静态view，写明原因。

104绑定/416引用与两件832行导出计划位于`../integration/`，是Codex程序输出；**不要把那个表派给Chat逐张画。**
