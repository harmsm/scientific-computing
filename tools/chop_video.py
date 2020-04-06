#!/usr/bin/env python
__description__ = \
"""
Take a video file, extract the sections identified in a spreadsheet, and
then combine them into a single video.  Fades to black between clips.

Spreadsheet should specify the time stamps in HH:MM:SS format. Example:

start,stop,gap
00:05:00,00:15:12,00:00:05
00:22:17,01:07:06,00:00:00

This would take the input video and extract two chunks:

    from 00:05:00 (5 min) to 00:15:12 (15 min, 12 sec)
    from 00:22:17 (22 min, 17 sec) to 01:07:06 (1 hr, 7 min, 6 sec)

and then combine them.  The program will optionally look at the 'gap' column
to find the length of gaps to insert between clips.  In this case, it would
add a 5 second gap (black screen) between the clips but no gap after.

The codecs and resolution of the input video file should be (largely)
preserved.  This implementation assumes there is both an audio and a video
stream in the video file.  It uses ffmpeg under the hood.

The program will also optionally dump out a csv file mapping between the
time in the chopped video and real time.
"""

__author__ = "Michael J. Harms"
__date__ = "2020-04-03"

import ffmpeg

import pandas as pd
import numpy as np

import sys, random, string, copy, glob, shutil, os, argparse, datetime

def _time_to_seconds(time_string):
    """
    Convert a HH:MM:SS-style time-string into seconds (integer).
    """

    error_string = "time '{}' not recognized.  Should have format HH:MM:SS\n".format(time_string)

    # Make sure it's a string (should catch strings or numpy strings)
    if not isinstance(time_string,str):

        # If pandas interpreted as a datetime object, turn into a string
        if isinstance(time_string,datetime.time):
            time_string = str(time_string)
        else:
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
    if sum([t < 0 for t in t_list]) != 0:
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
    Note that it only looks at the first audio and first video streams.
    """

    # Rip some information from the video for use in arguments later
    ffprobe = ffmpeg.probe(input_file)["streams"]

    # Find indexes for audio and video streams
    video_index = None
    audio_index = None
    for i in range(len(ffprobe)):
        if video_index is None and ffprobe[i]['codec_type'] == "video":
            video_index = i
        elif audio_index is None and ffprobe[i]['codec_type'] == "audio":
            audio_index = i
        else:
            continue

        if video_index is not None and audio_index is not None:
            break

    if video_index is None:
        err = "{} does not contain a video stream\n".format(input_file)
        raise ValueError(err)

    if audio_index is None:
        err = "{} does not contain an audio stream\n".format(input_file)
        raise ValueError(err)

    # Dictionary of relevant information to return
    out = {}

    if audio_index > video_index:
        out["audio_first"] = False
    else:
        out["audio_first"] = True

    # Get max duration as integer
    out['duration'] = int(np.floor(float(ffprobe[audio_index]['duration'])))

    # Audio
    out['audio_codec'] = ffprobe[audio_index]['codec_name']
    out['sample_rate'] = ffprobe[audio_index]['sample_rate']
    out['channel_layout'] = ffprobe[audio_index]['channel_layout']

    # Video
    out['frame_rate'] = ffprobe[video_index]['avg_frame_rate']
    out['width'] = ffprobe[video_index]['width']
    out['height'] = ffprobe[video_index]['height']
    out['video_codec'] = ffprobe[video_index]['codec_name']
    out['pix_fmt'] = ffprobe[video_index]['pix_fmt']

    # Construct set of output keyword arguments for ffmpeg that will match input
    # video
    out_kwargs = {"c:v":"{}".format(out['video_codec']),
                  "c:a":"{}".format(out['audio_codec']),
                  "pix_fmt":out['pix_fmt'],
                  "r":out['frame_rate']}

    out['out_kwargs'] = out_kwargs

    return out

def _fade_in(input_file,output_file,stop_fade,fade_length):
    """
    Make a tiny video encoding a fade from black for a chunk extracted
    from a larger video.

    input_file: input video file.
    output_file: output video file.
    stop_fade: time at which to stop the fade (as indexed in the input_file)
    fade_length: fade length in seconds
    """

    video_props = _get_video_properties(input_file)

    out_kwargs = video_props["out_kwargs"]
    out_kwargs["filter:v"] = "fade=in:0:{}".format(fade_length*video_props['frame_rate'])

    # Fade length
    start_fade_sec = _time_to_seconds(stop_fade) - fade_length
    start_fade = _seconds_to_time(start_fade_sec)

    (
        ffmpeg
        .input(input_file,**{"ss":start_fade,
                             "to":stop_fade})
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
    stop_fade_sec = _time_to_seconds(start_fade) + fade_length
    stop_fade = _seconds_to_time(stop_fade_sec)

    (
        ffmpeg
        .input(input_file,**{"ss":start_fade,
                             "to":stop_fade})
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
    if video_props["audio_first"]:
        stream = ffmpeg.concat(video.video,audio.audio,a=1,v=1).node
    else:
        stream = ffmpeg.concat(video.audio,audio.video,v=1,a=1).node

    # Write output
    out = ffmpeg.output(stream[0],stream[1],output_file,**out_kwargs)
    out.run()


def _load_time_column(df,column_name=None,allow_missing=False):
    """
    Load a column of HH:MM:SS type values from a data frame.

    df: dataframe with column
    column_name: name of column.  if None, return a set of 00:00:00 of the
                 proper length
    allow_missing: whether or not to allow missing values.  if True, set
                   missing values to 00:00:00
    """

    # Get time values from spreadsheets
    try:

        values = np.array(df[column_name],dtype=np.str)

        # Deal with missing values. Either replace with 00:00:00 or throw error
        if allow_missing:
            values[df[column_name].isnull()] = "00:00:00"
        else:
            if np.sum(df[column_name].isnull()) > 0:
                err = "column '{}' has missing values\n".format(column_name)
                raise ValueError(err)

    except KeyError:
        if column_name is None:
            num_values = len(df.iloc[:,0])
            values = np.array(["00:00:00" for _ in range(num_values)])
        else:
            err = "spreadsheet does not have column '{}'\n".format(column_name)
            raise ValueError(err)

    # Check sanity of times.  This will throw an error if they have the incorrect
    # format.
    for v in values:
        _ = _time_to_seconds(v)

    return values


def process_video(video_file,output_file,
                  spreadsheet_file,
                  start_column="start",stop_column="stop",gap_column=None,
                  fade_length=1,
                  timebase_file=None,real_time="00:00:00",
                  force=False):
    """
    Take a video file, extract the sections identified in a spreadsheet, and
    then combine them into a single video.  Fades to black between clips.
    Optionally dump out a csv file mapping between the time in the chopped video
    and real time.

    video_file: video file to process
    output_file: output video file name
    spreadsheet file: spreadsheet encoding chunks to extract
    start_column: column in spreadsheet with chunk starts
    stop_column: column in spreadsheet with chunk stops
    gap_column: column in spreadsheet with gaps (if None, do not use)
    fade_length: length of fades in seconds
    timebase_file: file to write out map between video and real time. if None
                   do not write out the file
    real_time: real time in HH:MM:SS format corresponding to 00:00:00 in output
               video. only used in timebase_file.
    force: wipe out existing output files (default is False)
    """

    # -------------------------------------------------------------------------
    # Check sanity of input files
    if not os.path.isfile(video_file):
        err = "video_file '{}' does not exist.\n".format(video_file)
        raise FileNotFoundError(err)

    if os.path.isfile(output_file) and not force:
        err = "output_file '{}' exists. Stopping. Use --force to overwrite.\n".format(output_file)
        raise FileExistsError(err)

    if not os.path.isfile(spreadsheet_file):
        err = "spreadsheet_file '{}' does not exist.\n".format(spreadsheet_file)
        raise FileNotFoundError(err)

    if timebase_file is not None and not force:
        if os.path.isfile(timebase_file):
            err = "timebase_file '{}' exists. Stopping. Use --force to overwrite.\n".format(timebase_file)
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

    # Get times of chunks from the spreadsheet
    starts = _load_time_column(df,start_column,allow_missing=False)
    stops = _load_time_column(df,stop_column,allow_missing=False)
    gap_after = _load_time_column(df,gap_column,allow_missing=True)

    # Check time sanity
    for i in range(len(stops)):
        stop_value = _time_to_seconds(stops[i])
        start_value = _time_to_seconds(starts[i])

        if stop_value <= start_value:
            err = "stop time '{}' before or identical to start time '{}'\n".format(stops[i],starts[i])
            raise ValueError(err)

        if stop_value > video_props["duration"]:
            longest_allowed = _seconds_to_time(video_props["duration"])
            err = "stop time '{}' is longer than the video ({})".format(stops[i],
                                                                        longest_allowed)
            raise ValueError(err)

    # -------------------------------------------------------------------------
    # Prep variables for main procesing loop

    # Create unique file prefix for temporary files
    file_prefix = "tmp_{}".format("".join([random.choice(string.ascii_letters)
                                           for _ in range(8)]))

    section_type = []
    real_starts_sec = []
    real_stops_sec = []
    output_starts_sec = []
    output_stops_sec = []

    real_time_sec = _time_to_seconds(real_time)

    # Now go through each chunk to chop out and construct timebase and video
    # chunks

    # There are *three* sets of times that we have to keep track of to build
    # a map between the final video time and real time.
    # 1) SOURCE time.  This is the time index of the original source file
    # 2) OUTPUT time.  This is the time index in the final output video
    # 3) REAL time.  This is the real time.  It is related to the SOURCE time
    #    by a simple offset.  Because we chop out chunks to make OUTPUT time,
    #    it is not simply related to OUTPUT time...
    #
    # Below, I denote variables as {start|stop}_{source|output|real}_{sec|string}
    # The last field indicates whether the variable is a HH:MM:SS string or an
    # integer of seconds.
    #
    # Final note on indexing.  I chop up chunks as fade-in + chunk and then
    # fade-in + gap.  Everything has 1 second resolution.
    # |fadein0chunk0|fadeout0gap0|fadein1chunk1|fadeout1gap1|...
    #  ^           ^ ^
    #  1           2 3
    # 1: 0
    # 2: t
    # 3: t+1
    # ...

    file_list = []
    for i in range(len(starts)):

        # ---------------------------------------------------------------------
        # Build conversion data for timebase file
        # ---------------------------------------------------------------------

        # ---------------- Source time ------------------

        # Chunk start and stop SOURCE times in seconds
        start_source_sec = _time_to_seconds(starts[i])
        stop_source_sec = _time_to_seconds(stops[i])

        # Make sure the start and stop have room for fading in and out
        if (start_source_sec - fade_length) < 0:
            start_source_sec = 0 + fade_length
        if stop_source_sec + fade_length > video_props["duration"]:
            stop_source_sec = video_props["duration"] - fade_length

        # Start and stop SOURCE times as strings
        start_source_string = _seconds_to_time(start_source_sec)
        stop_source_string  = _seconds_to_time(stop_source_sec)

        # How long is the chunk (includes *one* of the fades)
        chunk_duration = stop_source_sec - start_source_sec + fade_length

        # The first start corresponds to the specified real time. The first
        # time through the loop, calculate the appropriate offset.
        if i == 0:
            real_time_offset = real_time_sec - (start_source_sec - fade_length)

        # ----------------------------------------------------------------------
        # Work on main chunk:
        # |fadein0chunk0|fadeout0gap0|
        #  *************  <- indexes for fade-in through chunk
        # ----------------------------------------------------------------------

        section_type.append("content")

        # ---------------- Output time ------------------

        # If this is the first chunk, output start time is zero.  If not, the
        # output start time is the previous output stop + 1.
        if i == 0:
            start_output_sec = 0
        else:
            start_output_sec = output_stops_sec[-1] + 1

        stop_output_sec = start_output_sec + chunk_duration

        output_starts_sec.append(start_output_sec)
        output_stops_sec.append(stop_output_sec)

        # ---------------- Real time ------------------

        # Second, calculate real time for this chunk
        start_real_sec = (start_source_sec - fade_length) + real_time_offset
        stop_real_sec = start_real_sec + chunk_duration

        real_starts_sec.append(start_real_sec)
        real_stops_sec.append(stop_real_sec)

        # ----------------------------------------------------------------------
        # Work on gap chunk:
        # |fadein0chunk0|fadeout0gap0|
        #                ************ <- indexes for fade-out through gap
        # ----------------------------------------------------------------------

        section_type.append("gap")

        # ---------------- Output time ------------------

        # On the final video the gap will go:
        # (prev_stop + 1) -> (prev_stop + 1 + gap_duration)
        start_output_sec = output_stops_sec[-1] + 1
        gap_duration_sec = _time_to_seconds(gap_after[i]) + fade_length
        stop_output_sec = start_output_sec + gap_duration_sec

        output_starts_sec.append(start_output_sec)
        output_stops_sec.append(stop_output_sec)

        # ---------------- Real time ------------------

        # The real start time is the last real time seen + 1
        start_real_sec = real_stops_sec[-1] + 1

        # Get the next chunk start SOURCE time (either the start of the next
        # chunk or the end of the video).
        if i != len(starts) - 1:
            start_source_next_chunk = _time_to_seconds(starts[i+1]) - fade_length
        else:
            start_source_next_chunk = video_props["duration"]

        # Gap duration the time between the (start of next chunk - 1) and the
        # end of the chunk.
        gap_duration = (start_source_next_chunk - 1) - (stop_source_sec + 1)
        stop_real_sec = start_real_sec + gap_duration

        real_starts_sec.append(start_real_sec)
        real_stops_sec.append(stop_real_sec)

        # ---------------------------------------------------------------------
        # Construct temporary video files for this chunk

        # Create initial fade in (start - fade_length) -> start
        fade_in_file = "{}_{:03}_fade-in.mp4".format(file_prefix,i)
        _fade_in(video_file,fade_in_file,start_source_string,fade_length)
        file_list.append(fade_in_file)

        # Chop out video chunk from start -> stop
        chunk_out_file = "{}_{:03}.mp4".format(file_prefix,i)
        _slice_out(video_file,chunk_out_file,start_source_string,stop_source_string)
        file_list.append(chunk_out_file)

        # Generate fade out (stop -> stop + fade_length)
        fade_out_file = "{}_{:03}_fade-out.mp4".format(file_prefix,i)
        _fade_out(video_file,fade_out_file,stop_source_string,fade_length)
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
    out = ffmpeg.output(joined[0],joined[1],
                        "{}_final.mp4".format(file_prefix),
                        **video_props["out_kwargs"])
    out.run()

    # Copy final file to output file name and nuke temporary files
    to_remove = glob.glob("{}*".format(file_prefix))
    shutil.copy("{}_final.mp4".format(file_prefix),output_file)
    for f in to_remove:
        os.remove(f)


    # Write out timebase_file, if requested.
    if timebase_file is not None:

        out_dict = {}
        out_dict["section_type"] = section_type
        out_dict["real_start"] = [_seconds_to_time(t) for t in real_starts_sec]
        out_dict["real_stop"] = [_seconds_to_time(t) for t in real_stops_sec]
        out_dict["video_start"] = [_seconds_to_time(t) for t in output_starts_sec]
        out_dict["video_stop"] = [_seconds_to_time(t) for t in output_stops_sec]

        pd.DataFrame(out_dict).to_csv(timebase_file,index=False)


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

    argv: command line arguments
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
                        help="column in spreadsheet with chunk start time stamps [default 'start']",
                        action=_NonDefaultAction)
    parser.add_argument('--stop-column','-p',dest="stop_column",
                        type=str,default="stop",nargs=1,
                        help="column in spreadsheet with chunk stop time stamps [default 'stop']",
                        action=_NonDefaultAction)
    parser.add_argument('--gap-column','-g',dest="gap_column",
                        type=str,default=None,nargs=1,
                        help="column in spreadsheet with gaps to add after chunks [default 'None']",
                        action=_NonDefaultAction)

    # Output and video arguments
    parser.add_argument('--out-file','-o',dest="out_file",
                        type=str,nargs=1,default="{video_file}.processed.mp4",
                        help="name of output file [default: 'processed_{video_file}'']",
                        action=_NonDefaultAction)
    parser.add_argument('--fade-length','-f',dest="fade_length",
                        type=int,nargs=1,default=1,
                        help="fade length for transitions, in seconds [default '1']")

    # Timebase arguments
    parser.add_argument('--timebase-file','-t',dest="timebase_file",
                        type=str,nargs=1,default=None,
                        help="file in which to store csv mapping chopped time to real time [default 'None'; do not write out]",
                        action=_NonDefaultAction)
    parser.add_argument("--real-time","-r",dest="real_time",
                        type=str,nargs=1,default="00:00:00",
                        help="real start time of first video chunk as HH:MM:SS string [default: '00:00:00']",
                        action=_NonDefaultAction)

    parser.add_argument("--force",dest="force",action="store_true",
                        help="overwrite any previous output files")


    args = parser.parse_args(argv)

    video_file = args.video_file[0]
    spreadsheet_file = args.spreadsheet[0]

    # Grab start_column
    if hasattr(args,"start_column_nondefault"):
        start_column = args.start_column[0]
    else:
        start_column = args.start_column

    # Grab stop_column
    if hasattr(args,"stop_column_nondefault"):
        stop_column = args.stop_column[0]
    else:
        stop_column = args.stop_column

    # Grab gap_column
    if hasattr(args,"gap_column_nondefault"):
        gap_column = args.gap_column[0]
    else:
        gap_column = args.gap_column

    # Grab out_file
    if hasattr(args,"out_file_nondefault"):
        out_file = args.out_file[0]
    else:
        out_file = "processed_{}".format(video_file)

    # get fade_length
    fade_length = args.fade_length

    # Grab timebase file
    if hasattr(args,"timebase_file_nondefault"):
        timebase_file = args.timebase_file[0]
    else:
        timebase_file = args.timebase_file

    # Grab real time
    if hasattr(args,"real_time_nondefault"):
        real_time = args.real_time[0]
    else:
        real_time = args.real_time

    # grab force
    force = args.force

    # Process the video
    process_video(video_file,out_file,
                  spreadsheet_file,
                  start_column,stop_column,gap_column,
                  fade_length,
                  timebase_file,real_time,
                  force)

# If called from the command line.
if __name__ == "__main__":
    main()
