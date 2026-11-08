# SM/SM2：原生轮廓与涂装微调的区别

2026-11-07 回溯补录。调用轮廓库并不等于参考涂装自动 100% 贴合。两机实际使用的主几何 XYZ、UV 与库中数据完全一致，没有移动原生轮廓或 UV；修正的是 J-16 设计向不同机体的采样位置、连续性和涂层。

## 实际发生过的适配

1. 初次制作：按同名物理部件匹配来源三角形；机鼻长度差异仅在临时采样位置中校正，方向舵采样按各自源部件的 X/Y 范围归一化。不会写回目标原生模型。
2. 初次制作：翼面、缝翼、襟副翼分开 UV 会破坏直接投射的连续性，因此先制作正反面来源平面，再分别投射两面机翼及四个垂尾侧面。已保存实际选中的原生三角形编号、投影轴、范围、尺寸、方向和相机标定角点。
3. 初次制作：恢复原生机械/光学组件细节，并限制部分细节转移的三角形及来源 UV。历史 `detail_finish.json` 把统计字段命名为 `intake_ramp_*`，实际代码选择 `nozzle3* / nozzle4*`，故本库明确记录原生 part 前缀，不用旧字段名代替物理结构判断。选中 7132 个三角形，历史光栅统计成功处理 2520 个，两者不是同一统计口径。
4. 用户要求全角度复检后：清理来源编号和厂商身份；对起落架/舱门几何上的蓝色涂层做受限灰色处理，同时保留 G/A 结构法线。实际修正蒙版和条件已收录。颜色修正只能从保存的修正前输入执行一次，不应反复在既有成品上叠加羽化处理。
5. 后续文字修订：短编号、厂商分工、ENDFIELD 保护与栅格方向，见[标识布局配方](su30_endfield_high_markings.md)。这些应在图案投射和涂层处理之后执行。

## 配方与实际数据

- [SM 表面适配配方](../recipes/su30sm_surface_adaptation.json)及[三角形/蒙版数据](../recipes/su30sm_surface_adaptation.npz)
- [SM2 表面适配配方](../recipes/su30sm2_surface_adaptation.json)及[三角形/蒙版数据](../recipes/su30sm2_surface_adaptation.npz)
- `config/tools/prepare_sm_design_mapping.py`：从本库对应原生几何重建初次制作的三角形来源 UV 映射；使用项目既有算法，输出到用户指定目录。

```powershell
python config/tools/validate_surface_recipes.py
python config/tools/prepare_sm_design_mapping.py --output PATH_TO_WORKING_OUTPUT
```

NPZ 不包含原始涂装图片。它提供六组连续性三角形索引、受限细节的来源 UV、原生细节保护三角形、连续性范围蒙版，以及复检时实际使用的涂层蒙版。蒙版以 `np.packbits(..., bitorder='little')` 保存，解码后 reshape 为 4096×4096。索引与蒙版仅适用于配方指定的几何 SHA；不能当成其他飞机的通用岛编号。

使用者仍需自行提供有权使用的参考涂装。来源平面按存储标定变换后，可用现有 `map_design.rasterize` 将三维平面采样坐标光栅化到目标原生 UV；不要再手工猜测偏移。新图案需要检查身份内容、材质和渲染，配方不承诺免检自动贴合。

## 为什么不直接改原生轮廓

轮廓错误应修正对应几何派生数据；图案移植、字号排版和涂层处理应保存为明确版本的适配配方。把后者写进原生 UV 会损坏后续其他涂装的定位基础。本次已确认的两机原生 XYZ / UV 无差异，因此补回适配配方，不改动原生轮廓、UV 或接缝坐标。

此前提交 `2ca9754` 主要回写标识布局，本次补齐此前没有完整入库的表面投射、连续性、细节保护与涂层数据。验证范围仍是固定 LOD0 的静态模拟，不代表实际游戏、动画、损伤或其他 LOD 的全状态保证。

## 2026-11-08 fin-joint and reference-slot correction

The schema-2 recipes append per-pixel native-world fin-joint weights, ink protection and allowed repair scopes. See [current repair rules](su30_endfield_high_markings.md) and the geometry-bound arrays. The previous base projection and continuity data remain valid; the old identity layout is superseded. Native geometry and UV are unchanged.
