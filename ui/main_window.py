import tkinter as tk
import threading
import queue
import sys
import ctypes

from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from config import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, DEFAULT_OCR_PARAMS
from ocr_core import OCRProcessor
from file_utils import get_valid_files, save_result, ensure_dir, filter_valid_files


class MainWindow(tk.Tk):
    def __init__(self):
        if sys.platform.startswith("win"):
            try:
                # Per-Monitor V2 感知（支持多显示器不同缩放比例）
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    # 兼容旧版系统的系统级DPI感知
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass  # 非Windows或设置失败则自动跳过

        super().__init__()
        self.title("批量OCR识别系统")
        self.geometry("1000x720")
        self.minsize(800, 500)

        # 路径变量
        self.input_dir_var = tk.StringVar(value=str(DEFAULT_INPUT_DIR))
        self.output_dir_var = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))

        self.selected_files = []

        # 线程通信：日志队列
        self.log_queue = queue.Queue()
        # 运行状态
        self.is_running = False
        self.ocr_processor = None  # 延迟初始化OCR模型

        self._build_ui()
        self._poll_log()  # 启动日志轮询

    def _build_ui(self):
        """构建界面组件"""
        # 路径设置区域
        path_frame = ttk.LabelFrame(self, text="路径配置")
        path_frame.pack(fill=tk.X, padx=12, pady=10)

        # 输入目录行
        ttk.Label(path_frame, text="输入来源:").grid(row=0, column=0, padx=8, pady=10, sticky="w")
        self.input_entry = ttk.Entry(path_frame, textvariable=self.input_dir_var, width=65)
        self.input_entry.grid(row=0, column=1, padx=5, pady=10)
        ttk.Button(path_frame, text="浏览文件夹", command=self._select_input_dir).grid(row=0, column=2, padx=4, pady=10)
        ttk.Button(path_frame, text="选择文件", command=self._select_files).grid(row=0, column=3, padx=4, pady=10)


        # 输出目录行
        ttk.Label(path_frame, text="输出文件夹:").grid(row=1, column=0, padx=8, pady=10, sticky="w")
        ttk.Entry(path_frame, textvariable=self.output_dir_var, width=65).grid(row=1, column=1, padx=5, pady=10)
        ttk.Button(path_frame, text="浏览", command=self._select_output_dir).grid(row=1, column=2, padx=8, pady=10)

        # 操作按钮区
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=12, pady=2)
        self.start_btn = ttk.Button(btn_frame, text="开始识别", command=self._start_process)
        self.start_btn.pack(side="right", padx=5)

        # 日志展示区
        log_frame = ttk.LabelFrame(self, text="处理日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        self.log_text = tk.Text(log_frame, wrap="word", state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # 底部状态栏
        self.status = tk.StringVar(value="就绪")
        ttk.Label(self, textvariable=self.status, anchor="w", relief="sunken").pack(fill=tk.X, side="bottom")

    def _select_files(self):
        """手动选择单个或多个文件（按住Ctrl可多选）"""
        filetypes = [
            ("所有支持文件", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.pdf"),
            ("图片文件", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
            ("PDF文件", "*.pdf"),
            ("所有文件", "*.*")
        ]
        # 默认打开当前输入文件夹作为初始目录
        initial_dir = self.input_dir_var.get()
        if not Path(initial_dir).exists():
            initial_dir = str(Path.home())

        selected = filedialog.askopenfilenames(
            title="选择要识别的文件（按住Ctrl可多选）",
            filetypes=filetypes,
            initialdir=initial_dir
        )
        if not selected:
            return  # 用户取消选择

        # 过滤有效格式
        valid_files = filter_valid_files(selected)
        if not valid_files:
            messagebox.showwarning("提示", "选中的文件中没有支持识别的图片或PDF格式")
            return

        # 切换为文件模式：保存列表 + 输入框显示提示 + 设为只读防止误编辑
        self.selected_files = valid_files
        self.input_dir_var.set(f"已选择 {len(valid_files)} 个文件")
        self.input_entry.config(state="readonly")

    def _select_input_dir(self):
        """选择输入文件夹"""
        path = filedialog.askdirectory(title="选择输入文件夹")
        if path:
            self.selected_files = []  # 清空手动选中的文件
            self.input_entry.config(state="normal")  # 恢复输入框可编辑
            self.input_dir_var.set(path)

    def _select_output_dir(self):
        """选择输出文件夹"""
        path = filedialog.askdirectory(title="选择输出文件夹")
        if path:
            self.output_dir_var.set(path)

    def _add_log(self, msg):
        """向日志队列写入消息"""
        self.log_queue.put(msg)

    def _poll_log(self):
        """轮询日志队列，更新界面（主线程安全）"""
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self._append_log_text(msg)
        self.after(100, self._poll_log)

    def _append_log_text(self, msg):
        """向日志框追加内容"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _start_process(self):
        """启动识别任务"""
        if self.is_running:
            messagebox.showwarning("提示", "正在处理中，请等待完成")
            return

        output_dir = self.output_dir_var.get().strip()

        # 模式1：手动选择了文件
        if self.selected_files:
            # 校验文件是否都存在（防止选完后文件被删除）
            missing = [f for f in self.selected_files if not f.exists()]
            if missing:
                msg = "以下文件不存在，请检查：\n" + "\n".join([str(f) for f in missing[:3]])
                if len(missing) > 3:
                    msg += f"\n... 共 {len(missing)} 个"
                messagebox.showerror("错误", msg)
                return
            input_dir = ""  # 文件模式下无输入目录，仅占位

        # 模式2：文件夹批量模式
        else:
            input_dir = self.input_dir_var.get().strip()
            if not input_dir or not Path(input_dir).is_dir():
                messagebox.showerror("错误", "输入文件夹不存在，请重新选择或切换为选择文件模式")
                return

        # 输出目录校验（两种模式通用）
        try:
            ensure_dir(output_dir)
        except Exception as e:
            messagebox.showerror("错误", f"无法创建输出目录: {e}")
            return

        # 重置状态
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.status.set("处理中...")
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

        # 子线程执行耗时任务
        threading.Thread(
            target=self._process_task,
            args=(input_dir, output_dir),
            daemon=True
        ).start()

    def _process_task(self, input_dir, output_dir):
        """后台识别任务"""
        try:
            # 延迟初始化OCR模型，提升启动速度
            if not self.ocr_processor:
                self._add_log("正在加载OCR模型，请稍候...")
                self.ocr_processor = OCRProcessor(**DEFAULT_OCR_PARAMS)
                self._add_log("模型加载完成\n")

            # 获取待处理文件
            if self.selected_files:
                files = self.selected_files
            else:
                files = get_valid_files(input_dir)

            if not files:
                self._add_log("没有可识别的有效文件，请检查输入来源")
                return

            self._add_log(f"共找到 {len(files)} 个文件，开始处理\n")
            success = 0

            for idx, file_path in enumerate(files, 1):
                filename = file_path.name
                suffix = file_path.suffix.lower()
                self._add_log(f"[{idx}/{len(files)}] 处理文件：{filename}")

                try:
                    if suffix == ".pdf":
                        # PDF识别，带进度回调
                        def pdf_progress(cur, total):
                            self._add_log(f"  识别进度：第 {cur}/{total} 页")
                        text = self.ocr_processor.recognize_pdf(file_path, pdf_progress)
                    else:
                        # 图片识别
                        text = self.ocr_processor.recognize_image(file_path)

                    # 保存结果
                    out_file = Path(output_dir) / f"{file_path.stem}.txt"
                    save_result(text, out_file)
                    self._add_log(f"  完成，结果已保存：{out_file.name}")
                    success += 1

                except Exception as e:
                    self._add_log(f"  处理失败：{str(e)}")

            self._add_log(f"\n全部处理完成！成功 {success} 个，失败 {len(files)-success} 个")
            self.status.set("处理完成")

        except Exception as e:
            self._add_log(f"系统错误：{str(e)}")
            self.status.set("运行出错")
        finally:
            self.is_running = False
            self.start_btn.config(state="normal")
            