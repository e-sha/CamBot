import cv2
import io
from pathlib import Path
import tempfile

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
                MessageType.IMAGE: Command(
            description='Finds objects on an image',
            processor=self._process_image),
                MessageType.VIDEO: Command(
            description='Finds objects in a video',
            processor=self._process_video)}

    def __call__(self, data):
        if (data.type == MessageType.TEXT and
                data.data == '/video'):
            video_path = Path(__file__).parent.resolve()/'data'/'test.mp4'
            buf = io.BytesIO()
            buf.write(video_path.read_bytes())
            buf.seek(0)
            return VideoData(buf)
        assert (data.type == MessageType.TEXT and
                data.data == '/start')
        img = self._cam.get_image()
        img = self._processor(img)
        return ImageData(img)

    def _process_image(self, data):
        assert data.type == MessageType.IMAGE
        img = self._processor(data.data)
        return ImageData(img)

    def _process_video(self, data):
        assert data.type == MessageType.VIDEO
        with tempfile.NamedTemporaryFile() as in_tmp_file, \
             tempfile.NamedTemporaryFile(suffix='.mkv') as out_tmp_file:
            in_tmp_file.write(data.data)
            input_video = cv2.VideoCapture(in_tmp_file.name)

            width = int(input_video.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(input_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(input_video.get(cv2.CAP_PROP_FPS))
            #fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            output_video = cv2.VideoWriter(out_tmp_file.name,
                                           fourcc,
                                           fps,
                                           (width, height))
            while True:
                is_fine, image = input_video.read()
                if not is_fine:
                    break
                output_video.write(self._processor(image))

            input_video.release()
            output_video.release()

            buf = io.BytesIO()
            buf.write(Path(out_tmp_file.name).read_bytes())
        return VideoData(buf)
