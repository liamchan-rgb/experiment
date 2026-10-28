# legendaryStaff 接入

原GameCore .equip负责库存交换及合法性，营地试装借用一把权杖，普攻原1D20、技能强击仍1D6+2，自然20原规则不改。独立武器层/图标及两衣装208背负绑定，未以整人图片替代分层。

LegendaryStaffRig读取legendary-staff-v1.json的241个认可曲线采样，持续插值；0.8384秒杖头出手，1.048秒同一受击点一次结算，1.7秒复位。单人/小队共用LegendaryStaffEffects连续采样与MeadowStaffEffectPainter；普通共用身体状态复用，腕角避免遮脸。128纯测试、五旧检查及geometry.json为补充。设备归档/包校验见Media/Build59。无App/模拟器/设备运行。
