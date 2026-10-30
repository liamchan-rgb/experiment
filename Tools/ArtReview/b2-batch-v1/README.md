# 装备素材审核页

静态HTML/JS/CSS，无构建依赖。把本目录index.html/app.js/style.css放入站点dist，再把Art/Review/Equipment/b2-batch-v1内的清单、PNG与GIF复制到dist/assets。Sites以私有站点发布；具体ID、版本与URL以审核目录deployment.json为准。不要提交凭据或浏览器反馈。

每个清单item可提供walking atlas（13×256宽、8×256高）和battle clip atlas（10列、256格），不需要重新绘制共用人物。新批次用新manifest.id/resourceRevisionSHA256，旧反馈不可自动套用到新资源。用户操作仅写当前浏览器；可导出带物品ID/方向/帧/版本的JSON再反馈。

26合同检查与浏览器交互检查是技术证据，不能自动认可新美术。当前专用权杖施法和demo接入待后续整合。
