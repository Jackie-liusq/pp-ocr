from pathlib import Path
from config import IMG_EXTENSIONS


def get_valid_files(input_dir):
    """获取目录下所有支持识别的文件（图片+PDF）"""
    input_path = Path(input_dir)
    if not input_path.exists() or not input_path.is_dir():
        raise FileNotFoundError(f"输入目录不存在: {input_dir}")

    valid_files = []
    for file in input_path.iterdir():
        if not file.is_file():
            continue
        suffix = file.suffix.lower()
        if suffix in IMG_EXTENSIONS or suffix == ".pdf":
            valid_files.append(file)
    return valid_files


def save_result(text, output_path, encoding="utf-8"):
    """将识别结果保存为txt文件"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding=encoding) as f:
        f.write(text)


def ensure_dir(dir_path):
    """确保目录存在，不存在则自动创建"""
    Path(dir_path).mkdir(parents=True, exist_ok=True)


def filter_valid_files(file_paths):
    """从手动选中的文件路径列表中，过滤出支持识别的有效文件"""
    valid_files = []
    for path in file_paths:
        p = Path(path)
        suffix = p.suffix.lower()
        if p.is_file() and (suffix in IMG_EXTENSIONS or suffix == ".pdf"):
            valid_files.append(p)
    return valid_files
    