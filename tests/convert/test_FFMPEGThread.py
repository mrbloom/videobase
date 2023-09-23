import unittest
import os

from convert.tools.localvideo import FFmpegThread, ConfigFFmpeg


class TestFFMPEGThread(unittest.TestCase):

    def setUp(self):
        # This method runs before each test
        # Here, you can set up any required resources
        sample_video_path = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\in\\1.ts"
        output_video_path = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\out\\1.mp4"
        input_keys = {}
        output_keys = {'vcodec': 'h264', 'video_bitrate': '1.5M'}

        self.config = ConfigFFmpeg(sample_video_path, output_video_path,input_keys,output_keys)
    def tearDown(self):
        # This method runs after each test
        # Here, you can release or remove any resources used in tests
        if os.path.exists(self.config.output):
            os.remove(self.config.output)

    def test_ffmpeg_thread_conversion(self):
        # Test if FFMPEGThread can convert a video without errors
        thread = FFmpegThread(self.config)
        thread.start()
        thread.join()  # Wait for the thread to finish

        # Check if the output file exists after conversion
        self.assertTrue(os.path.exists(self.config.output))

if __name__ == '__main__':
    # TestFFMPEGThread.test_ffmpeg_thread_conversion()
    unittest.main()
