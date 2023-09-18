import unittest
import os
import progressbar
import threading
import ffmpeg

class TestFFMPEGThread(unittest.TestCase):

    def setUp(self):
        # This method runs before each test
        # Here, you can set up any required resources
        self.sample_video_path = 'sample_video.mp4'  # Adjust path as needed
        self.output_video_path = 'test_output.mp4'

    def tearDown(self):
        # This method runs after each test
        # Here, you can release or remove any resources used in tests
        if os.path.exists(self.output_video_path):
            os.remove(self.output_video_path)

    def test_ffmpeg_thread_conversion(self):
        # Test if FFMPEGThread can convert a video without errors
        thread = FFmpegThread(self.sample_video_path, self.output_video_path,
                              output_keys={'vcodec': 'h264', 'video_bitrate': '1.5M'})
        thread.start()
        thread.join()  # Wait for the thread to finish

        # Check if the output file exists after conversion
        self.assertTrue(os.path.exists(self.output_video_path))

if __name__ == '__main__':
    unittest.main()
