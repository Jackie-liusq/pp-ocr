import os
import tempfile
import shutil
import pymupdf
from paddleocr import PaddleOCR
from config import IMG_EXTENSIONS


class OCRProcessor:
    """OCR核心处理器，封装所有识别逻辑"""

    def __init__(self, **kwargs):
        """初始化PaddleOCR实例，支持传入自定义参数覆盖默认配置"""
        self.ocr = PaddleOCR(**kwargs)

    @staticmethod
    def _extract_text(ocr_result):
        """从OCR返回结果中提取纯文本，兼容多种返回格式"""
        lines = []
        for res in ocr_result:
            rec_texts = None
            # 兼容对象属性格式
            if hasattr(res, "rec_texts"):
                rec_texts = res.rec_texts
            # 兼容字典格式
            elif isinstance(res, dict) and "rec_texts" in res:
                rec_texts = res["rec_texts"]
            # 兼容带json属性的对象
            else:
                try:
                    json_data = res.json if hasattr(res, "json") else res
                    if isinstance(json_data, dict) and "rec_texts" in json_data:
                        rec_texts = json_data["rec_texts"]
                except Exception:
                    pass

            if rec_texts is not None:
                if isinstance(rec_texts, list):
                    lines.extend(rec_texts)
                else:
                    lines.append(str(rec_texts))
            else:
                lines.append("[警告：该行文本提取失败]")
        return "\n".join(lines)

    def recognize_image(self, image_path):
        """识别单张图片，返回文本内容"""
        result = self.ocr.predict(str(image_path))
        return self._extract_text(result)

    def recognize_pdf(self, pdf_path, progress_cb=None):
        """
        逐页识别PDF文件
        :param pdf_path: PDF文件路径
        :param progress_cb: 进度回调函数，接收 (当前页, 总页数)
        :return: 完整识别文本
        """
        full_text = []
        temp_dir = tempfile.mkdtemp(prefix="pdf_pages_")

        try:
            doc = pymupdf.open(pdf_path)
            total_pages = len(doc)

            for page_idx in range(total_pages):
                page = doc[page_idx]
                # 2倍缩放渲染，提升识别精度
                mat = pymupdf.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                img_path = os.path.join(temp_dir, f"page_{page_idx + 1}.png")
                pix.save(img_path)

                # 触发进度回调
                if progress_cb:
                    progress_cb(page_idx + 1, total_pages)

                page_text = self.recognize_image(img_path)
                full_text.append(f"--- 第 {page_idx + 1} 页 ---\n{page_text}")

            doc.close()
        except Exception as e:
            raise RuntimeError(f"PDF处理失败: {str(e)}")
        finally:
            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)

        return "\n\n".join(full_text)
    