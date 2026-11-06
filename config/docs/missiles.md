# 已制作导弹的整理范围

复用既有轮廓，27 个原生型号、29 张贴图布局：

- PL-12、PL-12A、PL-8、PL-8B、LD-10。
- R-77、R-77-1、R-27R/T/ER/ET、R-73、R-73L。
- AIM-120A/B/C/D、AAM-4、MICA EM/IR、Derby、R-Darter。
- Kh-29L/T、Kh-38ML/MT、Grom-E1。

Kh-29L 与 Kh-38ML 各有一张独立网格辅贴图。共享贴图名的型号仍保存独立几何，不按名称合并空间坐标。

## 来源与历史制作

[来源索引](../evidence/missiles_previous/source_evidence.json)保留资源入口、解析器版本和来源哈希。[历史轮廓校验](../evidence/missiles_previous/original_kit_validation.json)覆盖当时整套 30 型/100 张库，不能误读为本次导弹的新渲染报告。

[逐型号清单](../evidence/missiles_previous/inventory.json)区分轮廓和历史 HIGH v2 成品贴图。HIGH v2 当时制作 32 张 DDS，安装 24 个文件，不等于所有轮廓型号都做过 HIGH v2 涂装。[HIGH v2 说明](../evidence/missiles_previous/high_v2_README_ZH.md)、[校验](../evidence/missiles_previous/high_v2_validation_v2.json)和制作代码保留供回查，其中本机路径是历史来源，不是通用运行配置。

PL-12A 的历史 UV 恒等映射和投影诊断示例保存在同一证据目录，仅是单个示例，不能据此断言全部导弹已重新模拟渲染。

## 当前接缝数据库

每张贴图独立保存到 `config/data/missile_seams/型号/贴图/seam_links.sqlite3`，使用该贴图制作分辨率，不统一强制到 8192。所有原生 UV 三角形与重叠岛保留，未做外表面筛选。极小而无法独立取样的分区保留于几何数据，在树中标明不参与像素定位。

单像素短线只存数据库，每侧 1–7 个采样点。精确共边、共顶点、近邻间隙和装配定位参考分别记录。装配参考两侧是不同空间点，不能把局部切平面变换当作曲面的无缝延伸。`needs_review`、`anchor_error_px` 和空间间距仍需结合实际制作复核。

本次检查原件一致性、几何哈希、边界端点、CSV 像素换算、树连通/无环、短线连续与回算。未新增全体导弹全视角渲染、游戏内测试或 `_n` 独立验证。`_n` 按用户约定暂按共用布局，使用时模拟渲染确认。
