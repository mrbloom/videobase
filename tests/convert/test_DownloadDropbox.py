import unittest
import os
import shutil
from convert.tools.dropboxvideo import DropboxDownload

class TestDropboxDownload(unittest.TestCase):

    def setUp(self):
        # Setting up directories
        self.download_folder = "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\in"
        os.makedirs(self.download_folder, exist_ok=True)



            ffmpeg_path="D:\\input_folder\\ffmpeg\\bin",
            n
            input_folder=self.input_folder,
            output_folder=self.output_folder,
            file_mask="*.ts",
            video_codec="h264",
            video_bitrate="1.5M",
            output_ext="mp4"
        )

        # You need to have some test video files; for simplicity, let's assume you have two dummy videos.
        # shutil.copy2('test_video1.mp4', self.input_folder)
        # shutil.copy2('test_video2.mp4', self.input_folder)

    def test_conversion_with_two_threads(self):
        converter = DropboxDownload(self.config)
        converter.convert()

        # Assuming you had 2 video files in the input directory
        # self.assertEqual(len(os.listdir(self.output_folder)), 2)

        # Add more assertions as needed, e.g., checking file properties, etc.

    def tearDown(self):
        # Cleaning up
        pass
        # shutil.rmtree(self.input_folder)
        # shutil.rmtree(self.output_folder)


if __name__ == "__main__":
    unittest.main()
