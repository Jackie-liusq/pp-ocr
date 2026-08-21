## 安装conda环境，教程：
https://blog.csdn.net/ming12131342/article/details/140233867

conda create -n pp-ocr python=3.11
conda activate pp-ocr

## 以下3种方式选择一种
### CPU version
python -m pip install paddlepaddle==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/

### GPU version, requires driver version >= 450.80.02 (Linux) or >= 452.39 (Windows)
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/

### GPU version, requires driver version >= 550.54.14 (Linux) or >= 550.54.14 (Windows)  本机运行的这条
python -m pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

## 安装完整功能
pip install "paddleocr[all]"

注意安装的 PaddlePaddle GPU 包是基于 cuDNN9.9 编译的，但你本机环境实际 cuDNN 版本是 9.5，版本不一致，存在潜在报错风险（本机运行时的提示）

### test为测试脚本，独立于其他脚本，自动读取file下所有文件并输出结果到output
初次运行会自动下载模型，默认pp-ocr_v6

python test.py

### 带界面
### 文件夹批量处理与单文件多文件处理
python main.py


======================================================================
## ezdxf读取cad文件.dxf后缀
pip install ezdxf
