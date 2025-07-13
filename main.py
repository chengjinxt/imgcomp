import sys
import os
import subprocess
import requests
import webbrowser
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QFileDialog, 
                               QSlider, QSpinBox, QCheckBox, QTextEdit, 
                               QProgressBar, QGroupBox, QGridLayout, QMessageBox,
                               QLineEdit, QComboBox, QSplitter, QDialog, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QPixmap, QFont, QIcon, QPalette, QColor, QCursor
import json

class AdDataThread(QThread):
    """广告数据获取线程"""
    data_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def run(self):
        try:
            url = "http://www.firemail.wang:8880/api/admin/api/record/fetch"
            headers = {"Content-Type": "application/json"}
            data = {
                "classId": 1274,
                "syncTime": 1519297787000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0 and "data" in result:
                data_list = result["data"].get("dataList", [])
                self.data_loaded.emit(data_list)
            else:
                self.error_occurred.emit(f"API返回错误: {result.get('msg', '未知错误')}")
                
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"网络请求失败: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"获取广告数据失败: {str(e)}")

class ImageViewerDialog(QDialog):
    """图片查看器对话框"""
    def __init__(self, image_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("图片查看")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 图片显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background: white;")
        layout.addWidget(self.image_label)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        # 加载图片
        self.load_image(image_url)
    
    def load_image(self, image_url):
        """加载图片"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            
            if not pixmap.isNull():
                # 缩放图片以适应窗口
                scaled_pixmap = pixmap.scaled(
                    self.size(), 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
            else:
                self.image_label.setText("无法加载图片")
                
        except Exception as e:
            self.image_label.setText(f"加载图片失败: {str(e)}")

class ImageCompressorThread(QThread):
    """图片压缩线程"""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, input_file, output_file, quality, webp=False, 
                 target_size=None, size_range=None, webp_quality=100):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.quality = quality
        self.webp = webp
        self.target_size = target_size
        self.size_range = size_range
        self.webp_quality = webp_quality
    
    def run(self):
        try:
            cmd = [get_imagecomp_path(), self.input_file, "-o", self.output_file]
            cmd.append("--force")
            if self.quality is not None:
                cmd.extend(["-q", str(self.quality)])
            
            if self.webp:
                cmd.append("--webp")
                if self.webp_quality != 100:
                    cmd.extend(["--webp-quality", str(self.webp_quality)])
            
            if self.target_size is not None:
                cmd.extend(["-t", str(self.target_size)])
            
            if self.size_range is not None:
                cmd.extend(["-s", str(self.size_range[0]), str(self.size_range[1])])
            
            self.progress.emit(f"执行命令: {' '.join(cmd)}")
            
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                creationflags=creationflags
            )
            
            if result.returncode == 0:
                self.finished.emit(True, "压缩完成！")
            else:
                self.finished.emit(False, f"压缩失败: {result.stderr}")
                
        except Exception as e:
            self.finished.emit(False, f"执行错误: {str(e)}")

class ImageCompressorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_file = ""
        self.output_file = ""
        self.original_pixmap = None
        self.compressed_pixmap = None

        # 走马灯广告相关属性初始化
        self.ad_marquee_text = "【1/1】测试广告内容"
        self.ad_marquee_index = 0
        self.ad_marquee_timer = QTimer()
        self.ad_marquee_timer.timeout.connect(self.update_ad_marquee)
        self.ad_marquee_timer.start(80)  # 滚动速度，越小越快

        self.ad_data = []  # 广告数据
        self.current_ad_index = 0  # 当前广告索引

        self.init_ui()
        self.load_settings()
        self.load_ad_data()
        
    def init_ui(self):
        # 设置窗口图标
        def resource_path(relative_path):
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller打包后
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        
        ico_path = resource_path("imgcomp.ico")
        self.setWindowIcon(QIcon(ico_path))
        self.setWindowTitle("图片压缩工具")
        self.setMinimumSize(1100, 700)
        
        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #ffffff;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #5c6bc0;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QSpinBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
                min-height: 20px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #4CAF50;
                border: none;
                border-radius: 2px;
                width: 16px;
                height: 12px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #45a049;
            }
            QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
                background-color: #3d8b40;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid white;
                margin-top: 2px;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid white;
                margin-bottom: 2px;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
                min-height: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #4CAF50;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #cccccc;
                background-color: white;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #4CAF50;
            }
            QLabel {
                color: #333333;
            }
            QLabel[class="info"] {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #f9f9f9;
                color: #666666;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 广告走马灯区域
        self.create_ad_banner(main_layout)
        
        # 主要内容区域
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        content_layout.addWidget(splitter)
        
        # 左侧控制面板
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # 右侧图片显示面板
        right_panel = self.create_image_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
    def create_control_panel(self):
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件选择组
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 输入文件选择
        input_layout = QHBoxLayout()
        self.input_label = QLabel("未选择文件")
        self.input_label.setProperty("class", "info")
        input_layout.addWidget(self.input_label)
        
        self.select_input_btn = QPushButton("选择图片")
        self.select_input_btn.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.select_input_btn)
        file_layout.addLayout(input_layout)
        
        # 输出文件选择
        output_layout = QHBoxLayout()
        self.output_label = QLabel("未选择输出位置")
        self.output_label.setProperty("class", "info")
        output_layout.addWidget(self.output_label)
        
        self.select_output_btn = QPushButton("选择输出")
        self.select_output_btn.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.select_output_btn)
        
        # 新增：打开输出目录按钮
        self.open_output_dir_btn = QPushButton("打开输出目录")
        self.open_output_dir_btn.clicked.connect(self.open_output_dir)
        output_layout.addWidget(self.open_output_dir_btn)

        file_layout.addLayout(output_layout)
        
        layout.addWidget(file_group)
        
        # 压缩设置组
        settings_group = QGroupBox("压缩设置")
        settings_layout = QGridLayout(settings_group)
        
        # 质量设置
        settings_layout.addWidget(QLabel("压缩质量:"), 0, 0)
        slider_layout = QHBoxLayout()
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(80)
        self.quality_slider.setFixedWidth(140)
        self.quality_slider.valueChanged.connect(self.update_quality_spinbox)
        slider_layout.addWidget(self.quality_slider)
        self.quality_value_label = QLabel(str(self.quality_slider.value()))
        self.quality_value_label.setFixedWidth(30)
        self.quality_value_label.setAlignment(Qt.AlignCenter)
        slider_layout.addWidget(self.quality_value_label)
        self.quality_slider.valueChanged.connect(lambda v: self.quality_value_label.setText(str(v)))
        settings_layout.addLayout(slider_layout, 0, 1)
        
        self.quality_spinbox = QSpinBox()
        self.quality_spinbox.setRange(1, 100)
        self.quality_spinbox.setValue(80)
        self.quality_spinbox.valueChanged.connect(self.update_quality_slider)
        settings_layout.addWidget(self.quality_spinbox, 0, 2)
        
        # WebP转换
        self.webp_checkbox = QCheckBox("转换为WebP格式")
        settings_layout.addWidget(self.webp_checkbox, 1, 0, 1, 2)
        
        # WebP质量
        settings_layout.addWidget(QLabel("WebP质量:"), 2, 0)
        self.webp_quality_spinbox = QSpinBox()
        self.webp_quality_spinbox.setRange(1, 100)
        self.webp_quality_spinbox.setValue(100)
        settings_layout.addWidget(self.webp_quality_spinbox, 2, 1)
        
        # 目标文件大小
        settings_layout.addWidget(QLabel("目标大小(KB):"), 3, 0)
        self.target_size_spinbox = QSpinBox()
        self.target_size_spinbox.setRange(1, 10000)
        self.target_size_spinbox.setValue(100)
        self.target_size_spinbox.setSpecialValueText("不限制")
        settings_layout.addWidget(self.target_size_spinbox, 3, 1)
        
        # 大小范围
        settings_layout.addWidget(QLabel("大小范围(KB):"), 4, 0)
        range_layout = QHBoxLayout()
        self.min_size_spinbox = QSpinBox()
        self.min_size_spinbox.setRange(1, 10000)
        self.min_size_spinbox.setValue(50)
        range_layout.addWidget(self.min_size_spinbox)
        range_layout.addWidget(QLabel("-"))
        self.max_size_spinbox = QSpinBox()
        self.max_size_spinbox.setRange(1, 10000)
        self.max_size_spinbox.setValue(200)
        range_layout.addWidget(self.max_size_spinbox)
        settings_layout.addLayout(range_layout, 4, 1)
        
        # 压缩模式选择
        settings_layout.addWidget(QLabel("压缩模式:"), 5, 0)
        self.compression_mode = QComboBox()
        self.compression_mode.addItems(["质量优先", "目标大小", "大小范围"])
        self.compression_mode.currentTextChanged.connect(self.on_compression_mode_changed)
        settings_layout.addWidget(self.compression_mode, 5, 1)
        
        layout.addWidget(settings_group)
        
        # 操作按钮组
        button_group = QGroupBox("操作")
        button_layout = QVBoxLayout(button_group)
        
        self.compress_btn = QPushButton("开始压缩")
        self.compress_btn.clicked.connect(self.start_compression)
        self.compress_btn.setEnabled(False)
        button_layout.addWidget(self.compress_btn)
        
        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_settings_btn)
        
        layout.addWidget(button_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 日志显示
        log_group = QGroupBox("执行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
        
        layout.addStretch()
        return panel
    
    def create_ad_banner(self, parent_layout):
        ad_container = QFrame()
        ad_container.setFixedHeight(60)  # 增大广告栏高度
        ad_container.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #388E3C, stop:1 #2E7D32);
                border-radius: 8px;
                border: 2px solid #1B5E20;
                margin: 6px 8px 6px 8px;
            }
        """)
        ad_layout = QHBoxLayout(ad_container)
        ad_layout.setContentsMargins(16, 4, 16, 4)
        ad_layout.setSpacing(4) # Changed from 8 to 4

        # 广告图标
        ad_icon = QLabel("📢")
        ad_icon.setStyleSheet("color: #FFF; font-size: 20px; font-weight: bold;")
        ad_icon.setMinimumWidth(36)   # 增加宽度
        ad_icon.setMinimumHeight(32)  # 增加高度
        ad_icon.setAlignment(Qt.AlignCenter)
        ad_layout.addWidget(ad_icon)

        # 广告文本标签
        self.ad_label = QLabel("【测试广告】欢迎使用图片压缩工具！")
        self.ad_label.setStyleSheet("""
            QLabel {
                color: #F00;
                font-size: 18px;  /* 或 20px */
                font-weight: bold;
                background: yellow;
                padding: 4px 12px;
            }
        """)
        self.ad_label.setMinimumWidth(500)
        self.ad_label.setMinimumHeight(40)
        self.ad_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.ad_label.installEventFilter(self)  # 用于鼠标悬停暂停
        self.ad_label.mousePressEvent = self.on_ad_clicked
        self.ad_label.setCursor(QCursor(Qt.PointingHandCursor))
        ad_layout.addWidget(self.ad_label, 1)

        # 左右切换按钮
        prev_btn = QPushButton("◀")
        btn_size = 36
        prev_btn.setFixedSize(btn_size, btn_size)
        prev_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #FFF;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #FFD600;
            }
        """)
        prev_btn.clicked.connect(self.show_previous_ad)
        ad_layout.addWidget(prev_btn)

        next_btn = QPushButton("▶")
        next_btn.setFixedSize(btn_size, btn_size)
        next_btn.setStyleSheet(prev_btn.styleSheet())
        next_btn.clicked.connect(self.show_next_ad)
        ad_layout.addWidget(next_btn)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(btn_size, btn_size)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #FFF;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                color: #F44336;
            }
        """)
        close_btn.clicked.connect(lambda: ad_container.setVisible(False))
        ad_layout.addWidget(close_btn)

        parent_layout.addWidget(ad_container)

        # 定时器
        self.ad_timer = QTimer()
        self.ad_timer.timeout.connect(self.show_next_ad)
        self.ad_timer.start(5000)
    
    def create_image_panel(self):
        """创建右侧图片显示面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 图片信息组
        info_group = QGroupBox("图片信息")
        info_layout = QGridLayout(info_group)
        
        self.info_labels = {}
        info_fields = ["文件名", "文件大小", "图片尺寸", "文件格式", "压缩后大小"]
        
        for i, field in enumerate(info_fields):
            info_layout.addWidget(QLabel(f"{field}:"), i, 0)
            label = QLabel("未加载")
            label.setProperty("class", "info")
            self.info_labels[field] = label
            info_layout.addWidget(label, i, 1)
        
        layout.addWidget(info_group)
        
        # 图片显示组
        image_group = QGroupBox("图片预览")
        image_layout = QVBoxLayout(image_group)
        
        # 原始图片
        original_layout = QHBoxLayout()
        original_layout.addWidget(QLabel("原始图片:"))
        self.original_size_label = QLabel("")
        original_layout.addWidget(self.original_size_label)
        original_layout.addStretch()
        image_layout.addLayout(original_layout)
        
        self.original_image_label = QLabel()
        self.original_image_label.setMinimumSize(200, 150)
        self.original_image_label.setStyleSheet("border: 2px solid #ddd; background: white; border-radius: 4px;")
        self.original_image_label.setAlignment(Qt.AlignCenter)
        self.original_image_label.setText("请选择图片")
        image_layout.addWidget(self.original_image_label)
        
        # 压缩后图片
        compressed_layout = QHBoxLayout()
        compressed_layout.addWidget(QLabel("压缩后图片:"))
        self.compressed_size_label = QLabel("")
        compressed_layout.addWidget(self.compressed_size_label)
        compressed_layout.addStretch()
        image_layout.addLayout(compressed_layout)
        
        self.compressed_image_label = QLabel()
        self.compressed_image_label.setMinimumSize(200, 150)
        self.compressed_image_label.setStyleSheet("border: 2px solid #ddd; background: white; border-radius: 4px;")
        self.compressed_image_label.setAlignment(Qt.AlignCenter)
        self.compressed_image_label.setText("压缩后显示")
        image_layout.addWidget(self.compressed_image_label)
        
        layout.addWidget(image_group)
        return panel
    
    def update_quality_spinbox(self, value):
        """更新质量数值框"""
        self.quality_spinbox.setValue(value)
    
    def update_quality_slider(self, value):
        """更新质量滑块"""
        self.quality_slider.setValue(value)
    
    def on_compression_mode_changed(self, mode):
        """压缩模式改变时的处理"""
        if mode == "质量优先":
            self.quality_slider.setEnabled(True)
            self.quality_spinbox.setEnabled(True)
            self.target_size_spinbox.setEnabled(False)
            self.min_size_spinbox.setEnabled(False)
            self.max_size_spinbox.setEnabled(False)
        elif mode == "目标大小":
            self.quality_slider.setEnabled(False)
            self.quality_spinbox.setEnabled(False)
            self.target_size_spinbox.setEnabled(True)
            self.min_size_spinbox.setEnabled(False)
            self.max_size_spinbox.setEnabled(False)
        elif mode == "大小范围":
            self.quality_slider.setEnabled(False)
            self.quality_spinbox.setEnabled(False)
            self.target_size_spinbox.setEnabled(False)
            self.min_size_spinbox.setEnabled(True)
            self.max_size_spinbox.setEnabled(True)
    
    def select_input_file(self):
        """选择输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", "", 
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp);;所有文件 (*)"
        )
        if file_path:
            self.input_file = file_path
            self.input_label.setText(os.path.basename(file_path))
            self.load_image_info(file_path)
            self.update_compress_button()
    
    def select_output_file(self):
        """选择输出文件"""
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请先选择输入文件")
            return
            
        input_path = Path(self.input_file)
        default_name = input_path.stem + "_compressed"
        if self.webp_checkbox.isChecked():
            default_name += ".webp"
        else:
            default_name += input_path.suffix
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存压缩图片", str(input_path.parent / default_name),
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp);;所有文件 (*)"
        )
        if file_path:
            self.output_file = file_path
            self.output_label.setText(os.path.basename(file_path))
            self.update_compress_button()
    
    def open_output_dir(self):
        """打开压缩后图片所在目录"""
        if not self.output_file:
            QMessageBox.information(self, "提示", "请先选择输出文件")
            return
        output_path = Path(self.output_file)
        folder = str(output_path.parent)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录: {str(e)}")
    
    def load_image_info(self, file_path):
        """加载图片信息"""
        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                raise Exception("无法加载图片")
            
            self.original_pixmap = pixmap
            self.display_image(self.original_image_label, pixmap)
            
            # 更新图片信息
            file_size = os.path.getsize(file_path) / 1024  # KB
            self.info_labels["文件名"].setText(os.path.basename(file_path))
            self.info_labels["文件大小"].setText(f"{file_size:.1f} KB")
            self.info_labels["图片尺寸"].setText(f"{pixmap.width()} x {pixmap.height()}")
            self.info_labels["文件格式"].setText(Path(file_path).suffix.upper())
            self.original_size_label.setText(f"大小: {file_size:.1f} KB")
            
            # 自动设置输出文件
            if not self.output_file:
                input_path = Path(file_path)
                default_name = input_path.stem + "_compressed"
                if self.webp_checkbox.isChecked():
                    default_name += ".webp"
                else:
                    default_name += input_path.suffix
                self.output_file = str(input_path.parent / default_name)
                self.output_label.setText(os.path.basename(self.output_file))
                self.update_compress_button()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载图片失败: {str(e)}")
    
    def display_image(self, label, pixmap):
        """在标签中显示图片"""
        if pixmap.isNull():
            return
            
        # 计算缩放比例
        label_size = label.size()
        pixmap_size = pixmap.size()
        
        scaled_pixmap = pixmap.scaled(
            label_size, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        label.setPixmap(scaled_pixmap)
    
    def update_compress_button(self):
        """更新压缩按钮状态"""
        self.compress_btn.setEnabled(bool(self.input_file and self.output_file))
    
    def start_compression(self):
        """开始压缩"""
        if not self.input_file or not self.output_file:
            QMessageBox.warning(self, "警告", "请选择输入和输出文件")
            return
        
        # 获取压缩参数
        mode = self.compression_mode.currentText()
        quality = None
        target_size = None
        size_range = None
        
        if mode == "质量优先":
            quality = self.quality_spinbox.value()
        elif mode == "目标大小":
            target_size = self.target_size_spinbox.value()
        elif mode == "大小范围":
            size_range = (self.min_size_spinbox.value(), self.max_size_spinbox.value())
        
        # 创建压缩线程
        self.compressor_thread = ImageCompressorThread(
            self.input_file,
            self.output_file,
            quality,
            self.webp_checkbox.isChecked(),
            target_size,
            size_range,
            self.webp_quality_spinbox.value()
        )
        
        self.compressor_thread.progress.connect(self.update_log)
        self.compressor_thread.finished.connect(self.compression_finished)
        
        # 更新UI状态
        self.compress_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.log_text.clear()
        
        # 开始压缩
        self.compressor_thread.start()
    
    def update_log(self, message):
        """更新日志"""
        self.log_text.append(message)
        self.log_text.ensureCursorVisible()
    
    def compression_finished(self, success, message):
        """压缩完成"""
        self.compress_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.update_log(message)
        
        if success:
            # 加载压缩后的图片
            try:
                compressed_pixmap = QPixmap(self.output_file)
                if not compressed_pixmap.isNull():
                    self.compressed_pixmap = compressed_pixmap
                    self.display_image(self.compressed_image_label, compressed_pixmap)
                    
                    # 更新压缩后信息
                    compressed_size = os.path.getsize(self.output_file) / 1024
                    self.info_labels["压缩后大小"].setText(f"{compressed_size:.1f} KB")
                    self.compressed_size_label.setText(f"大小: {compressed_size:.1f} KB")
                    
                    # 计算压缩率
                    original_size = os.path.getsize(self.input_file) / 1024
                    compression_ratio = (1 - compressed_size / original_size) * 100
                    self.update_log(f"压缩率: {compression_ratio:.1f}%")
                    
            except Exception as e:
                self.update_log(f"加载压缩后图片失败: {str(e)}")
        
        QMessageBox.information(self, "完成", message)
    
    def save_settings(self):
        """保存设置"""
        settings = {
            "quality": self.quality_spinbox.value(),
            "webp": self.webp_checkbox.isChecked(),
            "webp_quality": self.webp_quality_spinbox.value(),
            "target_size": self.target_size_spinbox.value(),
            "min_size": self.min_size_spinbox.value(),
            "max_size": self.max_size_spinbox.value(),
            "compression_mode": self.compression_mode.currentText()
        }
        
        try:
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "设置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                
                self.quality_spinbox.setValue(settings.get("quality", 80))
                self.webp_checkbox.setChecked(settings.get("webp", False))
                self.webp_quality_spinbox.setValue(settings.get("webp_quality", 100))
                self.target_size_spinbox.setValue(settings.get("target_size", 100))
                self.min_size_spinbox.setValue(settings.get("min_size", 50))
                self.max_size_spinbox.setValue(settings.get("max_size", 200))
                
                mode = settings.get("compression_mode", "质量优先")
                index = self.compression_mode.findText(mode)
                if index >= 0:
                    self.compression_mode.setCurrentIndex(index)
                    
        except Exception as e:
            print(f"加载设置失败: {str(e)}")
    
    def load_ad_data(self):
        """加载广告数据"""
        self.ad_thread = AdDataThread()
        self.ad_thread.data_loaded.connect(self.on_ad_data_loaded)
        self.ad_thread.error_occurred.connect(self.on_ad_error)
        self.ad_thread.start()
    
    def on_ad_data_loaded(self, data_list):
        """广告数据加载完成"""
        self.ad_data = data_list
        if self.ad_data:
            self.current_ad_index = 0
            self.update_ad_display()
        else:
            self.ad_label.setText("📢 暂无广告信息")
    
    def on_ad_error(self, error_msg):
        """广告数据加载错误"""
        self.ad_label.setText(f"📢 广告加载失败: {error_msg}")
    
    def update_ad_display(self):
        """更新广告显示"""
        if not self.ad_data:
            return
        
        if 0 <= self.current_ad_index < len(self.ad_data):
            ad_item = self.ad_data[self.current_ad_index]
            title = ad_item.get("title", "未知广告")
            # 添加序号和特殊格式
            total_ads = len(self.ad_data)
            current_num = self.current_ad_index + 1
            self.ad_marquee_text = f"【{current_num}/{total_ads}】{title}"
            self.ad_marquee_index = 0
        else:
            self.ad_marquee_text = ""
            self.ad_marquee_index = 0
    
    def update_ad_marquee(self):
        if not self.ad_marquee_text:
            return
        # 让内容循环滚动
        text = self.ad_marquee_text
        idx = self.ad_marquee_index
        show_len = 30  # 可视字符数
        if len(text) <= show_len:
            self.ad_label.setText(text)
        else:
            display = text[idx:idx+show_len]
            if len(display) < show_len:
                display += "   " + text[:show_len - len(display)]
            self.ad_label.setText(display)
            self.ad_marquee_index = (idx + 1) % len(text)
    
    def show_next_ad(self):
        """显示下一个广告"""
        if not self.ad_data:
            return
        
        self.current_ad_index = (self.current_ad_index + 1) % len(self.ad_data)
        self.update_ad_display()
    
    def show_previous_ad(self):
        """显示上一个广告"""
        if not self.ad_data:
            return
        
        self.current_ad_index = (self.current_ad_index - 1) % len(self.ad_data)
        self.update_ad_display()
    
    def on_ad_clicked(self, event):
        """广告点击事件"""
        if not self.ad_data or not (0 <= self.current_ad_index < len(self.ad_data)):
            return
        
        ad_item = self.ad_data[self.current_ad_index]
        relative_path = ad_item.get("relativePath", "")
        
        if not relative_path:
            return
        
        # 检查是否是图片链接
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        is_image = any(relative_path.lower().endswith(ext) for ext in image_extensions)
        
        if is_image:
            # 在客户端内打开图片
            dialog = ImageViewerDialog(relative_path, self)
            dialog.exec()
        else:
            # 调用系统默认浏览器打开链接
            try:
                webbrowser.open(relative_path)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开链接: {str(e)}")

    def eventFilter(self, obj, event):
        if obj == self.ad_label:
            if event.type() == QEvent.Enter:
                self.ad_marquee_timer.stop()
            elif event.type() == QEvent.Leave:
                self.ad_marquee_timer.start(80)
        return super().eventFilter(obj, event)

def get_imagecomp_path():
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
    else:
        # 源码运行
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "imagecomp.exe")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("图片压缩工具")
    app.setApplicationVersion("1.0")
    
    window = ImageCompressorApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 