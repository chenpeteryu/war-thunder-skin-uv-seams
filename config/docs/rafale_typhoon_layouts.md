# 阵风与现代台风：可复用轮廓及型号差异

提取批次：2026-11-07；整理与上传：2026-11-08。读取本机正式服原生 LOD0，共 9 个载具入口、8 套原生模型、79 张 `_c` 布局。现代 Eurofighter 台风与二战 Hawker Typhoon 分开，本批不包含后者。

## 共用与独立保存

- 阵风 C 与希腊 `rafale_eg_greece`：官方载具配置调用同一 `rafale_c_f3` 模型，希腊型将主贴图替换为 `rafale_eg_greece_c`。两张原生 HQ 颜色贴图均为 4096×4096，因此合并使用 C 的轮廓与空间坐标，保留载具和贴图别名。此结论不表示两套涂装身份文字或标识可直接照搬。
- 阵风 M：与 C 的 208 个部件名中，154 个 UV 三角形集合相同，54 个不同（包含仅一型存在的部件）。差异包括机身、起落架、机轮和着舰钩等，保留独立轮廓和接缝树。
- 台风六套模型：主贴图均存在机身等差异，全部独立保存。意/英四套模型两两比较均为 231 个部件中 230 个 UV 集合相同，剩余 `fuse` 不同；不能因大部分相同就整套合并。德系与其他型号还涉及 `gear_r9`、`gear_r10`、`gun_close` 等，德系常规/AESA 比较还涉及 `optic`、`optic1_gun`、`optic1_turret`。
- 附件即使共用贴图名，装配位置或实际几何仍可能不同，保留逐模型记录；逐贴图对比结果见原始比较报告。

## 载具入口、模型和尺寸

| 载具配置入口 | 原生模型/共用目录 | 主贴图 | 制作尺寸 |
|---|---|---|---|
| `rafale_c_f3` | [`rafale_c_f3`](../../aircraft/rafale_c_f3/README.md) | `rafale_c_f3_c` | 4096×4096 |
| `rafale_m_f3r` | [`rafale_m_f3_r`](../../aircraft/rafale_m_f3_r/README.md) | `rafale_m_f3_r_c` | 4096×4096 |
| `rafale_eg_greece` | [`rafale_c_f3`](../../aircraft/rafale_c_f3/README.md) | `rafale_eg_greece_c` | 4096×4096 |
| `ef_2000_block_10` | [`ef_2000_block_10`](../../aircraft/ef_2000_block_10/README.md) | `ef_2000_block_10_c` | 2048×2048 |
| `ef_2000_aesa` | [`ef_2000_aesa`](../../aircraft/ef_2000_aesa/README.md) | `ef_2000_aesa_c` | 2048×2048 |
| `ef_2000a` | [`f_2000a`](../../aircraft/f_2000a/README.md) | `f_2000a_c` | 2048×2048 |
| `ef_2000a_aesa` | [`f_2000a_aesa`](../../aircraft/f_2000a_aesa/README.md) | `f_2000a_aesa_c` | 2048×2048 |
| `ef_2000_fgr4` | [`typhoon_fgr4`](../../aircraft/typhoon_fgr4/README.md) | `typhoon_fgr4_c` | 2048×2048 |
| `ef_2000_typhoon_aesa` | [`typhoon_aesa`](../../aircraft/typhoon_aesa/README.md) | `typhoon_aesa_c` | 2048×2048 |

目录表和离线索引支持搜索 `rafale_eg_greece` / `rafale_eg_greece_c`，指向 C 的同一布局。`map_design.py` 接受这两个别名；接缝查询使用规范模型 ID `rafale_c_f3`。

## 主贴图逐型号比较

以 1e-6 UV 量化，按原生部件名比较经顶点排序的 UV 三角形集合；同时比较配对 UV/XYZ 集合及原始三角形数量。忽略排列和集合内完全重复项的 UV 相同，不代表物理几何、所有纹素或艺术稿必然相同。只依据 UV 相同不合并不同空间几何。

| 模型 A | 模型 B | 相同 UV 部件/并集部件数 | 不同部件数 |
|---|---|---:|---:|
| `rafale_c_f3` | `rafale_m_f3_r` | 154/208 | 54 |
| `ef_2000_aesa` | `ef_2000_block_10` | 226/230 | 4 |
| `ef_2000_aesa` | `f_2000a` | 227/231 | 4 |
| `ef_2000_aesa` | `f_2000a_aesa` | 227/231 | 4 |
| `ef_2000_aesa` | `typhoon_aesa` | 227/231 | 4 |
| `ef_2000_aesa` | `typhoon_fgr4` | 227/231 | 4 |
| `ef_2000_block_10` | `f_2000a` | 224/231 | 7 |
| `ef_2000_block_10` | `f_2000a_aesa` | 224/231 | 7 |
| `ef_2000_block_10` | `typhoon_aesa` | 224/231 | 7 |
| `ef_2000_block_10` | `typhoon_fgr4` | 224/231 | 7 |
| `f_2000a` | `f_2000a_aesa` | 230/231 | 1 |
| `f_2000a` | `typhoon_aesa` | 230/231 | 1 |
| `f_2000a` | `typhoon_fgr4` | 230/231 | 1 |
| `f_2000a_aesa` | `typhoon_aesa` | 230/231 | 1 |
| `f_2000a_aesa` | `typhoon_fgr4` | 230/231 | 1 |
| `typhoon_aesa` | `typhoon_fgr4` | 230/231 | 1 |

逐部件签名、差异列表及附件比较见 [variant_comparison.json](../reviews/2026-11-07-rafale-typhoon/variant_comparison.json)。[载具绑定](../aircraft_variants.json)、[官方配置摘录与哈希](../reviews/2026-11-07-rafale-typhoon/unit_model_bindings.json)和[资源入口哈希](../reviews/2026-11-07-rafale-typhoon/native_source_evidence.json)保留在库内。结论针对该批资源，不假定后续游戏更新保持相同。

## 渲染、接缝与验证范围

- 8 套模型各 14 个固定视角，共 112 张色块模拟图，已查看全部汇总图。使用完整不透明材质几何作外观诊断，主贴图显示独立 2K 色块，附件为中性颜色；未观察到明显解码拉伸、飞面或轮廓缺失。原始图、相机和材质排除记录位于 [renders](../reviews/2026-11-07-rafale-typhoon/renders)，汇总图位于 [sheets](../reviews/2026-11-07-rafale-typhoon/sheets)。没有发现需要凭外观改写原生 UV 的已确认错误。
- 主贴图分别建立静态可见机体接缝树。完整原生 UV 保存在各布局目录，静态可见性输入单独保存。短线每侧宽 1 像素、1–7 个采样点，仅存数据库，不画进涂装或轮廓；76,623 个采样点通过独立检查。
- 64 个严格位于三角形内部的独立纹素回读全部通过，样本 alpha 均为 255。它们验证所选局部的纹素映射，不是对全库或全部短线逐像素渲染的证明。
- 主贴图尺寸直接取原生 HQ DDSx 头：阵风 4096×4096、台风 2048×2048；没有找到本机用户涂装制作尺寸参考。以后制作更高分辨率时按归一化 UV 换算，不直接套用不同尺寸的整数坐标。
- 静态筛选按面中心从双法线及 26 个方向做可见性检查；玻璃、空材质和效果面排除，部分可选附件按名称排除。未模拟逐纹素 alpha、游戏部件激活、动画、损伤或引擎实际材质。极小分区无法独立取样时不纳入像素树，但原生几何保留。
- `assembly_reference` 是跨空间间隙的定位参考，不是物理接缝；`needs_review`、锚点误差和空间距离保留，不能用树连通性替代无缝涂装验证。附件轮廓已提取和做坐标检查，未逐项外观复核或建立附件接缝树。
- `_n` 继续按既定约定视为待使用时模拟确认的共用布局，不声称已独立验证。未启动游戏。

## 查询与复现

```powershell
python config/tools/query_seams.py --db config/reviews/2026-11-07-rafale-typhoon/seam_links.sqlite3 --model rafale_c_f3
python config/tools/validate_seam_db.py --db config/reviews/2026-11-07-rafale-typhoon/seam_links.sqlite3
python config/reviews/2026-11-07-rafale-typhoon/tools/compare_variants.py --library . --output /PATH/TO/variant_comparison.json
```

比较脚本直接读取本仓库。提取/渲染脚本依赖另行安装的 UV kit / WT Asset Explorer 与 Blender，使用显式 `--kit-tools`、`--game`、`--out` 或 `--root` 指向独立工作目录；不会改写游戏或已安装涂装。具体流程见 [批次说明](../reviews/2026-11-07-rafale-typhoon/README.md)。
