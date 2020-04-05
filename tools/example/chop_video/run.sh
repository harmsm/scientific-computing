# Chop up test video, writing a timebase file.  First clip starts at 9:00 am.

python ../../chop_video.py test.mp4 test-extract.csv --timebase-file timebase.csv --real-time 00:09:00
