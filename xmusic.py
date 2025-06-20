from core import *


def main():
    item = Item(name="test", time_long=10.5)
    # print(item)
    item2 = Item(name="testt", time_long=10.5)
    # print(item2)

    playlist = Playlist(name="test_playlist")
    playlist.gen_from_list([item, item2])
    print(playlist)

    playlist.save_to_file("playlist.json")


if __name__ == "__main__":
    main()
