import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel,
                             QVBoxLayout, QWidget, QAction, QMenu,QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QPoint,QPropertyAnimation,QEasingCurve
from PyQt5.QtGui import QFont, QCursor, QColor, QPalette

class FadingLabel(QLabel):
    """带淡入淡出动画的标签"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)

        # 设置字体样式
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.setFont(font)

        # 透明度效果和动画
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(500)  # 动画持续时间
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def fade_in(self):
        """淡入效果"""
        self.animation.stop()
        self.effect.setOpacity(0)
        self.setVisible(True)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    # def fade_out(self):
    #     """淡出效果"""
    #     self.animation.stop()
    #     self.effect.setOpacity(1)
    #     self.animation.setStartValue(1)
    #     self.animation.setEndValue(0)
    #     self.animation.finished.connect(lambda: self.setVisible(False))
    #     self.animation.start()

class LyricWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 设置窗口属性
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint   # 置顶
            #Qt.Tool  # 不显示在任务栏
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        #始终置顶
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # 创建歌词显示标签
        self.lyric_label = FadingLabel("")
        # 在 LyricWindow 的 init_ui 中，创建 lyric_label 后添加：
        self.lyric_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.lyric_label.setAlignment(Qt.AlignCenter)
        # self.lyric_label.setStyleSheet("""
        #     QLabel {
        #         color: white;
        #         background-color: rgba(0, 0, 0, 0%);
        #         border-radius: 10px;
        #         padding: 8px 15px;
        #         font-size: 24px;
        #         font-weight: bold;
        #     }
        # """)

        # 设置字体（确保中文正常显示）
        font = QFont("PingFang SC")  # 使用黑体
        self.lyric_label.setFont(font)

        # 设置QSS样式（白色文本，半透明黑色背景）
        self.lyric_label.setStyleSheet("""
            QLabel {
                color: #9370DB;  /* 设置文本颜色为白色 */
                background-color: rgba(0, 0, 0, 01%);  /* 半透明黑色背景 */
                border-radius: 10px;
                padding: 8px 15px;
                font-size: 36px;
                font-weight: bold;
            }
        """)

        self.setCentralWidget(self.lyric_label)
        self.resize(500, 80)
        # self.move(300, 200)  # 默认位置

    # def display_lyric(self, lyric_text):
    #     """显示传入的歌词文本"""
    #     self.lyric_label.setText("")
    #     self.lyric_label.setText(lyric_text)

    def mousePressEvent(self, event):
        """鼠标按下事件，记录拖动起始位置"""
        self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，实现窗口拖动"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)

