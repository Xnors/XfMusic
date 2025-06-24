import tkinter as tk
from tkinter import ttk
import time
import core
from core.logger import mylogger
from tinytag import TinyTag
import keyboard
import pygame


class MusicPlayer:
    """音乐播放器核心逻辑"""

    def __init__(self):
        try:
            self.playlist = (
                core.Playlist("test_playlist3")
                .gen_from_dir("./test_musics/")
                .save_to_file()
            )
            self.current_song = None
            self.is_playing = True  # 默认自动播放
            self.progress = 0
            self.last_song_id = None  # 记录上一首歌ID
            self.last_song_start_time = 0  # 记录上一首歌开始播放时间

            # # 初始化第一首歌
            # self.current_song = self.get_random_song()
            # pygame.mixer.music.load(str(self.current_song.filename))
            self.play_song(self.get_random_song())
            mylogger.info("MusicPlayer initialized successfully")
        except Exception as e:
            mylogger.error(f"Failed to initialize MusicPlayer: {e}")
            raise

    def get_random_song(self):
        """获取随机歌曲(确保不重复)"""
        if len(self.playlist.items) <= 1:
            return self.playlist.items[0]

        new_song = self.playlist.random_recommend()

        # 确保不重复同一首歌
        while new_song.get_id() == self.last_song_id and len(self.playlist.items) > 1:
            new_song = self.playlist.random_recommend()

        self.last_song_id = new_song.get_id()
        self.last_song_start_time = time.time()
        return new_song

    def play_song(self, song):
        """播放指定歌曲"""

        if self.current_song is not None:
            pygame.mixer.music.stop()
        

        self.current_song = song
        pygame.mixer.music.load(str(self.current_song.filename))

        if self.is_playing:
            pygame.mixer.music.play()

        mylogger.info(f"Playing song: {self.current_song.name}")
        self.last_song_start_time = time.time()
        return True

    def playpause(self):
        """播放/暂停控制"""
        if not self.playlist or not self.current_song:
            mylogger.warning("Playlist is empty or no current song")
            return False

        try:
            if self.is_playing:
                # sdl2.sdlmixer.Mix_PauseMusic()
                pygame.mixer.music.pause()
                self.is_playing = False
                mylogger.info("Playback paused")
            else:
                # sdl2.sdlmixer.Mix_ResumeMusic()
                pygame.mixer.music.unpause()
                self.is_playing = True
                mylogger.info("Playback resumed")
            return self.is_playing
        except Exception as e:
            mylogger.error(f"Play/pause error: {e}")
            return False

    def next_song(self):
        """切换下一首"""
        if self.current_song:
            if self.last_song_start_time <= 0:
                mylogger.error("last_song_start_time is not set!")

            self.playlist.upgrade_item_weight(
                self.current_song,
                prg=(
                    100
                    * (
                        (time.time() - self.last_song_start_time)
                        / self.current_song.time_long
                    )
                ),
            )
        return self.play_song(self.get_random_song())

    def check_song_end(self):
        """检查歌曲是否播放结束"""
        if self.current_song and not pygame.mixer.music.get_busy():
            # 歌曲播放结束，更新权重
            try:
                if self.current_song:
                    self.playlist.upgrade_item_weight(
                        self.current_song,
                        prg=100,  # 歌曲播放完成
                    )
                    mylogger.info(f"Updated weight for song: {self.current_song.name}")
            except Exception as e:
                mylogger.error(f"Failed to update song weight: {e}")

            # 播放下一首
            self.next_song()
            return True
        return False

    def get_progress(self):
        """获取播放进度(秒)"""
        try:
            if self.current_song and self.current_song:
                pos = self.current_song.get_pos() / 1000  # 转换为秒
                return pos if pos >= 0 else 0
            return 0
        except Exception as e:
            mylogger.error(f"Failed to get progress: {e}")
            return 0

    def get_duration(self):
        """获取歌曲总时长(秒)"""
        try:
            if self.current_song:
                tag = TinyTag.get(str(self.current_song.filename))
                return tag.duration
            return 0
        except Exception as e:
            mylogger.error(f"Failed to get duration: {e}")
            return 0


class PlayerGUI:
    """播放器GUI界面"""

    def __init__(self, player):
        self.player = player
        self.root = tk.Tk()
        self.root.title("简易音乐播放器")
        self.root.geometry("600x400")
        self.create_menu()  # 创建菜单栏
        self.create_widgets()
        self.root.after(100, self.update_ui)  # 定期更新UI
        self.update_song_info()  # 初始化歌曲信息

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="从目录导入", command=self.import_from_directory)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        self.root.config(menu=menubar)

    def import_from_directory(self):
        """从目录导入歌曲"""
        from tkinter import filedialog
        dir_path = filedialog.askdirectory(title="选择音乐目录")
        if dir_path:
            try:
                # 创建新播放列表
                new_playlist = core.Playlist("current_playlist").gen_from_dir(dir_path)
                self.player.playlist = new_playlist
                
                # 更新UI
                self.listbox.delete(0, tk.END)
                for song in new_playlist.items:
                    self.listbox.insert(tk.END, song.name)
                
                # 重置当前歌曲
                self.player.current_song = None
                self.update_song_info()
                mylogger.info(f"成功从目录导入歌曲: {dir_path}")
            except Exception as e:
                mylogger.error(f"导入歌曲失败: {e}")

    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        mainframe = ttk.Frame(self.root, padding=10)
        mainframe.pack(fill=tk.BOTH, expand=True)

        # 顶部框架(用于放置歌曲信息和更多按钮)
        top_frame = ttk.Frame(mainframe)
        top_frame.pack(fill=tk.X, pady=10)

        # 歌曲信息
        self.song_info = ttk.Label(
            top_frame, text="正在加载歌曲...", font=("微软雅黑", 12)
        )
        self.song_info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 更多按钮(显示权重信息)
        self.more_btn = ttk.Button(
            top_frame, text="更多", command=self.show_weight_info
        )
        self.more_btn.pack(side=tk.RIGHT)

        # 控制按钮
        btn_frame = ttk.Frame(mainframe)
        btn_frame.pack(pady=5)

        self.play_btn = ttk.Button(btn_frame, text="⏸", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(btn_frame, text="▶", command=self.next_song)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress = ttk.Scale(
            mainframe,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            command=self.update_progress,
        )
        self.progress.pack(fill=tk.X, pady=5)
        self.progress.set(0)

        # 歌曲列表
        self.listbox = tk.Listbox(mainframe, selectmode=tk.SINGLE)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        # 填充歌曲列表(只显示歌曲名)
        for song in self.player.playlist.items:
            self.listbox.insert(tk.END, song.name)

        # 绑定双击事件
        self.listbox.bind("<Double-Button-1>", self.on_song_select)
        self.start_handle_key()

    def start_handle_key(self):
        self.has_pressed_capslock = False
        self.last_pressed_capslock_time = 0

        def on_key_pressed(event):
            if event.name == "caps lock" and event.event_type == "down":
                if not self.has_pressed_capslock:
                    self.last_pressed_capslock_time = time.time()
                    self.has_pressed_capslock = True
                    mylogger.info("再按一次CapsLock可以切歌!")
                elif time.time() - self.last_pressed_capslock_time <= 0.8:
                    self.next_song(None)
                    self.has_pressed_capslock = False
                else:
                    mylogger.info("双击CapsLock可以切歌, 你按得太慢了!")
                    self.has_pressed_capslock = False

        keyboard.hook(on_key_pressed)

    def next_song(self, event=None):
        """切换下一首"""
        if event:
            mylogger.debug("next_song", f"{event=}")
        else:
            mylogger.debug("next_song")
        self.player.next_song()
        self.update_song_info()

    def on_song_select(self, event):
        """处理歌曲列表双击事件"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            song = self.player.playlist.items[index]
            self.player.play_song(song)
            self.update_song_info()

    def show_weight_info(self):
        """显示歌曲信息"""
        if self.player.current_song:
            weight = self.player.current_song.weight
            # 创建弹窗
            popup = tk.Toplevel(self.root)
            popup.title("歌曲信息")
            popup.geometry("300x150")

            # 添加内容, 左对齐

            ttk.Label(
                popup,
                text=f"歌曲: {self.player.current_song.name}",
                font=("微软雅黑", 12),
            ).pack(pady=5)
            ttk.Label(popup, text=f"喜爱值: {weight:.2f}", font=("微软雅黑", 10)).pack(
                pady=5
            )
            ttk.Label(
                popup,
                text=f"专辑: {self.player.current_song.album}",
                font=("微软雅黑", 10),
            ).pack(pady=5)
            ttk.Label(
                popup,
                text=f"作者: {self.player.current_song.artist}",
                font=("微软雅黑", 10),
            ).pack(pady=5)

            mylogger.info(
                f"歌曲: {self.player.current_song.name}, 喜爱值: {weight:.2f}, 专辑: {self.player.current_song.album}, 作者: {self.player.current_song.artist}"
            )

            # 关闭按钮
            ttk.Button(popup, text="关闭", command=popup.destroy).pack(pady=10)
        else:
            self.song_info.config(text="当前没有播放歌曲")

    def update_song_info(self):
        """更新歌曲信息"""
        if self.player.current_song:
            self.song_info.config(text=f"当前播放：\n{self.player.current_song.name}")

    def toggle_play(self):
        """播放/暂停切换"""
        if self.player.playpause():
            self.play_btn.config(text="⏸")
        else:
            self.play_btn.config(text="▶")

    def update_progress(self, value):
        """更新进度条"""
        try:
            self.player.progress = float(value)
        except:
            pass

    def update_ui(self):
        """UI更新循环"""
        try:
            # 检查歌曲是否结束
            if self.player.check_song_end():
                self.update_song_info()

            if self.player.current_song:
                current_time = self.player.get_progress()
                total_time = self.player.get_duration()

                if total_time > 0:
                    self.progress.config(to=total_time)
                    self.progress.set(current_time)

            self.root.after(100, self.update_ui)
        except Exception as e:
            mylogger.error(f"UI更新错误: {e}")

    def run(self):
        """启动主循环"""
        self.root.mainloop()


if __name__ == "__main__":
    # 创建播放器和GUI
    try:
        player = MusicPlayer()
        gui = PlayerGUI(player)
        gui.run()
    except Exception as e:
        mylogger.error(f"Application error: {e}")
    finally:
        # sdl2.sdlmixer.Mix_CloseAudio()
        # sdl2.SDL_Quit()
        pygame.mixer.quit()
