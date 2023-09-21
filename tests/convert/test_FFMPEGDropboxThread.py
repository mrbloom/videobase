import unittest
from convert.tools.video  import FFMPEGDropboxThread, ConfigDropboxFFmpeg  # Ensure you import from the correct location.

class TestFFMPEGDropboxThread(unittest.TestCase):
    ACCESS_TOKEN = input("Enter your_real_dropbox_access_token :")

    def setUp(self):
        self.config = ConfigDropboxFFmpeg(
            "/andriyaka/2.ts",
            "",
            self.ACCESS_TOKEN,
            "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\dropbox\\2.ts",
            "D:\\docs\\dest\\1p1media\\soft\\videobase\\tests\\video_test\\dropbox\\2.mp4",
            {},
            {'vcodec': 'h264', 'video_bitrate': '1.5M'}
        )
        self.thread = FFMPEGDropboxThread(self.config)

    def test_run_fetches_video_from_dropbox(self):
        # Just running the actual function.
        # Ensure you check the output_video_path after this test to verify if the conversion was successful.
        self.thread.run()

    # def test_get_duration_from_chunk(self):
    #     # Use a small chunk of your video data, maybe the first few KBs or MBs.
    #     with open(self.output_video_path, 'rb') as file:
    #         data_chunk = file.read(2048)  # Reading the first 2KB. Adjust this size if needed.
    #
    #     duration = self.thread.get_duration_from_chunk(data_chunk)
    #     print(duration)
    #     # Ensure the printed duration is correct or make further assertions.

    # def test_time_to_seconds(self):
    #     # Test to ensure the function works as expected. This doesn't directly involve Dropbox.
    #     result = self.thread.time_to_seconds("01:02:03.45")
    #     self.assertEqual(result, 3723.45)  # 1 hour, 2 minutes, 3.45 seconds


if __name__ == '__main__':
    unittest.main()
