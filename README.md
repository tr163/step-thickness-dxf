# STEP → DXF 批量转换（按板厚分组）

把 STEP / STP 里的平板类实体压平成切割轮廓 DXF，**按板厚自动分文件夹**，直接丢给激光切割 / CNC。

```
输入  bracket.step (+ 装配体也行)
输出  dxf_out/
      ├─ T1.00mm/bracket.dxf
      ├─ T2.00mm/bracket_1.dxf
      └─ T3.00mm/bracket_2.dxf
```

每个 DXF = 一个零件的切割轮廓（外轮廓 + 所有孔），单位 mm，1:1。

## 用法

把 STEP 文件（可多选）或整个文件夹，拖到 `拖到这里转DXF.bat` 上，等黑窗口跑完。
DXF 生成在拖进来的文件/文件夹旁边的 `dxf_out`。

命令行：

```bash
python step2dxf.py 零件.step
python step2dxf.py 图纸目录 -o 输出目录
```

## 安装

需要 Python 3.10+ 和 cadquery 2.8.0（OCP 很大，装起来慢是正常的）：

```bash
pip install -r requirements.txt
```

`python/` 是一个自带全套依赖的便携解释器（1.3 GB），**不在仓库里**。
放了它 bat 会优先用它，什么都不用装；没有就退回到系统的 `python`。

## 原理

每个实体取**面积最大的平面**作为切割面，沿其法向压成 2D 导出；
板厚 = 实体沿该法向的包围盒尺寸，写进文件夹名和 DXF 图层名。

## 已知限制

- 只适合平板类零件：钣金、碳板、玻纤板、亚克力、木板
- 曲面件没有平面 → 跳过并提示
- 车削件（螺丝、轴）导出的是端面轮廓，不是侧视图
- 装配体里的垫片、螺钉也会各出一个 DXF，切割前删掉那些怪厚度文件夹即可
- 一个 STEP 多个实体 → `名字_1.dxf`、`名字_2.dxf`

## 许可

MIT
