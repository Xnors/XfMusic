from core import *
import cProfile
import os


def main():
    try:
        playlist = Playlist(name="test_playlist2").load_from_file()
        playlist.play_all()
    except FileNotFoundError:
        playlist = Playlist(name="test_playlist2")

        playlist.gen_from_dir("./test_musics/test")
        print(playlist)

        playlist.save_to_file()
        playlist.play_all()
    except IndexError:
        mylogger.warning("播放列表为空")
        os.remove(Playlist(name="test_playlist2").save_path)
        playlist = Playlist(name="test_playlist2").gen_from_dir("./test_musics/test").save_to_file()
        playlist.play_all()

    
    # print(playlist.random_recommend())
    # print(playlist.random_recommend())
    # print(playlist.random_recommend())
    # Item("./test_musics/0001.周杰伦-夜曲.mp3").play()


if __name__ == "__main__":
    # cProfile.run("main()",sort="tottime")
    main()
