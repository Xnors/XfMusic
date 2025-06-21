from core import *


def main():
    item = Item(time_long=10.5, filename=r".\test_musics\0001.周杰伦-夜曲.mp3")
    # print(item)
    item2 = Item(time_long=10.5, filename=r".\test_musics\0013.周杰伦-暗号.mp3")
    # print(item2)

    playlist = Playlist(name="test_playlist")
    playlist.gen_from_list([item, item2])
    print(playlist)

    playlist.save_to_file("playlist.json")

    playlist.play_one()


if __name__ == "__main__":
    main()
