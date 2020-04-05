__description__ = \
"""
Extract threads from slack json file and generate pretty, html-compatible
input for the templater.
"""
__author__ = "Michael J. Harms"
__date__ = "2020-03-29"

import json, re, os, urllib, zipfile, shutil, random, string, emoji
from datetime import datetime
import urllib.request, urllib.response, urllib.error


class StringHandler:
    """
    Given a string of slack input, look for pattern, replace the field
    """

    def __init__(self,pattern,replace_dict={}):

        self._pattern = pattern
        self._replace_dict = replace_dict
        self._search_pattern = re.compile(self._pattern,re.DOTALL)


    def filter_string(self,text_string):

        cuts = []
        replacements = []
        for match in self._search(text_string):

            # Figure out where to cut the string
            start = match.span()[0]
            end = match.span()[1]

            # Grab the field.
            field = self._process_match(text_string[start+1:end-1])
            replacements.append(field)

            # append cuts
            cuts.append((start,end+1))

        # Assemble the final string
        for i in range(len(cuts)-1,-1,-1):
            text_string = "{}{}{}".format(text_string[:cuts[i][0]],
                                          replacements[i],
                                          text_string[cuts[i][1]:])
        return text_string

    def _search(self,text_string):
        """
        Search for matches to self._search pattern in the text string.
        """

        return self._search_pattern.finditer(text_string)

    def _replace_match(self,field):
        """
        Try to replace the field with match in replace_dict.  Replace both
        match and whether replacement was successful.
        """

        try:
            new_field = self._replace_dict[field]
            return new_field, True
        except KeyError:
            return field, False

    def _process_match(self,field):
        """
        Process a match.
        """

        field, status = self._replace_match(field)

        return field

class SymmetricalStringHandler(StringHandler):
    """
    Identical to string handler except only returns every other match of the
    regex match to avoid screwing up patterns like 'code1' and 'code2'.
    """

    def _search(self,text_string):

        # Only return every other match if search pattern is symmetrical
        # (like `blah` or *blah*)
        return list(self._search_pattern.finditer(text_string))[::2]


class UrlHandler(StringHandler):
    """
    Process urls.
    """

    def __init__(self,pattern="\<http.*?\>|\<ftp.*?\>",replace_dict={}):

        super().__init__(pattern,replace_dict)

    def _process_match(self,field):

        field, status = self._replace_match(field)

        url_pattern = re.compile("\?|\|")
        url = url_pattern.split(field)[0]

        if url[-4:].lower() in [".png",".jpg","jpeg",".gif",".bmp"]:
            field = "<a href=\"{}\"><img src=\"{}\" class=\"img-fluid url-image\"></a>".format(url,url)
        else:
            field = "<a href=\"{}\">{}</a>".format(url,url)

        return field

class AtUserHandler(StringHandler):
    """
    Process @user fields.
    """

    def __init__(self,pattern="\<\@.*?\>",replace_dict={}):

        super().__init__(pattern,replace_dict)

    def _process_match(self,field):

        field, status = self._replace_match(field)
        return "<span class=\"font-italic\">@{} </span>".format(field)

class HashChannelHandler(StringHandler):
    """
    Process #channel fields.
    """

    def __init__(self,pattern="\<\#.*?\>",replace_dict={}):

        super().__init__(pattern,replace_dict)

    def _process_match(self,field):

        field, status = self._replace_match(field)

        try:
            new_field = field.split("|")[1]
        except IndexError:
            new_field = field

        return "<span class=\"font-italic\">#{} </span>".format(new_field)

class CodeHandler(SymmetricalStringHandler):
    """
    Process `code` fields.
    """

    def __init__(self,pattern="\`.*?\`",replace_dict={}):

        super().__init__(pattern,replace_dict)

    def _process_match(self,field):

        field, status = self._replace_match(field)
        return "<code>{}</code>".format(field)

class CodeBlockHandler(SymmetricalStringHandler):
    """
    Process ```code``` fields.
    """

    def __init__(self,pattern="```.*?```",replace_dict={}):

        super().__init__(pattern,replace_dict)

    def _process_match(self,field):

        field, status = self._replace_match(field)

        return "<div class=\"card m-1 bg-light p-2\"><pre><code>{}</code></pre></div>".format(field[2:-2])

def _process_polly_poll(msg):

    name = "Polly Poll"

    try:
        icon = msg["icons"]["image_48"]
    except KeyError:
        icon = None

    poll_creator = msg["text"].split()[0]
    question = msg["blocks"][0]["text"]["text"][1:-1]

    i = 2
    responses = []
    while True:
        try:
            this_response = msg["blocks"][i]["fields"]
            responses.extend(this_response)
            i += 1
        except KeyError:
            break


    text = ["<div class=\"card p-2\">"]
    text.append("<div>Poll by {}:</div>".format(poll_creator))
    text.append("<div class=\"font-italic\">{}</div>".format(question))

    filled_bar_pattern = re.compile("\u2588")
    response_bar_pattern = re.compile("\`.*?\`")

    text.append("<table class=\"table table-striped p-3\"><tbody>")
    for response in responses:

        r = response['text']

        answer = r.split()[0].strip()
        bar = response_bar_pattern.findall(r)[0][1:-1]
        num_yes = len(filled_bar_pattern.findall(bar))

        text.append("<tr>")
        text.append("<td>{}</td>".format(answer))
        text.append("<td>{}</td>".format(bar))
        text.append("<td>{}</td>".format(num_yes))
        text.append("</tr>")
    text.append("</tbody></table>")

    text_string = "".join(text)

    return name, icon, text_string



def parse_slack_channel(slack_zip_file,
                        channel="in_class",
                        out_dir="attachments",
                        date_span=None):

    """
    Generate a list of threads, formatted in pretty fashion, from an exported
    slack zip file.

    slack_zip_file: zip file generated by slack export
    out_dir: output directory for images
    channel: slack channel to extract
    date_span: (start_timestamp,end_timestamp) where timestamps are unix-style
    """

    # Check sanity of date_span
    if date_span is not None:
        try:
            if len(date_span) != 2:
                raise TypeError
            date_span[0] < 0
            date_span[1] < 0
        except TypeError:
            err = "date_span must be have a length of 2 (start,stop) containing unix timestamps\n"
            raise ValueError(err)

    # -------------------------------------------------------------------------
    # Extract slack zip file

    zf = zipfile.ZipFile(slack_zip_file)
    tmp_dir = "tmp_{}".format("".join([random.choice(string.ascii_letters) for _ in range(10)]))
    os.mkdir(tmp_dir)
    os.chdir(tmp_dir)
    zf.extractall()

    # extract channel
    try:
        channel_messages = []
        for f in os.listdir(channel):
            channel_messages.extend(json.load(open(os.path.join(channel,f))))
    except FileNotFoundError:
        os.chdir("..")
        shutil.rmtree(tmp_dir)
        err = "channel '{}' not in this slack export\n".format(channel)
        raise ValueError(err)


    # Load users_dict, allowing us to look up users by user_id or
    # @user_id
    users_dict = {}
    names_dict = {}
    icons_dict = {}
    if os.path.isfile("users.json"):

        users = json.load(open("users.json"))
        users_dict = dict([(u["id"],u) for u in users])
        for k in list(users_dict.keys()):
            users_dict["@{}".format(k)] = users_dict[k]

        names_dict = {}
        icons_dict = {}
        for k in users_dict.keys():
            names_dict[k] = users_dict[k]["profile"]["real_name"]
            icons_dict[k] = users_dict[k]["profile"]["image_72"]

    # Leave temporary directory and nuke it
    os.chdir("..")
    shutil.rmtree(tmp_dir)
    # -------------------------------------------------------------------------


    # Handlers for processing messages
    handlers = [UrlHandler(),
                AtUserHandler(replace_dict=names_dict),
                HashChannelHandler(),
                CodeBlockHandler(),
                CodeHandler()]

    # Go through messages, keeping track of threading
    thread_indexes = {}
    thread_list = []
    thread_counter = 0
    for m in channel_messages:

        final_message = {}

        # ---------------------------------------------------------------------

        # Grab time stamp
        timestamp = int(m['ts'].split(".")[0])

        # Check date range
        if date_span is not None:
            if timestamp < date_span[0] or timestamp > date_span[1]:
                continue

        # Record time stamp
        final_message["time"] = str(datetime.fromtimestamp(timestamp))

        # ---------------------------------------------------------------------

        # Grab basic information to construct html for this message
        try:
            text_string = m['text']
            final_message["user"] = names_dict[m['user']]
            final_message["icon"] = icons_dict[m['user']]

        # Basic information fails for some messages ...
        except KeyError:

            # See if this is a polly poll
            polly_poll = False
            try:
                if m['subtype'] == "bot_message" and m["username"] == "Polly":
                    polly_poll = True
            except KeyError:
                pass

            if polly_poll:
                usr, icon, text_string = _process_polly_poll(m)

                final_message["user"] = usr
                if icon is not None:
                    final_message["icon"] = icon
            else:
                continue

        # Process text_string
        for h in handlers:
            text_string = h.filter_string(text_string)

        text_string = emoji.emojize(text_string,use_aliases=True)
        final_message["message"] = text_string

        # ---------------------------------------------------------------------

        # See if there are any reactions to grab.  Try to convert them to
        # emojis
        all_rxn = []
        try:
            for rxn in m['reactions']:
                e = ":{}:".format(rxn['name'])
                all_rxn.append({"name":emoji.emojize(e,use_aliases=True),
                                "count":rxn['count']})
        except KeyError:
            pass

        final_message["reactions"] = all_rxn

        # ---------------------------------------------------------------------

        # See if their are any attachments
        attachments = []
        try:
            tmp_attachments = []
            for f in m['files']:

                try:
                    tmp_attachments.append(f['url_private_download'])
                except KeyError:
                    continue

            # Make output dir if there are attachments
            try:
                os.mkdir(out_dir)
            except FileExistsError:
                pass

            # Download the files
            for url in tmp_attachments:
                base = url.split("?")[0]
                new_path = os.path.join(out_dir,"{}".format("_".join(base.split(os.sep)[-3:])))
                urllib.request.urlretrieve(url, new_path)

                attachments.append(new_path)

        except KeyError:
            pass

        attachment_url = []
        for a in attachments:
            if a[-4:].lower() in [".png",".jpg",".bmp",".gif"]:
                attachment_url.append("<a href=\"{}\"><img src=\"{}\" class=\"img-fluid attachment-img\"></a>".format(a,a))
            else:
                attachment_url.append("<a href=\"{}\" class=\"attachment-file\">{}</a>".format(a,a))


        # ---------------------------------------------------------------------
        # Now figure out threading

        # The thread_ts key indicates this is part of a thread
        thread_index = None
        try:

            # If the thread_ts is already in thread_keys, grab the index
            # of the parent message.  Otherwise, this is the parent.
            thread_ts = m['thread_ts']
            try:
                thread_index = thread_indexes[thread_ts]
            except KeyError:
                thread_indexes[thread_ts] = thread_counter

        except KeyError:
            pass

        # If there is no message index, start a new thread for this message
        if thread_index is None:
            thread_list.append([final_message])
            thread_counter += 1

        # If there *is* a thread index, append this to an existing thread
        else:
            thread_list[thread_index].append(final_message)

    return thread_list
