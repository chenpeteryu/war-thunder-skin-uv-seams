# r_darter

原生型号：`r_darter`。

`_c` 布局已收录；`_n` 暂按共用布局处理，实际制作时用模拟渲染确认。

| 贴图 | 制作尺寸 | 轮廓与坐标 |
|---|---|---|
| `r_darter_c` | 2048×2048 | [编号图](r_darter_c/island_ids.png) · [轮廓](r_darter_c/outline.svg) · [边界坐标](r_darter_c/boundary_coordinates.csv) · [来源](r_darter_c/metadata.json) |

接缝树保留该贴图的全部原生 LOD0 几何，未进行静态外表面筛选。每张贴图独立建树，不虚构跨贴图连接。短线宽 1 像素、每侧 1–7 个采样点，仅存于数据库。

```powershell
python config/tools/query_seams.py --db config/data/missile_seams/r_darter/r_darter_c/seam_links.sqlite3 --model r_darter
```

以上命令从仓库根目录运行。模型分区、空间间隙和亚像素回算不等于游戏内外观验证。
