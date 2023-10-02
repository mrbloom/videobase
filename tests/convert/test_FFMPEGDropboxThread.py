import os
import unittest
from convert.tools.dropboxvideo import FFMPEGDropboxThread, ConfigDropboxFFmpeg

class TestFFMPEGDropboxThread(unittest.TestCase):

    # It's risky to ask for sensitive data within a test module. This should ideally be an environment variable.
    ACCESS_TOKEN = input("Enter your Dropbox access token:")

    def setUp(self):
        self.config = ConfigDropboxFFmpeg(
            input="D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\dropbox\\12.ts",
            output="D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\dropbox\\12.mp4",
            input_keys={},
            output_keys={'vcodec': 'h264', 'video_bitrate': '1.5M'},
            dropbox_input="/andriyaka/1.ts",
            dropbox_output="",
            access_token=self.ACCESS_TOKEN
        )
        self.thread = FFMPEGDropboxThread(self.config)

    def test_run_fetches_video_from_dropbox(self):
        # Assuming run() function should convert and save the video, let's check for the existence of the output video
        self.thread.run()

        # Checking if the output file exists
        self.assertTrue(os.path.exists(self.config.output))
        # Additional checks can be done depending on the expected outcome of the function

    # Uncomment when you're ready to test additional methods
    # def test_get_duration_from_chunk(self):
    #     with open(self.config.output, 'rb') as file:
    #         data_chunk = file.read(2048)  # Read the first 2KB. Adjust this size if needed.
    #
    #     duration = self.thread.get_duration_from_chunk(data_chunk)
    #     self.assertIsInstance(duration, float)  # Assuming the duration is a float
    #     # Additional checks can be done based on expected duration

    # def test_time_to_seconds(self):
    #     result = self.thread.time_to_seconds("01:02:03.45")
    #     self.assertEqual(result, 3723.45)  # 1 hour, 2 minutes, 3.45 seconds


if __name__ == '__main__':
    unittest.main()
