import struct
import sys

def get_bytes(byte:str, mode:str) -> str:
    if (sys.byteorder == "little" and mode == "big") or (sys.byteorder == "big" and "mode" == "little"):
        return byte[::-1]
    else:
        return byte

def header_parser(header:str) -> dict:
    """
    header format
    #<SensorType>:str <numberOfFrame>:int <numberOfValuesPerFrame>:int <Big Endian/Little Endian>:"big/little"
    """
    info = header.decode("utf-8").rstrip('\n').lstrip('#').split(' ')
    return {"sensor_type":info[0],
            "num_of_frame":info[1],
            "num_of_value":info[2],
            "endian":info[3]}

def read(file_path:str):
    with open(file_path, "rb") as f:
        header_line = f.readline()
        header = header_parser(header_line)
        num_of_value = int(header.get("num_of_value", '0'))
        num_of_frame = int(header.get("num_of_frame", '0'))
        endian = header.get("endian", "big")
        while True:
            # read time stamp
            content = f.read((num_of_value+1)*8)
            if len(content) != (num_of_value+1)*8:
                print("IMU Read Complete!")
                break
            byte = get_bytes(content[:8], endian)
            time_stamp = struct.unpack('Q', byte)[0]
            vals = []
            for i in range(num_of_value):
                # byte = get_bytes(f.read(8), "big")
                byte = get_bytes(content[8*(1+i):8*(2+i)], endian)
                vals.append(struct.unpack('d', byte)[0])
            # import pdb; pdb.set_trace()
            print("time:{} data:{}".format(time_stamp, " ".join([str(val) for val in vals])))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process imu byte data.')
    parser.add_argument('file_path', type=str, 
                    help='path to the imu file')

    args = parser.parse_args()
    read(args.file_path)
