from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .excel_writer import write_excel
from .pipeline import process_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image2excel",
        description="从多张学生信息照片中提取姓名和学号并输出 Excel。",
    )
    parser.add_argument(
        "images",
        type=Path,
        nargs="+",
        help="图片路径，按命令行参数顺序作为第1页、第2页……处理",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Excel 输出路径，默认保存到第1张图片所在目录，"
            "文件名为image2excel_YYYYMMDD_HHMMSS.xlsx"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="允许覆盖已经存在的输出文件",
    )
    parser.add_argument(
        "--columns",
        type=int,
        default=5,
        help="固定列数，默认5列",
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        default=7,
        help="完整页面的预期行数，仅用于无锚点时的回退，默认7行",
    )
    parser.add_argument(
        "-o",
        "--orientation",
        default="auto",
        help=(
            "图片方向：auto、0、90、180、270或-90（-90等同于270）；单个值应用于全部图片，"
            "也可用逗号按图片顺序指定，例如0,90,auto"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = args.images

    try:
        _validate_inputs(paths, args.columns, args.expected_rows)
        orientations = parse_orientation_spec(args.orientation, len(paths))
        output = args.output or _default_output_path(paths[0], args.overwrite)
        if output.exists() and not args.overwrite:
            raise FileExistsError(
                f"输出文件已存在：{output}。如需覆盖，请添加 --overwrite。"
            )

        print("正在加载本地 OCR 模型；如果本地缓存不存在，首次运行会自动下载模型文件……")
        records = process_images(
            paths,
            columns=args.columns,
            expected_rows=args.expected_rows,
            orientations=orientations,
            progress=_print_progress,
        )
        write_excel(records, output)
        normal = sum(record.status == "正常" for record in records)
        review = len(records) - normal
        print(f"处理完成：共识别 {len(records)} 条记录，正常 {normal} 条，待复核 {review} 条。")
        print(f"Excel：{output}")
        return 0
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


def _validate_inputs(paths: list[Path], columns: int, expected_rows: int) -> None:
    if columns <= 0:
        raise ValueError("列数必须大于0。")
    if expected_rows <= 0:
        raise ValueError("预期行数必须大于0。")
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f"图片不存在：{path}")
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}:
            raise ValueError(f"不支持的图片格式：{path}")


def _print_progress(message: str) -> None:
    print(message, flush=True)


def parse_orientation_spec(value: str, image_count: int) -> list[int | None]:
    """Parse one shared orientation or one orientation per image."""
    tokens = [token.strip().lower() for token in value.split(",")]
    if not tokens or any(not token for token in tokens):
        raise ValueError("方向参数不能为空，支持auto、0、90、180、270、-90。")
    if len(tokens) not in (1, image_count):
        raise ValueError(
            f"方向参数数量为{len(tokens)}，但图片数量为{image_count}；"
            "请提供一个方向，或为每张图片提供一个方向。"
        )

    if len(tokens) == 1:
        tokens *= image_count

    orientations: list[int | None] = []
    for token in tokens:
        if token == "auto":
            orientations.append(None)
            continue
        try:
            angle = int(token)
        except ValueError as exc:
            raise ValueError(f"无效方向：{token}，支持auto、0、90、180、270、-90。") from exc
        if angle not in (-90, 0, 90, 180, 270):
            raise ValueError(f"无效方向：{token}，支持auto、0、90、180、270、-90。")
        orientations.append(angle % 360)
    return orientations


def _default_output_path(first_image: Path, overwrite: bool = False) -> Path:
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    output = first_image.parent / f"image2excel_{timestamp}.xlsx"
    if overwrite or not output.exists():
        return output

    suffix = 1
    while True:
        candidate = first_image.parent / f"image2excel_{timestamp}_{suffix:02d}.xlsx"
        if not candidate.exists():
            return candidate
        suffix += 1


if __name__ == "__main__":
    raise SystemExit(main())
