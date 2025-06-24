from .logger import mylogger
from random import randint
import json
import random
import pathlib

import pygame
import keyboard
import time
from tinytag import TinyTag
import math
import os

# import sdl2
# import sdl2.ext
# import sdl2.sdl.mixer

# sdl2.SDL_Init(sdl2.SDL_INIT_AUDIO)
# sdl2.sdl.mixer.Mix_OpenAudio(44100, sdl2.sdl.mixer.MIX_DEFAULT_FORMAT, 2, 1024)

pygame.mixer.init()



class Item:
    ID_LEN = 12
    ID_MIN = int("1" + "0" * (ID_LEN - 1))
    ID_MAX = int("9" * ID_LEN)

    def __init__(
        self,
        filename: pathlib.Path | str,
        name: str | None = None,
        weight: float = 100.0,
        *args,
        **kwargs,
    ):
        self._id: int = randint(Item.ID_MIN, Item.ID_MAX)

        self.weight: float = weight

        if isinstance(filename, str):
            self.filename: pathlib.Path = pathlib.Path(filename)
        elif isinstance(filename, pathlib.Path):
            self.filename: pathlib.Path = filename

        if name is None:
            self.name: str = self.filename.stem
        else:
            self.name: str = name

        tag = TinyTag.get(self.filename)

        # 歌曲时长
        self.time_long: float = tag.duration or -1
        if self.time_long == -1:
            mylogger.error(f"无法获取{self.filename}的时长")
            raise ValueError("无法获取时长")

        # 歌曲专辑
        self.album: str = tag.album or "未知"

        # 歌手
        self.artist: str = tag.artist or "未知"

    def get_id(self) -> int:
        return self._id

    def set_id(self, id: int):
        if isinstance(id, int) and Item.ID_MIN <= id <= Item.ID_MAX:
            self._id = id
        else:
            raise ValueError("Invalid ID")

    def __str__(self):
        return f"{self.name} ({self.time_long}s)\t | \t{('W='+str(self.weight))}\t | \tID={self.get_id()}"

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        return json.dumps(
            obj={
                "id": self.get_id(),
                "filename": str(self.filename),
                "name": self.name,
                "time_long": self.time_long,
                "weight": self.weight,
                "album": self.album,
                "artist": self.artist,
            }
        )

    def play(self):
        mylogger.info("正在播放: %s" % self.filename)

        pygame.mixer.init()
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        # music = self.get_song()
        # if not music:
        #     mylogger.error(f"无法加载音频文件{self.filename}")
        #     sdl2.SDL_Quit()
        #     return

        # sdl2.sdl.mixer.Mix_PlayMusic(music, 1)  # 播放音乐

        # while sdl2.sdl.mixer.Mix_PlayingMusic():
        #     time.sleep(0.1)

        # sdl2.sdl.mixer.Mix_HaltMusic()  # 停止播放
        # sdl2.sdl.mixer.Mix_FreeMusic(music)  # 释放音乐

        # # 退出 SDL
        # sdl2.sdl.mixer.Mix_CloseAudio()
        # sdl2.SDL_Quit()

    def stop_playing(self):
        # sdl2.sdl.mixer.Mix_HaltMusic()  # 停止播放
        # sdl2.SDL_Quit()
        pygame.mixer.music.stop()

    def continue_playing(self):
        # sdl2.sdl.mixer.Mix_PlayMusic(self.get_song(), 1)  # 播放音乐
        pygame.mixer.music.unpause()

    def get_pos(self):
        # return self.get_song().pos
        return self.get_song().get_pos()

    def set_pos(self, pos: int):
        # self.get_song().pos = pos
        self.get_song().set_pos(pos)

    def get_song(self):
        return pygame.mixer.music


class PlaylistBase:
    def __init__(
        self, name: str, items: list[Item] | None = None, save_path: str | None = None
    ):
        self.name: str = name

        if items is not None:
            self.gen_from_list(items)
        else:
            self.items: list[Item] = []

        if save_path is not None:
            if not save_path.endswith(".json"):
                save_path += ".json"
            if os.path.exists(save_path):
                mylogger.error(f"文件{save_path}已存在, 可能覆盖原文件")
                raise FileExistsError(f"文件{save_path}已存在")
            self.save_path = save_path
        else:
            self.save_path = f"playlist/playlist_{self.name}.json"

    def add_item(self, item: Item):
        self.items.append(item)

    def gen_from_list(self, items: list[Item]):
        self.items = items
        self._check_ids_not_same_and_fix()

    def to_json(self):
        return json.dumps(
            [
                {
                    "id": item.get_id(),
                    "filename": str(item.filename),
                    "name": item.name,
                    "time_long": item.time_long,
                    "weight": item.weight,
                }
                for item in self.items
            ]
        )

    def from_json(self, json_str: str):
        items = json.loads(json_str)
        
        self.gen_from_list([Item(**item) for item in items])
        

    def save_to_file(self):
        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))
        with open(self.save_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return self

    def load_from_file(self):

        if not os.path.exists(os.path.dirname(self.save_path)):
            os.makedirs(os.path.dirname(self.save_path))
        with open(self.save_path, "r", encoding="utf-8") as f:
            self.from_json(f.read())

        return self

    def _check_ids_not_same_and_fix(self):
        """
        检测ID是否重复，如果重复则生成新的ID, 直到所有ID不重复
        注: 如果Item数量过多，可能需要较长时间, 如果Item数大于ID_MAX-ID_MIN，则会死循环
        """
        mylogger.info("Checking IDs...")
        sorted_items = sorted(self.items, key=lambda x: x.get_id())
        for i in range(len(sorted_items) - 1):
            if sorted_items[i].get_id() == sorted_items[i + 1].get_id():
                sorted_items[i + 1].set_id(randint(Item.ID_MIN, Item.ID_MAX))
                mylogger.warning(
                    "Duplicate ID found, generating new ID for item: %s"
                    % sorted_items[i + 1].name
                )
                mylogger.debug("New ID: %d" % sorted_items[i + 1].get_id())
                self._check_ids_not_same_and_fix()

        self.items = sorted_items.copy()
        mylogger.info("IDs checked and fixed")

    def gen_from_dir(self, dir_path: str, ext: str = "mp3"):
        """
        从目录中生成播放列表
        """
        mylogger.info(f"正在从{dir_path}中生成播放列表, 请稍等")
        mylogger.info(f"文件扩展名: {ext}")

        self.items = []
        for file in pathlib.Path(dir_path).glob(f"*.{ext}"):
            try:
                item = Item(file)
                self.items.append(item)
            except ValueError:
                mylogger.warning(f"无法获取{file}的时长, 跳过")

        return self

        self.gen_from_list(items)

    def change_weight_and_save(self, item: Item, weight: float):
        item.weight = weight
        self.save_to_file()

    def __str__(self):
        s = f"{self.name} ({len(self.items)} items):"
        for i, itm in enumerate(self.items):
            s += f"\n {i+1})\t{itm}"
        return s

    def __repr__(self):
        return self.__str__()


class Playlist(PlaylistBase):
    def __init__(
        self,
        name: str,
        items: list[Item] | None = None,
        save_path: str | None = None,
    ):
        super().__init__(
            name,
            items=items,
            save_path=save_path,
        )

    def random_recommend(self) -> Item:
        return random.choices(self.items, weights=[item.weight*0.01 for item in self.items],k=1)[
            0
        ]


    def play_one(self):
        item = self.random_recommend()
        item.play()

    def play_all(self):
        has_pressed_capslock = False
        pressed_capslock_time = 0
        item_music = None

        def on_key_pressed(event):
            TWICE_PRESSING_TIME = 0.8

            nonlocal item_music
            nonlocal has_pressed_capslock
            nonlocal pressed_capslock_time

            # 0.6s内双击capslock时切歌
            if event.name == "caps lock" and event.event_type == keyboard.KEY_DOWN:
                if not has_pressed_capslock:
                    mylogger.info(f"在{TWICE_PRESSING_TIME}s内再按一次CapsLock切歌")
                    has_pressed_capslock = True
                    pressed_capslock_time = time.time()
                else:
                    pressed_casplock_twice_in_time = (
                        time.time() - pressed_capslock_time
                    ) <= TWICE_PRESSING_TIME

                    if pressed_casplock_twice_in_time:
                        if item_music is None:
                            mylogger.error("还没有播放任何音乐")
                            return
                        item_music.stop()
                        item_music = None
                        has_pressed_capslock = False
                        return
                    else:
                        has_pressed_capslock = False
                        mylogger.info(
                            "想切歌要连续按两下CapsLock, 你按得太慢了, 快一点呢? 再试一次: 双击CapsLock!"
                        )

        keyboard.hook(on_key_pressed)
        while True:
            itm = self.random_recommend()
            start_time = time.time()

            # 加载并播放音乐
            mylogger.info(f"正在播放: {itm.name}")
            item_music = itm.get_song()
            if not item_music:
                mylogger.error(f"无法加载音频文件{itm.filename}")
                return

            itm.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            end_time = time.time()
            prg = (end_time - start_time) / itm.time_long * 100
            mylogger.debug(f"播放进度: {prg:.2f}%")

            self.upgrade_item_weight(itm, prg)

    def upgrade_item_weight(
        self, item: Item, prg: float, eta: float = 1, alpha: float = math.e
    ):
        """
        更新权重
        此算法由 Fexcode 编写
        """
        original_weight = item.weight

        prg = round(prg, 2) + 0.01  # 避免prg为0

        avg_weight = sum([item.weight for item in self.items]) / len(self.items)

        pred = 100 * (item.weight / (avg_weight + item.weight))
        d = prg - pred

        dW = (
            d * min(eta, original_weight) * math.log((1 / pred + alpha), alpha)
        )  # 权重过低更新就更慢一点

        if (new_weight := (item.weight + dW)) <= 0:
            self.change_weight_and_save(item, 0.01)
        else:
            self.change_weight_and_save(item, new_weight)

        mylogger.debug(f"预期prg: {pred:.2f}, 实际prg: {prg:.2f}, dW: {dW:.2f}")
        mylogger.debug(f"更新{item.name}的权重: {original_weight}->{item.weight:.2f}")
