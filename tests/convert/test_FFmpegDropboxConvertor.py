import unittest
import os
import shutil
from convert.tools.video import FFMPEGDropboxConverter

class TestFFmpegDropboxConverter(unittest.TestCase):
    ACCESS_TOKEN=input("ACCESS_TOKEN :")
    def setUp(self):
        # Setting up directories
        self.input_folder = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\in"
        self.output_folder = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\out"
        os.makedirs(self.input_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        self.dropbox_input = "/andriyaka"


        # You need to have some test video files; for simplicity, let's assume you have two dummy videos.
        # shutil.copy2('test_video1.mp4', self.input_folder)
        # shutil.copy2('test_video2.mp4', self.input_folder)

    def test_conversion_with_two_threads(self):
        converter = FFMPEGDropboxConverter(
                                    self.dropbox_input,
                                    "",
                                    self.ACCESS_TOKEN,
                                    ffmpeg_path="D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\bin",
                                    num_threads=2,
                                    start_delay=1,
                                    input_folder=self.output_folder,
                                    output_folder=self.output_folder,
                                    file_mask="*.ts")
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
