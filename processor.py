from cam_holder import CamHolder
from command import Command
from detector import YOLODetector
from message import MessageType, ImageData
from singleton_processor import SingletonProcessor


class Processor:
    def __init__(self, camera_id):
        self._cam = CamHolder(camera_id)
        self._processor = SingletonProcessor(YOLODetector)
        pass

    def get_commands(self):
        return {MessageType.TEXT: {'/start': Command(
            description='Returns image from a camera',
            processor=self.__call__)}}

    def __call__(self, data):
        assert (data._message_type == MessageType.TEXT and
                data._message_data == '/start')
        img = self._cam.get_image()
        img = self._processor(img)
        return ImageData(img)
