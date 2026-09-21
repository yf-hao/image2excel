from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .excel_writer import write_excel
from .pipeline import process_images


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="image2excel",
        description="从两张学生信息照片中提取姓名和学号并输出 Excel。",
    )
    parser.add_argument("image1", type=Path, help="第1张图片")
    parser.add_argument("image2", type=Path, help="第2张图片")
    parser.add_argument(
        "--output",
        type=Path,
        help="Excel 输出路径，默认保存到第1张图片所在目录/image2excel_result.xlsx",
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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = [args.image1, args.image2]

    try:
        _validate_inputs(paths, args.columns, args.expected_rows)
        output = args.output or paths[0].parent / "image2excel_result.xlsx"
        if output.exists() and not args.overwrite:
            raise FileExistsError(
                f"输出文件已存在：{output}。如需覆盖，请添加 --overwrite。"
            )

        print("正在加载本地 OCR 模型；如果本地缓存不存在，首次运行会自动下载模型文件……")
        records = process_images(
            paths,
            columns=args.columns,
            expected_rows=args.expected_rows,
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


if __name__ == "__main__":
    raise SystemExit(main())
