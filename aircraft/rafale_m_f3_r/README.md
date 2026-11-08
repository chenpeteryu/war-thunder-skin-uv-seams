# rafale_m_f3_r

原生型号：`rafale_m_f3_r`。

`_c` 布局已收录；`_n` 暂按共用布局处理，实际制作时用模拟渲染确认。

| 贴图 | 制作尺寸 | 轮廓与坐标 |
|---|---|---|
| `damocles_pod_c` | 1024×1024 | [编号图](damocles_pod_c/island_ids.png) · [轮廓](damocles_pod_c/outline.svg) · [边界坐标](damocles_pod_c/boundary_coordinates.csv) · [来源](damocles_pod_c/metadata.json) |
| `net_f_c` | 256×256 | [编号图](net_f_c/island_ids.png) · [轮廓](net_f_c/outline.svg) · [边界坐标](net_f_c/boundary_coordinates.csv) · [来源](net_f_c/metadata.json) |
| `pylon_rafale_adp_192_c` | 1024×512 | [编号图](pylon_rafale_adp_192_c/island_ids.png) · [轮廓](pylon_rafale_adp_192_c/outline.svg) · [边界坐标](pylon_rafale_adp_192_c/boundary_coordinates.csv) · [来源](pylon_rafale_adp_192_c/metadata.json) |
| `pylon_rafale_central_c` | 2048×512 | [编号图](pylon_rafale_central_c/island_ids.png) · [轮廓](pylon_rafale_central_c/outline.svg) · [边界坐标](pylon_rafale_central_c/boundary_coordinates.csv) · [来源](pylon_rafale_central_c/metadata.json) |
| `pylon_rafale_fuse_mica_c` | 2048×512 | [编号图](pylon_rafale_fuse_mica_c/island_ids.png) · [轮廓](pylon_rafale_fuse_mica_c/outline.svg) · [边界坐标](pylon_rafale_fuse_mica_c/boundary_coordinates.csv) · [来源](pylon_rafale_fuse_mica_c/metadata.json) |
| `pylon_rafale_mica_aux_c` | 1024×512 | [编号图](pylon_rafale_mica_aux_c/island_ids.png) · [轮廓](pylon_rafale_mica_aux_c/outline.svg) · [边界坐标](pylon_rafale_mica_aux_c/boundary_coordinates.csv) · [来源](pylon_rafale_mica_aux_c/metadata.json) |
| `pylon_rafale_mica_aux_rail_c` | 1024×256 | [编号图](pylon_rafale_mica_aux_rail_c/island_ids.png) · [轮廓](pylon_rafale_mica_aux_rail_c/outline.svg) · [边界坐标](pylon_rafale_mica_aux_rail_c/boundary_coordinates.csv) · [来源](pylon_rafale_mica_aux_rail_c/metadata.json) |
| `pylon_rafale_mica_c` | 1024×512 | [编号图](pylon_rafale_mica_c/island_ids.png) · [轮廓](pylon_rafale_mica_c/outline.svg) · [边界坐标](pylon_rafale_mica_c/boundary_coordinates.csv) · [来源](pylon_rafale_mica_c/metadata.json) |
| `pylon_rafale_pu_708_c` | 1024×256 | [编号图](pylon_rafale_pu_708_c/island_ids.png) · [轮廓](pylon_rafale_pu_708_c/outline.svg) · [边界坐标](pylon_rafale_pu_708_c/boundary_coordinates.csv) · [来源](pylon_rafale_pu_708_c/metadata.json) |
| `pylon_rafale_wing_c` | 2048×512 | [编号图](pylon_rafale_wing_c/island_ids.png) · [轮廓](pylon_rafale_wing_c/outline.svg) · [边界坐标](pylon_rafale_wing_c/boundary_coordinates.csv) · [来源](pylon_rafale_wing_c/metadata.json) |
| `rafale_m_f3_r_c` | 4096×4096 | [编号图](rafale_m_f3_r_c/island_ids.png) · [轮廓](rafale_m_f3_r_c/outline.svg) · [边界坐标](rafale_m_f3_r_c/boundary_coordinates.csv) · [来源](rafale_m_f3_r_c/metadata.json) |
| `seat_martin_baker_mk15f_c` | 1024×1024 | [编号图](seat_martin_baker_mk15f_c/island_ids.png) · [轮廓](seat_martin_baker_mk15f_c/outline.svg) · [边界坐标](seat_martin_baker_mk15f_c/boundary_coordinates.csv) · [来源](seat_martin_baker_mk15f_c/metadata.json) |
| `talios_pod_c` | 1024×1024 | [编号图](talios_pod_c/island_ids.png) · [轮廓](talios_pod_c/outline.svg) · [边界坐标](talios_pod_c/boundary_coordinates.csv) · [来源](talios_pod_c/metadata.json) |

[阵风/台风型号差异、共用关系与复核范围](../../config/docs/rafale_typhoon_layouts.md)。附件布局保留原生坐标，未逐项做外观复核。

从仓库根目录查询主贴图单像素树：

```powershell
python config/tools/query_seams.py --db config/reviews/2026-11-07-rafale-typhoon/seam_links.sqlite3 --model rafale_m_f3_r
```
