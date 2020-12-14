import functions.utils as utils
import config.setting_pb2 as pb
from google.protobuf import text_format


def config_from_string(string):
    config = Configure()
    config.parse(string)
    return config


class Configure:
    def __init__(self, setting=None):
        if setting is None:
            self.setting = pb.Setting()
        else:
            self.setting = setting

    def serialize(self):
        """serialize setting to string

        :return: None
        """
        return self.setting.SerializeToString()

    def parse(self, string):
        """parse setting from string

        :param string: serialized setting string
        :return: None
        """
        self.setting.ParseFromString(string)

    def load(self, path, debug=False):
        """load configuration from protobuf file

        :param path: path to protobuf file
        :param debug: if debug input txt file is human readable, otherwise not
        :return: None
        """
        try:
            if utils.file_exist(path):
                if debug:
                    f = open(path, 'r')
                    text_format.Parse(f.read(), self.setting)
                    f.close()
                else:
                    f = open(path, "rb")
                    self.setting.ParseFromString(f.read())
                    f.close()
            else:
                raise IOError('Could not open file {}'.format(path))
        except OSError as e:
            utils.print_e(e)

    def export(self, path, debug=False):
        """export configuration to text file

        :param path: path to text file
        :param debug: if debug output txt file is human readable, otherwise not
        :return: None
        """
        if not utils.file_exist(path):
            utils.print_w('File {} not exist, created a new one'.format(path))
        if debug:
            f = open(path, 'w+')
            f.write(text_format.MessageToString(self.setting))
            f.close()
        else:
            f = open(path, "wb")
            f.write(self.setting.SerializeToString())
            f.close()
