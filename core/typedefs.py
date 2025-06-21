from .logger import mylogger
from random import randint
import json
import random
import pathlib
from playsound import playsound
import shutil
import os


class Item:
    ID_LEN = 12
    ID_MIN = int("1" + "0" * (ID_LEN - 1))
    ID_MAX = int("9" * ID_LEN)

    def __init__(
        self,
        filename: pathlib.Path | str,
        time_long: float,
        name: str | None = None,
        weight: float = 100.0,
    ):
        self._id: int = randint(Item.ID_MIN, Item.ID_MAX)
        self.time_long: float = time_long  # in seconds
        self.weight: float = weight

        if isinstance(filename, str):
            self.filename: pathlib.Path = pathlib.Path(filename)
        elif isinstance(filename, pathlib.Path):
            self.filename: pathlib.Path = filename

        if name is None:
            self.name: str = self.filename.stem
        else:
            self.name: str = name

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
            }
        )

    def play(self):
        mylogger.debug("正在播放: %s" % self.filename)

        # 不能有中文路径, 所以移动到temp目录,文件名用id
        # 获取环境变量TEMP
        temp_dir = os.getenv("TEMP")
        if temp_dir is None:
            temp_dir = os.path.expanduser("~")  # 使用主目录作为默认临时目录
        else:
            temp_dir = pathlib.Path(temp_dir)

        temp_file = f"{temp_dir}/{self.get_id()}.{self.filename.suffix}"
        mylogger.debug("临时文件: %s" % temp_file)

        shutil.copy(self.filename, temp_file)
        playsound(str(temp_file))
        os.remove(temp_file)


class PlaylistBase:
    def __init__(self, name: str, items: list[Item] | None = None):
        self.name: str = name

        if items is not None:
            self.gen_from_list(items)
        else:
            self.items: list[Item] = []

    def add_item(self, item: Item):
        self.items.append(item)

    def gen_from_list(self, items: list[Item]):
        self.items = items.copy()
        self._check_ids_not_same_and_fix()

    def to_json(self):
        print([item.__dict__ for item in self.items])
        print("||||| ", [item.to_json() for item in self.items])
        return json.dumps([item.to_json() for item in self.items])

    def from_json(self, json_str: str):
        items = json.loads(json_str)
        self.gen_from_list([Item(**item) for item in items])

    def save_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    def load_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            self.from_json(f.read())

    def _check_ids_not_same_and_fix(self):
        """
        检测ID是否重复，如果重复则生成新的ID, 直到所有ID不重复
        注: 如果Item数量过多，可能需要较长时间, 如果Item数大于ID_MAX-ID_MIN，则会死循环
        """
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

    def __str__(self):
        s = f"{self.name} ({len(self.items)} items):"
        for i, itm in enumerate(self.items):
            s += f"\n {i+1})\t{itm}"
        return s

    def __repr__(self):
        return self.__str__()


class Playlist(PlaylistBase):
    def __init__(self, name: str, items: list[Item] | None = None):
        super().__init__(name, items)

    def random_recommend(self) -> Item:
        return random.choices(
            self.items,
            weights=[item.weight for item in self.items],
        )[0]

    def play_one(self):
        item = self.random_recommend()
        item.play()
