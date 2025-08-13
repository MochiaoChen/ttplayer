import sys, os, random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QListWidgetItem, QListWidget, QShortcut
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, pyqtSlot, QPropertyAnimation, QUrl, QRect, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPainterPath, QPalette, QBrush, QKeySequence
from PyQt5.QtMultimedia import QMediaPlaylist, QMediaContent

class PlayList(QWidget):
    def __init__(self, x=255, y=255, width=2, height=0, first=None):
        super().__init__()
        self.first = first
        self.ui = None
        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.volume = 30
        # 启用拖放支持
        self.setAcceptDrops(True)
        # 随机播放模式
        # self.shuffle_mode = True
        self.current_index = 0

        # 加载ui
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
        self.ui = uic.loadUi("./Designer_ui/list.ui", self)
        # 去掉标题栏
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.lyrics = []
        self.current_lyric_index = 0

        # 播放列表界面透明显示
        self.song_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: transparent;
                color: white; /* 设置文字颜色 */
            }
            QListWidget::item:selected {
                background-color: rgba(100, 100, 100, 100); /* 半透明选中项 */
            }
        """)
        # 加载主窗口背景图
        self.background_path = "./skin/Purple/playlist_skin.bmp"
        pixmap = QPixmap(self.background_path)
        pixmap = self.round_pixmap(pixmap, 8)  # 一行完成裁切并赋值

        # 设置窗口大小为图片大小
        self.setFixedSize(pixmap.width(), pixmap.height())

        # 或者保持原图大小，居中/左上对齐显示
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(pixmap))  # 原图大小
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # 设置窗口为无边框
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # 设置播放列表窗口和主窗口对齐
        self.move(self.x, self.y + self.height)
        self.resize(self.width, self.geometry().height())

        # 启动时渐显动画
        self.start_animation(0, 1)

        # 自动加载歌词列表
        self.load_music_folder()

        # 按钮组渲染
        btn = {
            self.close: './skin/Purple/close.bmp',

        }
        for key in btn:
            self.temp = self.crop_image_into_four_horizontal(btn[key])
            # 将 QPixmap 设置给 QPushButton
            icon = QIcon(self.round_pixmap(self.temp[0][0], 3))
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

        # 定时器
        self.lyric_timer = QTimer()
        self.lyric_timer.timeout.connect(self.update_lyrics)
        self.lyric_timer.start(1500)  # 每100ms检查一次歌词

        # 快捷键
        self.space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.space_shortcut.activated.connect(self.first.play_audio)
        # 创建向右箭头快捷键
        self.down_shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.down_shortcut.activated.connect(self.play_next)
        # 创建向左箭头快捷键
        self.down_shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.down_shortcut.activated.connect(self.play_preview)

        # 连接信号和槽
        self.ui.close.clicked.connect(self.exit_all)
        self.ui.song_list.itemDoubleClicked.connect(self.select_song)

        self.show()

    # 将同级目录下的play_list.txt文件里的歌曲地址读进self.playlist列表中
    def load_music_folder(self):
        try:
            with open("./play_list.txt", 'r', encoding='utf-8') as f:
                temp_playlist = f.read().splitlines()
            self.playlist = temp_playlist
            # 更新播放列表显示
            self.update_playlist_display()

        except Exception as e:
            print(f"加载失败：{e}")  # 打印具体错误

    def update_playlist_display(self):
        """更新播放列表显示"""
        # self.sync_playlist_to_ui()

        self.song_list.clear()
        for path in self.playlist:
            # 添加音乐文件到self.all_playlist中
            self.first.all_playlist.addMedia(QMediaContent(QUrl.fromLocalFile(path)))
            # 提取文件名（不含后缀）
            file_name = os.path.basename(path)  # 例如："歌曲1.mp3"
            name_without_ext = os.path.splitext(file_name)[0]  # 例如："歌曲1"
            # 创建列表项并设置居中对齐
            item = QListWidgetItem(name_without_ext)
            item.setTextAlignment(Qt.AlignCenter)  # 关键：设置文本居中

            self.song_list.addItem(item)  # 添加带对齐属性的条目


    # 创建淡入淡出动画
    def start_animation(self, start, end):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(800)  # 动画持续时间（毫秒）
        self.animation.setStartValue(start)  # 起始透明度
        self.animation.setEndValue(end)  # 结束透明度
        self.animation.start()
        return self.animation

    # 关闭按钮,渐隐动画完成后关闭程序
    def exit_all(self):
        self.anim = self.start_animation(1, 0)
        self.anim.finished.connect(self.hide)

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
    def add_playlist(self, file_path):
        with open("./play_list.txt", 'a+') as f:
            f.seek(0)  # 移动到文件开头读取
            if file_path not in f.read():
                f.write(file_path + '\n')
                print("已添加")
            else:
                print("已存在")
        self.load_music_folder()
        self.update_playlist_display()

    # 定义圆角函数（只需写一次）
    def round_pixmap(self, pixmap, radius):
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

    def select_song(self, item=None):
        self.current_index = self.song_list.row(item)
        self.first.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.playlist[self.current_index])))
        # self.first.volume_slider.setValue(min(self.first.volume_slider.current_volume, 100))
        # self.first.player.setVolume(self.first.volume_slider.current_volume)
        self.first.player.play()
        self.load_lyrics(self.playlist[self.current_index], self.first)
        self.first.status_label.setText(os.path.splitext(os.path.basename(self.playlist[self.current_index]))[0])
    # 水平裁切图像，并保存在列表中
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

    def load_lyrics(self, audio_path, first):
        """每次加载歌词时更新悬浮窗位置"""
        self.first.lrc.move(self.geometry().x() + (self.geometry().width() / 2) - self.first.lrc.geometry().width() / 2,
                      self.geometry().y() + self.geometry().height())

        """加载与音频同名的 .lrc 歌词文件"""
        base, _ = os.path.splitext(audio_path)
        lrc_path = base + ".lrc"
        self.lyrics = []
        # self.current_lyric_index = 1

        if not os.path.exists(lrc_path):
            self.first.current_lyric_label.setText("111")
            return

        # 尝试多种编码读取歌词文件
        encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
        for encoding in encodings:
            try:
                with open(lrc_path, "r", encoding=encoding) as f:
                    lines = f.readlines()
                break
            except UnicodeDecodeError:
                continue
        else:
            return

        # 解析歌词
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 处理标准歌词格式 [mm:ss.xx]歌词内容
            if line.startswith('[') and ']' in line:
                parts = line.split(']')
                text = ''.join(parts[1:]).strip()

                # 处理多个时间标签的情况
                for time_part in parts[:-1]:
                    time_part = time_part.strip('[')
                    try:
                        # 解析时间
                        if ':' in time_part and '.' in time_part:
                            # 格式: mm:ss.xx
                            minutes, seconds = time_part.split(':')
                            seconds, millis = seconds.split('.')
                            total_ms = int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(millis) * 10
                        elif ':' in time_part:
                            # 格式: mm:ss
                            minutes, seconds = time_part.split(':')
                            total_ms = int(minutes) * 60 * 1000 + int(seconds) * 1000
                        else:
                            continue

                        self.lyrics.append((total_ms, text))
                    except (ValueError, IndexError):
                        continue
        # 按时间排序
        self.lyrics.sort(key=lambda x: x[0])
        self.current_lyric_index = -1  # 重置当前歌词索引

    def update_lyrics(self):
        """根据当前播放时间更新歌词显示"""
        # if not self.lyrics or self.player.state() != QMediaPlayer.PlayingState:
        #     return

        current_time = self.first.player.position()

        # 找到当前歌词行
        new_index = -1
        for i, (timestamp, _) in enumerate(self.lyrics):
            if timestamp <= current_time:
                if i < len(self.lyrics) - 1 and self.lyrics[i + 1][0] > current_time:
                    new_index = i
                    break
            else:
                break

        # 如果是最后一行歌词
        if new_index == -1 and self.lyrics and self.lyrics[-1][0] <= current_time:
            new_index = len(self.lyrics) - 1

        # 如果歌词行发生变化，更新显示
        if new_index != self.current_lyric_index:
            self.current_lyric_index = new_index

            # 更新顶部大字体歌词
            if 0 <= new_index < len(self.lyrics):
                self.first.current_lyric_label.setText(self.lyrics[new_index][1])
                '''更新浮动歌词条'''
                self.first.lrc.lyric_label.clear()  # 清空文本
                self.first.lrc.lyric_label.setText(self.lyrics[new_index][1])
                self.first.lrc.lyric_label.fade_in()

                self.first.current_lyric_label.adjustSize()

                self.first.current_lyric_label.fade_in()
            else:
                self.first.current_lyric_label.setText("")
                self.first.current_lyric_label.adjustSize()
                # print(self.lyrics[new_index][1])
                # '''更新浮动歌词条'''
                # self.first.lrc.lyric_label.setText(self.lyrics[new_index][1])
                # self.first.lrc.lyric_label.fade_in()

    def play_next(self):
        """播放下一首歌曲"""
        # if not self.first.all_playlist:
        #     return

        if self.first.shuffle_mode:
            # 随机播放下一首
            if len(self.playlist) > 1:
                new_index = self.current_index
                while new_index == self.current_index:
                    new_index = random.randint(0, len(self.playlist) - 1)
                self.current_index = new_index

                self.first.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.playlist[self.current_index])))
                self.first.player.play()
                self.load_lyrics(self.playlist[self.current_index], self.first)
                self.song_list.setCurrentRow(self.current_index)
                self.first.status_label.setText(os.path.splitext(os.path.basename(self.playlist[self.current_index]))[0])
        else:
            # 顺序播放下一首
            self.current_index +=1
            self.first.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.playlist[self.current_index])))
            self.first.player.play()
            self.load_lyrics(self.playlist[self.current_index], self.first)
            self.song_list.setCurrentRow(self.current_index)
            self.first.status_label.setText(os.path.splitext(os.path.basename(self.playlist[self.current_index]))[0])

    def play_preview(self):
        """播放上一首歌曲"""
        # if not self.first.all_playlist:
        #     return

        if self.first.shuffle_mode:
            # 随机播放上一首
            if len(self.playlist) > 1:
                new_index = self.current_index
                while new_index == self.current_index:
                    new_index = random.randint(0, len(self.playlist) - 1)
                self.current_index = new_index
        else:
            # 顺序播放上一首
            self.current_index -=1
            self.first.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.playlist[self.current_index])))
            self.first.player.play()
            self.load_lyrics(self.playlist[self.current_index], self.first)
            self.song_list.setCurrentRow(self.current_index)

    def sync_playlist_to_ui(self):
        """将 QMediaPlaylist 中的所有歌曲同步到 QListWidget"""
        self.song_list.clear()  # 清空现有内容
        for i in range(self.first.all_playlist.mediaCount()):
            # 获取媒体内容（QMediaContent）
            media = self.first.all_playlist.media(i)
            # 从 URL 提取文件名（你可以自定义显示格式）
            url = media.canonicalUrl()
            song_name = url.fileName()  # 只取文件名，比如 "甜蜜蜜.mp3"
            # 也可以去掉扩展名
            # song_name = QFileInfo(song_name).baseName()
            self.song_list.addItem(song_name)
