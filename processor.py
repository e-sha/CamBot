from cvbot.utils.cam_holder import CamHolder
from cvbot.utils.command import Command
from cvbot.utils.message import MessageType, ImageData, VideoData
from cvbot.utils.singleton_processor import SingletonProcessor
from detector import YOLODetector


class Processor:
    def __init__(self, camera_id):
        self._cam = CamHolder(camera_id)
        self._processor = SingletonProcessor(YOLODetector)
        pass

    def get_commands(self):
        return {MessageType.TEXT: {'/start': Command(
            description='Returns image from a camera',
            processor=self.__call__),
                                   '/video': Command(
            description='Returns video',
            processor=self.__call__)},
                MessageType.IMAGE: {'': Command(
            description='Finds objects on an image',
            processor=self._process_image)}}

    def __call__(self, data):
        if (data._message_type == MessageType.TEXT and
                data._message_data == '/video'):
            from pathlib import Path
            video_path = Path(__file__).parent.resolve()/'data'/'test.mp4'
            import io
            buf = io.BytesIO()
            buf.write(video_path.read_bytes())
            buf.seek(0)
            return VideoData(buf)
        assert (data._message_type == MessageType.TEXT and
                data._message_data == '/start')
        img = self._cam.get_image()
        img = self._processor(img)
        return ImageData(img)

    def _process_image(self, data):
        assert data._message_type == MessageType.IMAGE
        img = self._processor(data._message_data)
        return ImageData(img)
