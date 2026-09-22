# image2excel

从学生信息照片中提取座位号、姓名和学号，并输出 Excel。OCR 在本地执行。

## 创建环境

建议使用 Python 3.11：

```bash
git clone https://github.com/yf-hao/image2excel.git
cd image2excel
conda create -n image2excel python=3.11 -y
conda activate image2excel
python -m pip install -e .
```

## 使用

图片参数按页面顺序处理，支持一张或更多图片：

```bash
image2excel image1.jpg image2.jpg
image2excel image1.jpg image2.jpg image3.jpg image4.jpg
```

### 命令参数

```text
image2excel [选项] 图片路径...
```

| 参数 | 默认值 | 说明 |
|---|---|---|
| `images` | 必填 | 一个或多个图片路径，按参数顺序作为第1页、第2页……处理。支持 `.jpg`、`.jpeg`、`.png`、`.bmp`、`.webp` |
| `-o, --orientation` | `auto` | 图片方向。支持 `auto`、`0`、`90`、`180`、`270`、`-90`（`-90` 等同于 `270`）；一个值应用于全部图片，也可以用逗号按图片顺序指定 |
| `--output` | 第1张图片所在目录的 `image2excel_YYYYMMDD_HHMMSS.xlsx` | 指定 Excel 输出路径 |
| `--overwrite` | 关闭 | 允许覆盖已经存在的 Excel 文件 |
| `--columns` | `5` | 固定列数，必须大于0 |
| `--expected-rows` | `7` | 完整页面的预期行数，仅用于没有文字锚点时的回退，必须大于0 |
| `-h, --help` | - | 显示帮助信息 |

默认输出到第一张图片所在目录：

```text
image2excel_20260922_125131.xlsx
```

固定列数默认为 5，行数会根据图片中的文字锚点自动检测。程序支持页面旋转、常见透视变形和只拍到页面局部的情况。

默认文件名使用本地时间，格式为：

```text
image2excel_年月日_时分秒.xlsx
```

同一秒内重复运行时，会自动追加 `_01`、`_02` 等序号，不覆盖已有结果。

默认方向为 `auto`，会对每张图片自动检测方向。多个图片可以统一指定方向，也可以按图片顺序分别指定。`90` 表示顺时针旋转 90°，`-90` 表示逆时针旋转 90°，也可以写成 `270`：

```bash
# 所有图片使用90°
image2excel -o 90 image1.jpg image2.jpg image3.jpg

# image1使用0°，image2使用90°，image3自动检测
image2excel -o 0,90,auto image1.jpg image2.jpg image3.jpg
```

支持的方向值为 `auto`、`0`、`90`、`180`、`270`、`-90`。手动指定方向可以跳过该图片的四方向检测，减少处理时间。

覆盖已有文件：

```bash
image2excel image1.jpg image2.jpg --overwrite
```

指定输出路径：

```bash
image2excel image1.jpg image2.jpg --output ./students.xlsx
```

修改列数和完整页面预期行数：

```bash
image2excel \
  --columns 5 \
  --expected-rows 7 \
  image1.jpg image2.jpg
```

查看所有参数：

```bash
image2excel --help
```

## Excel 工作表

- `学生信息`：全部识别到的学生记录。
- `待复核`：姓名、学号、座位号缺失，格式异常，置信度较低或学号重复的记录。

Excel 只输出以下四列：

```text
座位号 | 学号 | 姓名 | 校验备注
```

运行过程中会显示图片、方向检测和学生区域识别进度，例如：

```text
[第1页] 方向检测 1/4（0°）
[第1页] 方向检测 2/4（90°）
[第1页] 方向：0°，检测到 35 个区域，开始识别
[第1页] 识别区域 1/35
```
