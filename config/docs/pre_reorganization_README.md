# 战雷涂装 UV 接缝与模拟渲染库

## 2026-11-06 静态复核版

新增[独立复核版目录](reviewed/2026-11-06/README.md)：107张布局，包含J15T主贴图基准、J16/J10C复核副本、Su-30SM/SM2和测试服F-15EX。下载仓库后打开[离线轮廓索引](reviewed/2026-11-06/打开轮廓索引.html)。

- J16修正两个蒙皮部件432个三角形的字段解码，默认绑定姿态经261顶点检查；原有基线数据保留。
- J10C分别记录全几何与静态外表面，补充独立喷口树。
- [SM/SM2比较](docs/su30sm_sm2_layout_comparison.md)：主贴图大部分共用布局，但机身、左右前缘缝翼及部分挂架/吊舱有差异，保留两套。
- 新主树使用机体静态可见性，包含J16 2236、J10C 728、SM 1591、SM2 1594、F15EX 1828个可定位分区；每树连接数为分区数减1。J15T基准仍为原版数据。
- 单像素短线仍只保存于数据库；主树57292采样、辅树7368采样通过结构验证。所选48个纹素回读通过，不扩大为全库像素级精准结论。

查询新版时显式指定数据库：

```powershell
python tools/query_seams.py --db reviewed/2026-11-06/data/seam_links.sqlite3 --model su_30sm
python tools/validate_seam_db.py --db reviewed/2026-11-06/data/seam_links.sqlite3
```

详细[验收范围与限制](reviewed/2026-11-06/验收范围.md)随库保存。透明裁切、部件激活、动画、损伤和实际游戏材质未完成游戏内验证；附件布局未逐项外观审查。

## 初版基线（保留用于回查）

为 J15T、J16、J10C 的机体外表面保存可遍历的接缝定位树。短连线只存于 SQLite，**不画在涂装、轮廓图或渲染图上**。座舱、座椅等内饰不在本次范围内，武器贴图也不在本次数据库范围内。

| 模型 | 外表面 UV 分区 | 树连接 |
|---|---:|---:|
| J15T | 2579 | 2578 |
| J16 | 2892 | 2891 |
| J10C | 787 | 786 |

每个分区是原始 part + island。每个模型只保留一棵生成树：A-B-C 已可遍历时不添加 A-C。每条连接两侧各存一段宽 1 像素、最多 7 个采样像素的短线，它们不必与同一分区上的其他短线相接。

浮点锚点保留亚像素相位；整数短线用于定位。两侧纹素密度不同或边界没有恰好穿过像素中心时，不能宣称两个整数像素是同一空间点。`anchor_error_px` 和 `needs_review` 记录这些例外。真正分离的部件用 `assembly_reference` 联系，保存两侧独立空间坐标和距离，**不是物理共边**。详见 [数据库约定](docs/database.md)。

## 使用

Python 3.11+，安装 `requirements.txt`。已有数据库可直接查询，不需要 Blender。

```powershell
python tools/query_seams.py --model j_15t --chart 1
python tools/query_seams.py --connection 1
python tools/validate_seam_db.py --report data/reports/independent_validation.json
python tools/build_seam_db.py
```

用查询所得的两个 chart ID 可组合树路径：`--chart A --to C --pixel X Y`。增加 `--contacts-only` 可排除跨装配间隙的参考桥，届时不保证全图连通。转换是局部切平面配准，不能代替整片曲面展开。

- [模拟渲染方法](docs/rendering.md)：相机统一、上下与斜角检查、法线诊断和证据边界。
- [易错点](docs/pitfalls.md)：UV 镜像、跨岛采样、内外侧、喷口材质及真实模型间隙。
- `data/geometry/`：静态外表面筛选输入及来源校验值。
- `data/reports/`：连通性、像素连续性、空间回算、转换往返误差的独立检查。
- `recipes/`：本地轮廓库已有修复配方和坐标；不包含整张涂装或 DDS。配方中的 baseline 哈希是其制作时的来源，不代表当前安装文件。

外表面筛选使用几何遮挡测试、双向法线和多个观察方向，并结合已审查的座舱区域排除规则。它是静态近似；动画、玻璃、损伤、游戏材质可见性仍需游戏内确认。数据库验证通过不等于游戏效果已验证。

## 来源与分发

工具为本项目编写。几何与 UV 坐标派生自本机游戏资源，仅供已授权的涂装定位研究；游戏资源权利仍归其权利人。仓库不提供游戏贴图、完整模型、账号凭据或游戏资源的再许可。仓库初次发布设为私有。
