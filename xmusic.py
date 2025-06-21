from core import *


def main():
    playlist = Playlist(name="test_playlist").load_from_file()
    playlist.gen_from_dir("./test_musics/test")
    print(playlist)

    playlist.save_to_file()

    playlist.play_all()


if __name__ == "__main__":
    main()
