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

默认输出到第一张图片所在目录：

```text
image2excel_result.xlsx
```

固定列数默认为 5，行数会根据图片中的文字锚点自动检测。程序支持页面旋转、常见透视变形和只拍到页面局部的情况。

如需覆盖已有输出文件：

```bash
image2excel image1.jpg image2.jpg --overwrite
```

如需显式指定输出路径：

```bash
image2excel image1.jpg image2.jpg --output ./students.xlsx
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
