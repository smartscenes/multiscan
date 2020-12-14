### Sensors

#### sensorReader
usage `(base) BowendeMacBook-Pro:multiscan bowenchen$ python scripts/sensors/sensorReader.py ../data/test.rot --cmp ../data/test.rot_raw --report report.txt`
```bash
usage: sensorReader.py [-h] [--verbose] [--cmp CMP] [--report REPORT]
                       file_path

Process imu byte data.

positional arguments:
  file_path        path to the ply file

optional arguments:
  -h, --help       show this help message and exit
  --verbose        print file content line by line
  --cmp CMP        ply file to compare against
  --report REPORT  redict report information
```
