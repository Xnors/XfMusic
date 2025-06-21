from core import *


def main():
    try:
        playlist = Playlist(name="test_playlist").load_from_file()
    except FileNotFoundError:
        playlist = Playlist(name="test_playlist")

        playlist.gen_from_dir("./test_musics/")
        print(playlist)

        playlist.save_to_file()

    playlist.play_all()
    print(playlist.random_recommend())
    print(playlist.random_recommend())
    print(playlist.random_recommend())


if __name__ == "__main__":
    main()
