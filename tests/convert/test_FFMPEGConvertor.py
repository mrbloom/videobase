import unittest
import os
import shutil
from convert.tools.localvideo import FFMPEGConverter, ConfigFFMPEGConverter

class TestFFMPEGConverter(unittest.TestCase):

    def setUp(self):
        # Setting up directories
        self.input_folder = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\in"
        self.output_folder = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\out"
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)

        self.config = ConfigFFMPEGConverter(
            ffmpeg_path = "D:\\input_folder\\ffmpeg\\bin",
            num_threads = 2,
            start_delay = 1,
            input_folder = self.input_folder,
            output_folder = self.output_folder,
            file_mask = "*.ts",
            video_codec = "h264",
            video_bitrate = "1.5M",
            output_ext = "mp4"
        )

        # You need to have some test video files; for simplicity, let's assume you have two dummy videos.
        # shutil.copy2('test_video1.mp4', self.input_folder)
        # shutil.copy2('test_video2.mp4', self.input_folder)

    def test_conversion_with_two_threads(self):
        converter = FFMPEGConverter(self.config)
        converter.convert()

        # Assuming you had 2 video files in the input directory
        #self.assertEqual(len(os.listdir(self.output_folder)), 2)

        # Add more assertions as needed, e.g., checking file properties, etc.

    def tearDown(self):
        # Cleaning up
        pass
        # shutil.rmtree(self.input_folder)
        # shutil.rmtree(self.output_folder)


if __name__ == "__main__":
    unittest.main()
