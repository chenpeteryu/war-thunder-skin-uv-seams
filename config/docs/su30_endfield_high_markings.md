# SM / SM2 的 ENDFIELD HIGH 标识布局

2026-11-07 定稿。参考 J-16 HIGH 的文字层级，不复用 J-16 专属编号、名称及中国厂商标识。这是本次艺术涂装的布局配方，不代表真实部队涂装规范。

|位置|文字|效果|
|---|---|---|
|机鼻|SUKHOI|斜线栅格，唯一 SUKHOI 文字源|
|垂尾大字|SU-30|竖线栅格|
|垂尾小字|IRKUTSK / AVIATION PLANT|两行实心|
|翼根说明|IRKUTSK / AVIATION / PLANT|三行实心|
|原上方小厂标|IRKUTSK|实心|
|完整型号|SU-30SM / SU-30SM2|保留已确认的位置|
|原短编号|30SM / 30SM2|机身、尾翼与翼面实心，平尾为斜线栅格|
|ENDFIELD|原图保留|实心、栅格和图形都不重新替换|

SUKHOI 是设计品牌，IRKUTSK AVIATION PLANT 是生产厂。厂商关系依据 [Rostec 的 SM2 介绍](https://rostec.ru/media/news/istrebitel-su-30sm2-gospodstvo-v-vozdukhe/)及[生产厂官方说明](https://yakovlev.ru/press-centre/releases/irkutskomu-aviatsionnomu-zavodu-90-let/)。不要把当前企业隶属关系改写为飞机型号，也不要将两机改称出口型 SME。

## 可复用数据

- [SM 配方](../recipes/su30sm_endfield_high_markings.json)
- [SM2 配方](../recipes/su30sm2_endfield_high_markings.json)
- [本轮复检记录及相机参数](../reviews/2026-11-07/su30_endfield_high.json)
- [配方检查结果](../reviews/2026-11-07/marking_recipe_validation.json)

每机 15 个记录包含 14 个身份标识位置和 1 个原图保护区；最后一次修订仅修改其中 4 处。配方同时保存 1536 参考坐标、4096 制作坐标及 UV，矩形采用左上原点和半开区间，整数化为 nearest / ties-to-even。大字多边形还必须按指定垂尾/方向舵原生几何筛选裁剪；它不是可直接整块填色的通用 UV 岛。显式 ENDFIELD 保护区并非全机所有标识的完整清单，其他现有 ENDFIELD 也必须保留。

```powershell
python config/tools/validate_marking_recipes.py
```

## 修订中确认的问题

1. 不能把 AVIC、NORINCO 等全部替换成相同的 SUKHOI：同一尾翼的大字与小厂标应分配不同含义，全机也需检查重复密度。
2. 对照源图确认文字本身。曾把栅格 ENDFIELD 误记为 STYLE 小字；已恢复原图并加入明确保护区。
3. 保留文字的原有效果。机鼻和平尾用斜线栅格，尾翼大字用竖线栅格，翼面短编号为实心；栅格在最终旋转/缩放之后生成，避免缩放后变成实心。
4. 清理厂商大字要覆盖旧字边缘，并使用原始清晰涂层重建连续双色底色。不能把已经替换过的字或残留碎斑继续当作底色样本。
5. 不明区域可用独立临时色块、编号、方向箭头逐级定位。先粗后细，补查背面和遮挡，再按物理表面限制编辑范围；色块不得进入交付贴图。

## 验证边界

两机当前原生主几何 XYZ / UV 数组与库中对应数据完全相等，383448 / 384192 个三角形，未修改轮廓、几何、接缝或 UV。本轮每机重新生成 84 个彩色视角、12 个去辅助部件遮挡视角；此前 42 个中性法线视角因 `_n` 及重建法线输入逐字节未变而沿用。最后四处文字范围外的像素、原型号和 ENDFIELD 均保持不变。

本次 SM/SM2 的局部 `_n` 解码核对为 X=A、Y=G、Z 重建；不将此结论推广为全库所有 shader 的通道定义，也不改变统一目录中尚待独立验证的 `_n` 布局状态。Blender 中性法线检查没有模拟完整 Dagor 的 R/B 材质响应。尚未验证游戏、动画、损伤和其他 LOD。仓库只发布位置、规则、参数与验证摘要，不包含原始 DDS 或涂装成品图。

投射、连续性与舱门涂层的前置处理数据见[表面适配配方](su30_surface_adaptation.md)；文字位置配方本身不等于完整的跨机体自动贴合流程。
