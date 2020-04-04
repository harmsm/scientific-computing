#!/usr/bin/env python
__description__ = \
"""
Take a video file, chop out the sections identified in a spreadsheet, and
then combine them into a single video.  Uses ffmpeg under the hood.

Spreadsheet should specificy time stamps in HH:MM:SS format. Example:

start,end,gap
00:05:00,00:15:12,00:00:05
00:22:17,01:07:06,00:00:00

This would take the input video and extract between (minute 5 and 0 seconds)
and (minute 15 and 12 seconds), and then between (minute 22 and 17 seconds)
and (hour 1, minute 7, and 6 seconds). These will be combined with a 5 second
black screen between them.  A one second fade is added to the front and end
of each clip by default, so the total video time would go from:

00:04:59 -> 00:15:13
5 seconds of black
00:22:16 -> 01:07:07

The program will also optionally dump out a json file mapping between the
time in the chopped video back to real time.
"""

__author__ = "Michael J. Harms"
__date__ = "2020-04-03"
__usage__ = "./process_video.py video_file spreadsheet_file"

import ffmpeg

import pandas as pd
import numpy as np

import sys, random, string, copy, glob, shutil, os, argparse, json

def _time_to_seconds(time_string):
    """
    Convert a HH:MM:SS-style time-string into seconds (integer).
    """

    error_string = "time '{}' not recognized.  Should have format HH:MM:SS\n".format(time_string)

    # Make sure it's a string
    if type(time_string) is not str:
        raise ValueError(error_string)

    # Make sure it splits into three with ":"
    t_list = time_string.split(":")
    if len(t_list) != 3:
        raise ValueError(error_string)

    # Make sure each bit of the string can be converted to an integer
    try:
        # Make sure each chunk has exactly length = 2
        if sum([len(t) != 2 for t in t_list]) > 0:
            raise ValueError

        # Convert to integer
        t_list = [int(t) for t in t_list]

    except ValueError:
        raise ValueError(error_string)

    # Make sure values are all positive
    if sum([t >= 0 for t in t_list]) != 0:
        raise ValueError(error_string)

    # Return converted time
    return t_list[0]*3600 + t_list[1]*60 + t_list[2]

def _seconds_to_time(seconds):
    """
    Convert seconds into a time-string with the format HH:MM:SS.  Seconds should
    be an integer or float (rounded to nearest second and then cast to int).
    """

    # Represent as integer
    try:
        if not type(seconds) is int:
            seconds = int(round(seconds,0))
    except TypeError:
        err = "seconds must be able to be converted to an integer\n"
        raise ValueError(err)

    # Make sure the it is not too large to represent
    max_value = 99*3600 + 59*60 + 59
    if seconds > max_value:
        err = "times longer than {} (99:59:59) cannot be represented in HH:MM:SS.\n".format(max_value)
        raise ValueError(err)

    # Convert seconds to hours, minutes, seconds
    hours = seconds // 3600
    leftover = seconds - hours*3600
    minutes = leftover // 60
    seconds = leftover - minutes*60

    # Make sure the resulting time is sane.
    try:
        assert seconds >= 0 and seconds < 60
        assert minutes >= 0 and minutes < 60
        assert hours >= 0 and hours < 100
    except AssertionError:
        err = "time could not be converted to HH:MM:SS format.\n"
        err += "gave: {} hours, {} minutes, {} seconds\n".format(hours,minutes,seconds)
        raise RuntimeError(err)

    return "{:02}:{:02}:{:02}".format(hours,minutes,seconds)

def _get_video_properties(input_file):
    """
    Use ffprobe to extract information for video processing from video file.
    """

    # Rip some information from the video for use in arguments later
    ffprobe = ffmpeg.probe(input_file)["streams"]

    # Dictionary of relevant information to return
    out = {}

    # Get max duration as integer
    out['duration'] = int(np.floor(ffprobe[0]['duration']))

    # Audio
    out['audio_codec'] = ffprobe[0]['codec_name']
    out['sample_rate'] = ffprobe[0]['sample_rate']
    out['channel_layout'] = ffprobe[0]['channel_layout']

    # Video
    out['frame_rate'] = ffprobe[1]['avg_frame_rate']
    out['width'] = ffprobe[1]['width']
    out['height'] = ffprobe[1]['height']
    out['video_codec'] = ffprobe[1]['codec_name']
    out['pix_fmt'] = ffprobe[1]['pix_fmt']

    # Construct set of output keyword arguments for ffmpeg that will match input
    # video
    out_kwargs = {"c:v":"{}".format(ffprobe[1]['codec_name']),
                  "c:a":"{}".format(ffprobe[0]['codec_name']),
                  "pix_fmt":ffprobe[1]['pix_fmt'],
                  "r":ffprobe[1]['avg_frame_rate']}

    out['out_kwargs'] = out_kwargs

def _fade_in(input_file,output_file,end_fade,fade_length):
    """
    Make a tiny video encoding a fade from black for a chunk extracted
    from a larger video.

    input_file: input video file.
    output_file: output video file.
    end_fade: time at which to end the fade (as indexed in the input_file)
    fade_length: fade length in seconds
    """

    video_props = _get_video_properties(input_file)

    out_kwargs = video_props["out_kwargs"]
    out_kwargs["filter:v"] = "fade=in:0:{}".format(fade_length*video_props['frame_rate'])

    # Fade length
    start_fade_in_seconds = _time_to_seconds(end_fade) - fade_length
    start_fade = _second_to_time(start_fade_in_seconds)

    (
        ffmpeg
        .input(input_file,**{"ss":start_fade,
                             "to":end_fade})
        .output(output_file,**out_kwargs)
        .run()
    )


def _slice_out(input_file,output_file,start,stop):
    """
    Chop a chunk of video out of a large video, copying the codecs.
    """

    (
        ffmpeg
        .input(input_file,**{"ss":start,"to":stop})
        .output(output_file,**{"c:v":"copy","c:a":"copy"})
        .run()
    )


def _fade_out(input_file,output_file,start_fade,fade_length):
    """
    Make a tiny video encoding a fade to black for a chunk extracted
    from a larger video.

    input_file: input video file.
    output_file: output video file.
    start_fade: time at which to start the fade (as indexed in the input_file)
    fade_length: fade length in seconds
    """

    video_props = _get_video_properties(input_file)

    out_kwargs = video_props["out_kwargs"]
    out_kwargs["filter:v"] = "fade=out:0:{}".format(fade_length*video_props['frame_rate'])

    # Fade length
    end_fade_in_seconds = _time_to_seconds(start_fade) + fade_length
    end_fade = _second_to_time(end_fade_in_seconds)

    (
        ffmpeg
        .input(input_file,**{"ss":start_fade,
                             "to":end_fade})
        .output(output_file,**out_kwargs)
        .run()
    )


def _generate_blank(input_file,output_file,length):
    """
    Generate a clip with black video and silent audio that matches the codecs
    and size of the input_file.

    input_file: input video file.
    output_file: output video file.
    length: length of black frame, in seconds
    """

    video_props = _get_video_properties(input_file)

    out_kwargs = video_props["out_kwargs"]

    # Generate black video
    video = ffmpeg.input("color=c=black:s={}x{}".format(video_props['width'],
                                                        video_props['height']),
                         **{"t":length,"f":"lavfi"})

    # Generate silent audio track
    audio = ffmpeg.input("anullsrc=channel_layout={}:sample_rate={}".format(video_props['channel_layout'],
                                                                            video_props['sample_rate']),
                         **{"t":length,"f":"lavfi"})

    # Combine video and audio
    stream = ffmpeg.concat(video.video,audio.audio,v=1,a=1).node

    # Write output
    out = ffmpeg.output(stream[0],stream[1],output_file,**out_kwargs)
    out.run()


def process_video(video_file,output_file,
                  spreadsheet_file,
                  start_column="start",end_column="end",gap_column=None,
                  fade_length=1,
                  timebase_file=None,real_time="00:00:00"):

    # -------------------------------------------------------------------------
    # Check sanity of input files
    if not os.path.isfile(video_file):
        err = "video_file '{}' does not exist.\n".format(video_file)
        raise FileNotFoundError(err)

    if os.path.isfile(output_file):
        err = "output_file '{}' exists.  Will not overwrite\n".format(output_file)
        raise FileExistsError(err)

    if not os.path.isfile(spreadsheet_file):
        err = "spreadsheet_file '{}' does not exist.\n".format(spreadsheet_file)
        raise FileNotFoundError(err)

    if timebase_file is not None:
        if os.path.isfile(timebase_file):
            err = "timebase_file '{}' exists.  Will not overwrite\n".format(timebase_file)
            raise FileExistsError(err)

    # -------------------------------------------------------------------------
    # Probe the video for its properties (resolution, codec, etc)

    video_props = _get_video_properties(video_file)

    # -------------------------------------------------------------------------
    # Load the spreadsheet

    if spreadsheet_file[-4:] == ".csv":
        df = pd.read_csv(spreadsheet_file)
    elif spreadsheet_file[-4:] in [".xls","xlsx"]:
        df = pd.read_excel(spreadsheet_file)
    else:
        err = "spreadsheet file type not recognized.  Should be excel or csv.\n"
        raise ValueError(err)

    # Get start times of chunks from the spreadsheet
    try:
        starts = np.array(df[start_column])
    except KeyError:
        err = "spreadsheet does not have start_column '{}'\n".format(start_column)
        raise ValueError(err)

    if np.sum(df[start_column].isnull()) > 0:
        err = "start column '{}' has missing values\n".format(start_column)
        raise ValueError(err)

    # Get stop times of chunks from the spreadsheet
    try:
        stops = np.array(df[end_column])
    except KeyError:
        err = "spreadsheet does not have end_column '{}'\n".format(end_column)
        raise ValueError(err)

    if np.sum(df[end_column].isnull()) > 0:
        err = "end column '{}' has missing values\n".format(end_column)
        raise ValueError(err)

    # Get list of gaps after chunks to add.  If not specified, add no gaps
    if gap_column is None:
        gap_after = np.array(["00:00:00" for _ in range(len(ends))])
    else:
        try:
            gap_after = np.array(df[gap_column])
            gap_after[df[gap_column].isnull()] = "00:00:00"
        except KeyError:
            err = "spreadsheet does not have gap_column '{}'\n".format(gap_column)
            raise ValueError(err)

    # -------------------------------------------------------------------------
    # Check time sanity

    for i in range(len(stops)):
        stop_value = _time_to_seconds(stops[i])
        start_value = _time_to_seconds(starts[i])

        if stop_value < start_value:
            err = "stop time '{}' before start time '{}'\n".format(stops[i],start[i])
            raise ValueError(err)

        if stop_value > video_props["duration"]:
            longest_allowed = _second_to_time(video_props["duration"])
            err = "stop time '{}' is longer than the video ({})".format(stops[i],
                                                                        longest_allowed)
            raise ValueError(err)

    # -------------------------------------------------------------------------
    # Prep variables for main procesing loop

    # Create unique file prefix for temporary files
    file_prefix = "tmp_{}".format("".join([random.choice(string.ascii_letters)
                                           for _ in range(8)]))

    # Information for keeping track of timebase
    real_time_offset_in_seconds = _time_to_seconds(real_time)

    real_time_starts = []
    real_time_stops = []
    video_time_starts = []
    video_time_stops = []

    # Now go through each chunk to chop out
    file_list = []
    for i in range(len(starts)):

        # ---------------------------------------------------------------------
        # Account for fades in start and stop times

        # Convert time-string to seconds for start and stop
        start_time_in_seconds = _time_to_seconds(starts[i])
        stop_time_in_seconds = _time_to_seconds(stops[i])

        # Make sure the start and stop have room for fading in and out
        if (start_time_in_seconds - fade_length) < 0:
            start_time_in_seconds = 0 + fade_length
        if stop_time_in_seconds + fade_length > video_props["duration"]:
            stop_time_in_seconds = video_props["duration"] - fade_length

        # Start and stop times, accounting for fades
        start = _second_to_time(start_time_in_seconds)
        stop  = _second_to_time(stop_time_in_seconds)

        # ---------------------------------------------------------------------
        # Build conversion data for timebase file

        # Keep track of real start time and end time (in seconds)
        real_start_time = start_time_in_seconds - fade_length + real_time_offset_in_seconds
        real_end_time = end_time_in_seconds + fade_length + real_time_offset_in_seconds

        # Keep track of video start and end time (in seconds)
        chunk_duration = real_end_time - real_start_time
        if i == 0:
            # If first chunk, start at 0
            video_start_time = 0
        else:
            # If there are previous chunks, start at prev_end + 1
            video_start_time = video_time_list[-1][1] + 1
        video_end_time = video_start_time + chunk_duration

        # Record real and video time start and stop for this chunk
        real_time_starts.append(real_start_time)
        real_time_stops.append(real_end_time))
        video_time_starts.append(video_start_time)
        video_time_stops.append(video_end_time)

        # Map the gap between this chunk and the next
        if i < (len(starts) - 1):
            # If we aren't at the last chunk, grab the next start for the gap
            next_start_in_seconds = _time_to_seconds(starts[i+1])
        else:
            # If at the last chunk, grab the total video duration as the gap
            next_start_in_seconds = video_props["duration"]

        # Now append real and video time components of the gap between the
        # chunks
        real_time_starts.append(real_end_time + 1)
        real_time_stops.append(next_start_in_seconds - 1)
        video_time_starts.append(video_end_time + 1)
        video_time_stops.append(video_end_time + _time_to_seconds(gaps[i]))

        # ---------------------------------------------------------------------
        # Construct temporary video files for this chunk

        # Create initial fade in (start - fade_length) -> start
        fade_in_file = "{}_{:03}_fade-in.mp4".format(file_prefix,i)
        _fade_in(video_file,fade_in_file,start,fade_length)
        file_list.append(fade_in_file)

        # Chop out video chunk from start -> stop
        chunk_out_file = "{}_{:03}.mp4".format(file_prefix,i)
        _slice_out(video_file,chunk_out_file,start,stop)
        file_list.append(chunk_out_file)

        # Generate fade out (stop -> stop + fade_length)
        fade_out_file = "{}_{:03}_fade-out.mp4".format(file_prefix,i)
        _fade_out(video_file,fade_out_file,stop,fade_length)
        file_list.append(fade_out_file)

        # Generate a black screen for gap_after if requested
        if gap_after[i] != "00:00:00":
            gap_out_file = "{}_{:03}_gap.mp4".format(file_prefix,i)
            _generate_blank(video_file,gap_out_file,gap_after[i])
            file_list.append(gap_out_file)


    # Combine all streams
    inputs = []
    streams = []
    for f in file_list:
        inputs.append(ffmpeg.input(f))
        streams.append(inputs[-1].video)
        streams.append(inputs[-1].audio)

    joined = ffmpeg.concat(*streams,v=1,a=1).node

    # Render final movie.
    out = ffmpeg.output(joined[0],joined[1],"{}_final.mp4".format(file_prefix),**out_kwargs)
    out.run()

    # Copy final file to output file name and nuke temporary files
    to_remove = glob.glob("{}*".format(file_prefix))
    shutil.copy("{}_final.mp4".format(file_prefix),"output.mp4")
    for f in to_remove:
        os.remove(f)

    # Write out timebase_file, if requested.
    if timebase_file is not None:

        out_dict = {}
        out_dict["real_start"] = [_second_to_time(t) for t in real_time_starts]
        out_dict["real_stop"] = [_second_to_time(t) for t in real_time_stops]
        out_dict["video_start"] = [_second_to_time(t) for t in video_time_starts]
        out_dict["video_stop"] = [_second_to_time(t) for t in video_time_stops]

        pd.to_csv(timebase_file)


class _NonDefaultAction(argparse.Action):
    """
    Subclass of argparse.Action that reports whether a non-default value of the
    argument was used.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest+'_nondefault', True)

def main(argv=None):
    """
    Parse command line arguments and invoke process_video function.
    """

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__description__,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('video_file',type=str,nargs=1,
                        help='video file to process')

    # Spreadsheet arguments
    parser.add_argument('spreadsheet',type=str,nargs=1,
                        help='spreadsheet containing time stamps for chopping video')
    parser.add_argument('--start-column','-s',dest="start_column",
                        type=str,default="start",nargs=1,
                        help="column in spreadsheet with chunk start time stamps",
                        action=_NonDefaultAction)
    parser.add_argument('--end-column','-e',dest="end_column",
                        type=str,default="end",nargs=1,
                        help="column in spreadsheet with chunk end time stamps",
                        action=_NonDefaultAction)
    parser.add_argument('--gap-column','-g',dest="gap_column",
                        type=str,default=None,nargs=1,
                        help="column in spreadsheet with gaps to add after chunks (optional)",
                        action=_NonDefaultAction)

    # Output and video arguments
    parser.add_argument('--out-file','-o',dest="out_file",
                        type=str,nargs=1,default="{video_file}.processed.mp4",
                        help="name out output file (filetype determined by extension)",
                        action=_NonDefaultAction)
    parser.add_argument('--fade-length','-f',dest="fade_length",
                        type=int,nargs=1,default=1,
                        help="fade length for transitions, in seconds")

    # Timebase arguments
    parser.add_argument('--timebase-file','-t',dest="timebase_file",
                        type=str,nargs=1,default=None,
                        help="file in which to store json mapping chopped time to real time.")
    parser.add_argument("--real-fime","-r",dest="real_time",
                        type=str,nargs=1,default="00:00:00",
                        help="real start time of first video chunk as HH:MM:SS string")


    args = parser.parse_args(argv)

    video_file = args.video_file[0]
    spreadsheet = args.spreadsheet[0]

    # Grab start_column
    if hasattr(args,"start_column_nondefault"):
        start_column = args.start_column[0]
    else:
        start_column = args.start_column

    # Grab end_column
    if hasattr(args,"end_column_nondefault"):
        end_column = args.end_column[0]
    else:
        end_column = args.end_column

    # Grab gap_column
    if hasattr(args,"gap_column_nondefault"):
        gap_column = args.gap_column[0]
    else:
        gap_column = args.gap_column

    # Grab out_file
    if hasattr(args,"out_file_nondefault"):
        out_file = args.out_file[0]
    else:
        out_file = "{}.processed.mp4".format(video_file)

    # get fade_length
    fade_length = args.fade_length

    # Grab out_file
    if hasattr(args,"timebase_file_nondefault"):
        timebase_file = args.timebase_file[0]
    else:
        timebase_file = args.timebase_file

    # Grab out_file
    if hasattr(args,"real_time_file_nondefault"):
        real_time = args.real_time[0]
    else:
        real_time = args.real_time

    # Process the video
    process_video(video_file,output_file,
                  spreadsheet_file,
                  start_column,end_column,gap_column,
                  fade_length,
                  timebase_file,real_time)

# If called from the command line.
if __name__ == "__main__":
    main()
