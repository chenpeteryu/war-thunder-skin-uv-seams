# 战雷涂装轮廓库

飞机、导弹分组存放，配置、代码和复核证据集中存放。下载仓库后打开 [index.html 离线索引](index.html)，可按分类、型号和贴图名搜索。

```text
aircraft/                 飞机
  f15ex/ su30sm/ su30sm2/ j15t/ j16/ j10c/ …
  rafale_c_f3/ rafale_m_f3_r/ ef_2000_block_10/ typhoon_fgr4/ …
missiles/                 导弹
  pl12/ pl12a/ r77/ aim120a/ ……
config/                   配置文件、代码和证据
  catalog.json            统一目录，path 以仓库根目录为基准
  catalog.csv
  tools/                  查询、映射、模拟渲染、建库和校验
  data/                   初版飞机数据库及导弹分贴图接缝数据库
  recipes/                J15T 修正配方与 SM/SM2 标识布局配方
  reviews/                各批飞机复核数据库、模拟图和证据
  evidence/               已制作导弹的来源、历史校验与代码
  docs/                   方法、限制和型号差异
README.md                 使用说明
index.html                离线索引
```

飞机 14 套原生模型、186 张布局；导弹 27 型、29 张布局，共 215 张。希腊阵风入口复用 C 的同一模型，保留载具和贴图别名。目录使用短型号名，原生模型名与贴图名保留在目录表和元数据中。同贴图名不代表三维几何相同，MICA EM/IR、PL-8/8B、R-27 各型等均独立保存。

每张布局提供矢量/图片轮廓、覆盖蒙版、分区编号图、边界/分区坐标、原始 UV/XYZ 数据及来源。制作尺寸与原生贴图尺寸可能不同，应读取该张 `metadata.json`。坐标为 `x=u×W, y=(1-v)×H`，纹素中心为 `x+0.5,y+0.5`。

目前收录 `_c` 轮廓。`_n` 暂按共用布局处理，实际制作时再通过模拟渲染确认绑定、覆盖和像素对齐，未标记为已独立验证。

复用前请阅读[复用提醒与已遇到的易错点](config/docs/pitfalls.md)，包括来源机体专属特征的区分、已确认轮廓库错误的修正及 GitHub 同步。

## 接缝定位与模拟渲染

保留此前的细小单像素连线方法：每条连接两侧各宽 1 像素、1–7 个采样点，只存 SQLite，不画入涂装、轮廓或渲染图。每张导弹贴图独立建立可遍历树；`assembly_reference` 是跨部件间隙的定位参考，不是物理共边。分区上各短线无需彼此相连。亚像素误差、待复核标记与空间距离均保留。

Python 3.11+，从仓库根目录运行：

```powershell
python -m pip install -r config/requirements.txt
python config/tools/query_seams.py --db config/data/missile_seams/pl12a/pl_12a_missile_c/seam_links.sqlite3 --model pl_12a_missile
python config/tools/validate_seam_db.py --db config/data/missile_seams/pl12a/pl_12a_missile_c/seam_links.sqlite3
python config/tools/query_seams.py --db config/reviews/2026-11-06/data/seam_links.sqlite3 --model su_30sm
python config/tools/validate_library.py
```

`map_design.py --help` 提供图案到原生 UV 的映射，支持短型号名或原生型号名。`render_preview.py` 由 Blender 运行，读取所选布局的 `geometry.npz` 与指定诊断贴图；见 [模拟渲染说明](config/docs/rendering.md)。重建导弹短线库可运行 `python config/tools/build_missile_seams.py --model pl12a`，写入对应数据库，不修改轮廓或贴图。

## 验证范围

- 新增[阵风/现代台风轮廓及型号差异](config/docs/rafale_typhoon_layouts.md)：9 个载具入口对应 8 套原生模型、79 张布局。希腊阵风与 C 共用，M 及台风六套模型因存在差异独立保存；112 张色块模拟图已检查，64 个所选纹素回读通过。

- J15T 保留反复修正后的主贴图基准。J16/J10C 保留独立复核及已记录修正，不因曾用于参考而宣称整库像素级精准。
- [SM/SM2 差异说明](config/docs/su30sm_sm2_layout_comparison.md)：机身、左右前缘缝翼和部分外挂有差异，保留两套。
- 导弹复用既有原生 LOD0 轮廓，逐文件核对原件，检查几何/坐标并建立分贴图短线树。[历史制作范围和限制](config/docs/missiles.md)单独记录。HIGH v2 涂装制作与轮廓提取分别记录，不把 27 个轮廓型号等同于 27 套 HIGH v2 成品。
- 导弹树保留整张贴图原生几何，未做飞机库那样的外表面可见性筛选。单分区辅贴图树连接数为零。结构、坐标、完整性检查通过不等于整库逐像素或游戏外观已验证。
- 飞机的[验收范围](config/reviews/2026-11-06/验收范围.md)和所选模拟渲染证据保留。动画、损伤、玻璃及实际游戏材质等仍以游戏内测试为准。

原目录迁移关系见 [path_migration.json](config/path_migration.json)。历史报告内的绝对路径保留为来源证据，当前入口以统一目录表和本说明为准。迁移前版本可通过 Git 历史 `d076ec5` 回查。

工具为本项目编写；UV/几何派生自本机游戏资源，游戏资源权利归其权利人。本仓库不包含原版 DDS、GRP、完整引擎模型或账号凭据。
