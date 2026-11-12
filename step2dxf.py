#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""STEP -> DXF 批量转换（按板厚分组）

用法:
    python step2dxf.py <STEP文件或目录>... [-o 输出目录]

做法:
  每个实体取面积最大的平面作为切割面（外轮廓+内孔），沿其法向压成 2D；
  厚度 = 实体沿法向的包围盒尺寸，输出到 <out>/T{厚度}mm/ 下。
  一个 STEP 里有多个实体时，文件名加 _1 _2 ... 后缀。
"""
import argparse
import math
import sys
from pathlib import Path

import cadquery as cq
from cadquery.occ_impl.exporters.dxf import DxfDocument

Z = cq.Vector(0, 0, 1)
ORIGIN = cq.Vector(0, 0, 0)


def load_solids(path: Path):
    return cq.importers.importStep(str(path)).solids().vals()


def align_to_z(shape, normal):
    """绕原点旋转，使 normal 方向转到 +Z。"""
    axis = normal.cross(Z)
    if axis.Length < 1e-9:                      # 已平行 (±Z)
        return shape if normal.z > 0 else shape.rotate(ORIGIN, cq.Vector(1, 0, 0), 180)
    return shape.rotate(ORIGIN, axis, math.degrees(normal.getAngle(Z)))


def flat_face(solid):
    """返回 (面, 板厚)；没有平面就返回 (None, None)。"""
    faces = [f for f in solid.Faces() if f.geomType() == "PLANE"]
    if not faces:
        return None, None
    face = max(faces, key=lambda f: f.Area())
    n = face.normalAt()
    thick = align_to_z(solid, n).BoundingBox().zlen
    return align_to_z(face, n), thick


def export_dxf(face, thick, out: Path):
    face = face.translate((0, 0, -face.BoundingBox().zmin))   # 压到 Z=0
    layer = f"T{thick:.2f}"
    # ponytail: approx="arc" 绕开 cadquery 2.8 _dxf_spline 对裸 Shape 的 plane 未定义 bug
    dxf = DxfDocument(approx="arc", tolerance=1e-3)
    dxf.add_layer(layer)
    dxf.add_shape(face, layer)
    dxf.document.saveas(str(out))


def iter_steps(inputs):
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            yield from sorted(p.rglob("*.st[ep]*"))
        elif p.suffix.lower() in (".step", ".stp"):
            yield p


def main():
    ap = argparse.ArgumentParser(description="STEP -> 按板厚分组的 DXF")
    ap.add_argument("inputs", nargs="+", help="STEP 文件或目录")
    ap.add_argument("-o", "--out", default=None,
                    help="输出目录；不填则每个输入旁边生成 dxf_out/")
    args = ap.parse_args()

    total = ok = 0
    used = set()                               # 防不同子目录同名零件互相覆盖
    for item in args.inputs:
        p = Path(item)
        out_root = Path(args.out) if args.out else \
            (p if p.is_dir() else p.parent) / "dxf_out"
        for step in iter_steps([item]):
            total += 1
            try:
                solids = load_solids(step)
            except Exception as e:              # noqa: BLE001
                print(f"[跳过] {step.name}: 读入失败 {e}")
                continue
            for i, solid in enumerate(solids, 1):
                face, thick = flat_face(solid)
                if face is None:
                    print(f"[跳过] {step.name}#{i}: 无平面（曲面件）")
                    continue
                sub = out_root / f"T{thick:.2f}mm"
                sub.mkdir(parents=True, exist_ok=True)
                name = step.stem + (f"_{i}" if len(solids) > 1 else "")
                dst, n = sub / f"{name}.dxf", 2
                while dst in used:
                    dst, n = sub / f"{name}_{n}.dxf", n + 1
                used.add(dst)
                try:
                    export_dxf(face, thick, dst)
                except Exception as e:          # noqa: BLE001
                    print(f"[失败] {step.name}#{i}: {e}")
                    continue
                ok += 1
                print(f"[OK] {dst}  ({thick:.2f}mm)")

    print(f"\n完成: {ok} 个实体 -> DXF（共 {total} 个文件）")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
