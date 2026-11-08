# ef_2000_block_10

原生型号：`ef_2000_block_10`。

`_c` 布局已收录；`_n` 暂按共用布局处理，实际制作时用模拟渲染确认。

| 贴图 | 制作尺寸 | 轮廓与坐标 |
|---|---|---|
| `de_1000l_ef2000_drop_tank_c` | 1024×1024 | [编号图](de_1000l_ef2000_drop_tank_c/island_ids.png) · [轮廓](de_1000l_ef2000_drop_tank_c/outline.svg) · [边界坐标](de_1000l_ef2000_drop_tank_c/boundary_coordinates.csv) · [来源](de_1000l_ef2000_drop_tank_c/metadata.json) |
| `ef_2000_block_10_c` | 2048×2048 | [编号图](ef_2000_block_10_c/island_ids.png) · [轮廓](ef_2000_block_10_c/outline.svg) · [边界坐标](ef_2000_block_10_c/boundary_coordinates.csv) · [来源](ef_2000_block_10_c/metadata.json) |
| `ef_2000_block_10_itspl_launcher_c` | 512×256 | [编号图](ef_2000_block_10_itspl_launcher_c/island_ids.png) · [轮廓](ef_2000_block_10_itspl_launcher_c/outline.svg) · [边界坐标](ef_2000_block_10_itspl_launcher_c/boundary_coordinates.csv) · [来源](ef_2000_block_10_itspl_launcher_c/metadata.json) |
| `ef_2000_block_10_pylon1_c` | 512×128 | [编号图](ef_2000_block_10_pylon1_c/island_ids.png) · [轮廓](ef_2000_block_10_pylon1_c/outline.svg) · [边界坐标](ef_2000_block_10_pylon1_c/boundary_coordinates.csv) · [来源](ef_2000_block_10_pylon1_c/metadata.json) |
| `ef_2000_block_10_pylon2_c` | 512×256 | [编号图](ef_2000_block_10_pylon2_c/island_ids.png) · [轮廓](ef_2000_block_10_pylon2_c/outline.svg) · [边界坐标](ef_2000_block_10_pylon2_c/boundary_coordinates.csv) · [来源](ef_2000_block_10_pylon2_c/metadata.json) |
| `ef_2000_block_10_pylon3_c` | 512×512 | [编号图](ef_2000_block_10_pylon3_c/island_ids.png) · [轮廓](ef_2000_block_10_pylon3_c/outline.svg) · [边界坐标](ef_2000_block_10_pylon3_c/boundary_coordinates.csv) · [来源](ef_2000_block_10_pylon3_c/metadata.json) |
| `ef_2000_block_10_pylon_central_c` | 512×256 | [编号图](ef_2000_block_10_pylon_central_c/island_ids.png) · [轮廓](ef_2000_block_10_pylon_central_c/outline.svg) · [边界坐标](ef_2000_block_10_pylon_central_c/boundary_coordinates.csv) · [来源](ef_2000_block_10_pylon_central_c/metadata.json) |
| `litening_2_pod_c` | 1024×1024 | [编号图](litening_2_pod_c/island_ids.png) · [轮廓](litening_2_pod_c/outline.svg) · [边界坐标](litening_2_pod_c/boundary_coordinates.csv) · [来源](litening_2_pod_c/metadata.json) |
| `mfrl_launcher_c` | 2048×256 | [编号图](mfrl_launcher_c/island_ids.png) · [轮廓](mfrl_launcher_c/outline.svg) · [边界坐标](mfrl_launcher_c/boundary_coordinates.csv) · [来源](mfrl_launcher_c/metadata.json) |

[阵风/台风型号差异、共用关系与复核范围](../../config/docs/rafale_typhoon_layouts.md)。附件布局保留原生坐标，未逐项做外观复核。

从仓库根目录查询主贴图单像素树：

```powershell
python config/tools/query_seams.py --db config/reviews/2026-11-07-rafale-typhoon/seam_links.sqlite3 --model ef_2000_block_10
```
