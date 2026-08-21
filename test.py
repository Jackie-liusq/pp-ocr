from paddleocr import PaddleOCR
from pathlib import Path
import os
import sys
import pymupdf
import tempfile
import shutil

IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff', '.webp'}

def extract_text_from_result(ocr_result):
    lines = []
    for res in ocr_result:
        rec_texts = None
        if hasattr(res, 'rec_texts'):
            rec_texts = res.rec_texts
        elif isinstance(res, dict) and 'rec_texts' in res:
            rec_texts = res['rec_texts']
        else:
            try:
                json_data = res.json if hasattr(res, 'json') else res
                if isinstance(json_data, dict) and 'rec_texts' in json_data:
                    rec_texts = json_data['rec_texts']
            except Exception:
                pass

        if rec_texts is not None:
            if isinstance(rec_texts, list):
                lines.extend(rec_texts)
            else:
                lines.append(str(rec_texts))
        else:
            # 实在提取不到，跳过或记录
            print(f"  警告：无法从结果对象中提取文本，已跳过。")
    return '\n'.join(lines)


def ocr_image(ocr, image_path):
    """对单张图片进行 OCR，返回文本字符串"""
    result = ocr.predict(str(image_path))
    return extract_text_from_result(result)


def ocr_pdf(ocr, pdf_path):
    """对 PDF 文件进行 OCR，逐页识别并合并，返回完整文本"""
    full_text = []
    temp_dir = tempfile.mkdtemp(prefix="pdf_pages_")

    try:
        doc = pymupdf.open(pdf_path)
        total_pages = len(doc)
        print(f"  共 {total_pages} 页")

        for page_idx in range(total_pages):
            page = doc[page_idx]
            # 渲染为图片（缩放 2 倍以提高识别精度）
            mat = pymupdf.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img_path = os.path.join(temp_dir, f"page_{page_idx + 1}.png")
            pix.save(img_path)

            print(f"    正在识别第 {page_idx + 1}/{total_pages} 页...")
            page_text = ocr_image(ocr, img_path)
            full_text.append(f"--- 第 {page_idx + 1} 页 ---\n{page_text}")

        doc.close()
    except Exception as e:
        print(f"  处理 PDF 时出错：{e}")
        return ""
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return '\n\n'.join(full_text)


def main():
    # 定义输入输出文件夹路径
    script_dir = Path(__file__).parent
    input_dir = script_dir / 'file'
    output_dir = script_dir / 'output'
        
    # 检查输入文件夹是否存在
    if not input_dir.exists():
        print(f"错误：输入文件夹 '{input_dir}' 不存在，请创建并放入待处理文件。")
        sys.exit(1)

    # 创建输出文件夹
    output_dir.mkdir(exist_ok=True)

    # 初始化 PaddleOCR（使用与示例相同的参数）
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )

    # 获取输入文件夹中的所有文件
    files = [f for f in input_dir.iterdir() if f.is_file()]
    if not files:
        print(f"输入文件夹 '{input_dir}' 为空，请放入图片或 PDF 文件。")
        return

    print(f"找到 {len(files)} 个文件，开始处理...\n")

    for file_path in files:
        ext = file_path.suffix.lower()
        output_txt_path = output_dir / (file_path.stem + '.txt')

        print(f"处理文件：{file_path.name}")

        try:
            if ext in IMG_EXTENSIONS:
                # 图片直接 OCR
                text = ocr_image(ocr, file_path)
            elif ext == '.pdf':
                # PDF 逐页转换并 OCR
                text = ocr_pdf(ocr, file_path)
            else:
                print(f"  跳过不支持的文件类型：{ext}")
                continue

            # 写入文本文件
            with open(output_txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"  已保存文本：{output_txt_path}")

        except Exception as e:
            print(f"  处理文件时出错：{e}")

    print("\n所有文件处理完成！")


if __name__ == "__main__":
    main()