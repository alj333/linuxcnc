#!/usr/bin/env python3

import argparse
from pathlib import Path

import vtk


def count_polys(path: Path) -> int:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    return reader.GetOutput().GetNumberOfPolys()


def reduce_stl(src: Path, dst: Path, target_reduction: float) -> tuple[int, int]:
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(src))

    clean = vtk.vtkCleanPolyData()
    clean.SetInputConnection(reader.GetOutputPort())

    triangle = vtk.vtkTriangleFilter()
    triangle.SetInputConnection(clean.GetOutputPort())

    decimate = vtk.vtkQuadricDecimation()
    decimate.SetInputConnection(triangle.GetOutputPort())
    decimate.SetTargetReduction(target_reduction)
    decimate.VolumePreservationOn()

    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(decimate.GetOutputPort())
    normals.ConsistencyOn()
    normals.SplittingOff()

    writer = vtk.vtkSTLWriter()
    writer.SetInputConnection(normals.GetOutputPort())
    writer.SetFileName(str(dst))
    writer.SetFileTypeToBinary()
    writer.Write()

    return count_polys(src), count_polys(dst)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reduce STL triangle count with VTK.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--suffix",
        default="_reduced",
        help="Suffix added before the .stl extension.",
    )
    parser.add_argument(
        "--target-reduction",
        type=float,
        default=0.65,
        help="Fraction of triangles to remove. 0.65 keeps about 35%%.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    stl_files = sorted(args.input_dir.glob("*.stl"))
    if not stl_files:
        raise SystemExit(f"No STL files found in {args.input_dir}")

    for src in stl_files:
        dst = args.output_dir / f"{src.stem}{args.suffix}{src.suffix}"
        before_polys, after_polys = reduce_stl(src, dst, args.target_reduction)
        before_size = src.stat().st_size
        after_size = dst.stat().st_size
        print(
            f"{src.name}: polys {before_polys} -> {after_polys}, "
            f"size {before_size} -> {after_size}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
