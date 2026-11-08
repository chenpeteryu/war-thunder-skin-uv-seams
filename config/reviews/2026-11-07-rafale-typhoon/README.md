# 阵风/现代台风提取批次

提取日期 2026-11-07；整理发布 2026-11-08。主要入口为 [型号差异与复核说明](../../docs/rafale_typhoon_layouts.md)。

- `source_inventory.json`：79 张最终布局的原件哈希与清单；实际文件在仓库 `aircraft/`。
- `unit_model_bindings.json`：当前官方载具配置的模型字段、贴图替换摘录和来源哈希；原始配置仅在本地工作区保留。
- `model_probe.json`：原生部件、材质和顶点流格式。本批均无蒙皮部件，没有套用 J16 专用字段修正。
- `variant_comparison.json`：16 组主贴图比较、逐部件 UV 与 UV/XYZ 签名及共同附件比较。UV 相同不等于物理几何相同。
- `renders/`、`sheets/`、`visual_review.json`：112 张色块模拟、相机、材质排除及已查看的汇总图记录。
- `exterior/`：静态可见性筛选的主贴图树输入，原始 UV 未改写。
- `seam_links.sqlite3`、`reports/`、`independent_seam_validation.json`：八套主树、单像素短线和独立数值校验。
- `texel_probes_alpha/`：64 个严格内点的纹素回读，全部通过；不是全库逐像素保证。

## 独立工作目录中复现

工具脚本在 `tools/`。先用已有 UV kit 和游戏路径运行 `extract_native.py --kit-tools KIT_TOOLS --game GAME --out WORK`，再以相同参数运行 `finalize_native.py`。它们只在 WORK 写入提取结果。

随后运行 `blender -b --python tools/render_review.py -- --root WORK`，产生完整不透明材质色块图及 `WORK/exterior`；通过仓库 `config/tools/build_seam_db.py --inputs WORK/exterior --output WORK/seam_links.sqlite3 --models rafale_c_f3 rafale_m_f3_r ef_2000_block_10 ef_2000_aesa f_2000a f_2000a_aesa typhoon_fgr4 typhoon_aesa` 建树。脚本路径应按当前工作目录填写完整路径。

纹素诊断使用 `blender -b --python tools/render_texel_probes.py -- --root WORK --interior --transparent`，再运行 `python tools/verify_texel_probes.py --root WORK --transparent`。比较脚本支持 `--library` 指向仓库根目录或提取工作目录内的 `library`。

提取器版本字段包含此前记录的后端提交号，并明确标注当前本机 Git 元数据无法读取；不把旧版本记录当成本轮重新验证的版本。原生资源入口哈希、数组哈希和格式探测另行保留。动画、逐纹素 alpha、透明材质和游戏内效果仍未验证。
