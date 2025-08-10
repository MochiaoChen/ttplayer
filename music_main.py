import sys, os
import time

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QGraphicsOpacityEffect, QShortcut, QSlider
from PyQt5 import uic
from PyQt5.QtCore import Qt,pyqtSignal,QEvent,pyqtSlot,QPropertyAnimation,QRect, QEasingCurve,QUrl
from PyQt5.QtGui import QIcon, QFont ,QPixmap, QPalette, QBrush, QPainter, QPainterPath, QKeySequence, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import playlist


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
        self.animation.setDuration(800)  # 动画持续时间
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def fade_in(self):
        """淡入效果"""
        self.animation.stop()
        self.effect.setOpacity(0)
        self.setVisible(True)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()

    def fade_out(self):
        """淡出效果"""
        self.animation.stop()
        self.effect.setOpacity(1)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(lambda: self.setVisible(False))
        self.animation.start()

# 自定义滑块类
class ImageSlider(QSlider):
    def __init__(self, pixmap, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 100)  # 设置范围
        self.current_volume = 60
        self.setValue(0)
        self.handle_pixmap = pixmap  # 保存你的图片对象

    def paintEvent(self, event):
        # 不调用父类的 paintEvent，避免画出默认滑块
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)


        # 计算滑块位置
        # 注意：QSlider 的 groove（轨道）宽度是控件宽度减去滑块宽度
        available_width = self.width() - self.handle_pixmap.width()
        min_val, max_val = self.minimum(), self.maximum()
        current_val = self.value()

        # 将当前值映射到 x 坐标
        handle_x = int(available_width * (current_val - min_val) / (max_val - min_val))
        handle_y = (self.height() - self.handle_pixmap.height()) // 2  # 垂直居中


        # 绘制图片作为滑块
        painter.drawPixmap(handle_x, handle_y, self.handle_pixmap)

from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer

class ImageToggleButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFixedSize(100, 50)
        #
        # # 假设你已经有这些 QPixmap 对象
        # self.pixmap_normal = QPixmap("normal.jpg")    # 可以是任何来源
        # self.pixmap_hover = QPixmap("hover.jpg")
        # self.pixmap_pressed = QPixmap("pressed.jpg")
        #
        # # 缩放到按钮大小（可选）
        # size = self.size()
        # self.pixmap_normal = self.pixmap_normal.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        # self.pixmap_hover = self.pixmap_hover.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        # self.pixmap_pressed = self.pixmap_pressed.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        #
        # # 初始设置图标
        # self.setIcon(QIcon(self.pixmap_normal))
        # self.setIconSize(self.size())

    def enterEvent(self, event):
        self.setIcon(QIcon(self.pixmap_hover))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(QIcon(self.pixmap_normal))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setIcon(QIcon(self.pixmap_pressed))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.underMouse():  # 鼠标仍在按钮上
            self.setIcon(QIcon(self.pixmap_hover))
        else:
            self.setIcon(QIcon(self.pixmap_normal))
        super().mouseReleaseEvent(event)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = None
        # 启用拖放支持
        self.setAcceptDrops(True)

        # 播放器核心组件
        self.player = QMediaPlayer()
        self.playlist = []
        self.current_index = 0
        self.shuffle_mode = False
        self.current_playing_path = None
        self.init_ui()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.globalPos() - self.window().pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.window().move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False


    def init_ui(self):
        self.ui = uic.loadUi("./Designer_ui/player.ui",self)
        # 去掉标题栏
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.move(800,400)
        # 启动时渐显动画
        self.start_animation(0, 1)

        # 加载主窗口背景图
        self.background_path = "./skin/Purple/player_skin.bmp"
        pixmap = QPixmap(self.background_path)
        # 假设你已有 pixmap
        # 定义圆角函数（只需写一次）
        def round_pixmap(pixmap, radius):
            rounded = QPixmap(pixmap.size())
            rounded.fill(Qt.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            # 直接传 x, y, w, h
            path = QPainterPath()
            rect = pixmap.rect()
            path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), radius, radius)
            painter.setClipPath(path)

            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            return rounded
        pixmap = round_pixmap(pixmap, 8)  # 一行完成裁切并赋值

        # 设置窗口大小为图片大小
        self.setFixedSize(pixmap.width(), pixmap.height())

        # 或者保持原图大小，居中/左上对齐显示
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(pixmap))  # 原图大小
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 设置窗口为无边框
        self.setWindowFlags(Qt.FramelessWindowHint)

        # 按钮组渲染
        btn = {
            self.music_list: './skin/Purple/playlist.bmp',
            self.preview: './skin/Purple/prev.bmp',
            self.btn_play: './skin/Purple/play.bmp',
            self.next: './skin/Purple/next.BMP',
            self.fixed: './skin/Purple/ontop.bmp',
            self.mini_top: './skin/Purple/minimode.bmp',
            self.min: './skin/Purple/minimize.bmp',
            self.close: './skin/Purple/close.bmp',
            self.lrc: './skin/Purple/lyric.bmp',
        }
        for key in btn:
            self.temp = self.crop_image_into_four_horizontal(btn[key])
            # 将 QPixmap 设置给 QPushButton
            icon = QIcon()
            round = 5
            # icon = QIcon(round_pixmap(self.temp[0][0],3))
            icon_normal = round_pixmap(self.temp[0][0], round)
            icon_hover = round_pixmap(self.temp[0][1], round)
            icon_pressed = round_pixmap(self.temp[0][2], round)



            def setup_hover_pressed_icon( button, normal_pixmap, hover_pixmap, pressed_pixmap):
                """为任意 QPushButton 添加 hover/pressed 图标切换功能"""
                # 创建图标
                button._icons = {
                    'normal': QIcon(normal_pixmap),
                    'hover': QIcon(hover_pixmap),
                    'pressed': QIcon(pressed_pixmap)
                }

                # 初始图标
                button.setIcon(button._icons['normal'])
                button.setIconSize(button.size())
                button.setStyleSheet("border: none; background: transparent;")

                # 定义事件处理函数
                def enter_event(event):
                    button.setIcon(button._icons['hover'])
                    # 调用父类事件（保留原有行为）
                    button.__class__.enterEvent(button, event)

                def leave_event(event):
                    button.setIcon(button._icons['normal'])
                    button.__class__.leaveEvent(button, event)

                def mouse_press_event(event):
                    if event.button() == Qt.LeftButton:
                        button.setIcon(button._icons['pressed'])
                    button.__class__.mousePressEvent(button, event)

                def mouse_release_event(event):
                    if button.underMouse():
                        button.setIcon(button._icons['hover'])
                    else:
                        button.setIcon(button._icons['normal'])
                    button.__class__.mouseReleaseEvent(button, event)

                # 动态绑定事件（猴子补丁）
                key.enterEvent = enter_event
                key.leaveEvent = leave_event
                key.mousePressEvent = mouse_press_event
                key.mouseReleaseEvent = mouse_release_event

            # 给按钮“打补丁”：绑定事件
            setup_hover_pressed_icon(key, icon_normal, icon_hover, icon_pressed)
            icon.addPixmap(icon_normal, QIcon.Normal, QIcon.Off)
            # icon.addPixmap(icon_hover, QIcon.Active, QIcon.Off)  # hover
            # icon.addPixmap(icon_pressed, QIcon.Selected, QIcon.On)  # pressed

            # icon = round_pixmap(icon,3)
            key.setIcon(icon)
            # 设置图标大小为按钮大小
            key.setIconSize(key.size())
            key.setStyleSheet("""
                QPushButton {
                    border: none;
                    padding: 0px;
                    margin: 0px;
                    background: transparent;
                }
            """)

        # 创建自定义播放进度滑块
        pixmap = self.crop_image_into_four_horizontal('./skin/Purple/progress_thumb.bmp')
        pixmap = round_pixmap(pixmap[0][0], round)
        self.progress_slider = ImageSlider(pixmap)
        self.progress_slider.move(10, 112)
        # self.slider.setMaximumSize(400, 30)  # 宽度最多为400像素
        self.progress_slider.setFixedWidth(290)  # 设置滑块的宽度为300像素

        # 将标签添加到窗口（注意：不是 layout，而是直接 setParent）
        self.progress_slider.setParent(self)  # self 是你的主窗口（QWidget）

        # 创建自定义音量滑块
        pixmap = self.crop_image_into_four_horizontal('./skin/Purple/progress_thumb.bmp')
        pixmap = round_pixmap(pixmap[0][0], round)
        # 获取原始宽度和高度
        original_width = pixmap.width()
        original_height = pixmap.height()

        # 计算放大后的宽度和高度
        scaled_width = int(original_width * 1.1)
        scaled_height = int(original_height * 1.1)

        # 使用scaled方法生成放大后的QPixmap对象
        # 保持原始的AspectRatio
        pixmap = pixmap.scaled(scaled_width, scaled_height, Qt.KeepAspectRatio)
        self.volume_slider = ImageSlider(pixmap)
        self.volume_slider.move(205, 71)
        # self.slider.setMaximumSize(400, 30)  # 宽度最多为400像素
        self.volume_slider.setFixedWidth(92)  # 设置滑块的宽度为300像素
        #设置初始位置为音量大小
        self.volume_slider.setValue(self.volume_slider.current_volume)

        # 将标签添加到窗口（注意：不是 layout，而是直接 setParent）
        self.volume_slider.setParent(self)  # self 是你的主窗口（QWidget）

        # 正在播放的歌词（大字体显示）
        self.current_lyric_label = FadingLabel("")
        # 浮动字幕设置为紫色
        self.current_lyric_label.setStyleSheet(
            "color: #9370DB; font-size: 16px; font-weight: normal;font-family: PingFang SC;")
        self.current_lyric_label.setMinimumHeight(60)
        # 关键：使用 move(x, y) 设置位置
        self.current_lyric_label.move(15, 30)
        # 将标签添加到窗口（注意：不是 layout，而是直接 setParent）
        self.current_lyric_label.setParent(self)  # self 是你的主窗口（QWidget）        #创建播放列表窗口
        self.list = playlist.PlayList(self.geometry().x(), self.geometry().y(), self.geometry().width(),
                                  self.geometry().height(), self)


        # 功能组
        self.play = QMediaPlayer()



        #快捷键
        self.space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.space_shortcut.activated.connect(self.play_audio)

        # 创建上箭头快捷键
        self.up_shortcut = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.up_shortcut.activated.connect(self.increase_volume)

        # 创建下箭头快捷键
        self.down_shortcut = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.down_shortcut.activated.connect(self.decrease_volume)

        # 连接信号和槽
        self.close.clicked.connect(self.exit_all)
        self.fixed.clicked.connect(self.win_fixed)
        self.min.clicked.connect(self.minimize_window)
        self.music_list.clicked.connect(self.musiclist)
        self.btn_play.clicked.connect(self.play_audio)
        self.player.positionChanged.connect(self.update_slider_position)
        self.player.durationChanged.connect(self.set_slider_duration)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.volume_slider.valueChanged.connect(lambda v: self.player.setVolume(v))


    # 创建淡入淡出动画
    def start_animation(self,start,end):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(1000)  # 动画持续时间（毫秒）
        self.animation.setStartValue(start)  # 起始透明度
        self.animation.setEndValue(end)  # 结束透明度
        self.animation.start()
        return self.animation

    # 置顶与撤销置顶窗口
    def win_fixed(self):
        if self.windowFlags() & Qt.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.list.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)

        else:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.list.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.show()  # 必须重新 show() 才能生效
        self.list.show()

    # 窗口最小化
    def minimize_window(self):
        self.showMinimized()
        self.list.showMinimized()

    # 关闭按钮,渐隐动画完成后关闭程序
    def exit_all(self):
        self.anim = self.start_animation(1,0)
        self.anim = self.list.start_animation(1, 0)
        self.anim.finished.connect(sys.exit)


    #创建播放列表窗口
    def musiclist(self):
        if self.list.isVisible():
            self.list.start_animation(1, 0)

            # 连接动画结束信号，在动画完成后隐藏窗口
            self.list.animation.finished.connect(self.list.hide)
        else:
            self.list.start_animation(0, 1)
            self.list.show()

    # 当有对象被拖入窗口时触发此事件
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():  # 检查是否是 URL（文件）
            event.acceptProposedAction()  # 接受动作
        else:
            event.ignore()

    # 当有对象被释放（放下）时触发此事件
    def dropEvent(self, event):
        urls = event.mimeData().urls()  # 获取所有拖放的文件URL
        if urls:
            for url in urls:
                file_path = url.toLocalFile()  # 转换为本地文件路径
                if file_path.lower().endswith('.mp3'):  # 确保是MP3文件
                    print(f"拖放的文件路径: {file_path}")
                    self.add_playlist(file_path)
                else:
                    print(f"忽略非 MP3 文件: {file_path}")
        else:
            event.ignore()

    # 将文件路径加入播放列表文件
    def add_playlist(self,file_path):
        with open("./play_list.txt", 'a+') as f:
            f.seek(0)  # 移动到文件开头读取
            if file_path not in f.read():
                f.write(file_path + '\n')
                print("已添加")
            else:
                print("已存在")
        self.list.load_music_folder()
        self.list.update_playlist_display()

    #播放按钮，播放音乐
    def play_audio(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    #水平裁切图像，并保存在列表中
    def crop_image_into_four_horizontal(self, image_path):
        # 加载原始图片
        original_pixmap = QPixmap(image_path)

        if original_pixmap.isNull():
            print("图片加载失败，请检查路径")
            return

        # 获取原始图片的尺寸
        width = original_pixmap.width()
        height = original_pixmap.height()

        # 计算每个分割部分的宽度
        part_width = width // 4

        # 创建一个列表用于存储裁剪后的图像
        cropped_images = []

        for i in range(4):
            # 定义每个部分的矩形区域
            rect = QRect(i * part_width, 0, part_width, height)

            # 裁剪图片
            cropped = original_pixmap.copy(rect)

            # 将裁剪后的图像添加到列表中
            cropped_images.append(cropped)
        return cropped_images, part_width, height

    def update_slider_position(self, position):
        """更新进度条位置"""
        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position)

    def set_slider_duration(self, duration):
        """设置进度条总长度"""
        self.progress_slider.setRange(0, duration)
        # # 更新总时间显示
        # self.total_time_label.setText(self.format_time(duration))

    def slider_pressed(self):
        """进度条按下事件"""
        self.list.lyric_timer.stop()  # 暂停歌词更新

    def slider_released(self):
        """进度条释放事件"""
        position = self.progress_slider.value()
        self.player.setPosition(position)
        self.list.lyric_timer.start(100)  # 恢复歌词更新
        self.list.update_lyrics()  # 立即更新歌词

    def increase_volume(self):
        self.current_volume = self.volume_slider.value()
        self.volume_slider.setValue(min(self.current_volume + 15, 100))

    def decrease_volume(self):
        self.current_volume = self.volume_slider.value()
        self.volume_slider.setValue(max(self.current_volume - 15, 0))
if __name__ == "__main__":
    player = QApplication(sys.argv)
    music = Window()
    #设置图标
    player.setWindowIcon(QIcon("./skin/Purple/TTPlayer.ico"))  # 替换为你的图标文件路径
    music.show()
    player.exec_()