from pathlib import Path

# 程序根目录（以本文件所在目录为基准）
ROOT_DIR = Path(__file__).parent.resolve()

# 默认输入/输出文件夹
DEFAULT_INPUT_DIR = ROOT_DIR / "file"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output"

# 支持识别的图片格式
IMG_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# PaddleOCR 默认参数
DEFAULT_OCR_PARAMS = {
    "use_doc_orientation_classify": False,
    "use_doc_unwarping": False,
    "use_textline_orientation": False,
}
