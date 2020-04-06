#!/usr/bin/env python3
__description__ = \
"""
Convert a class schedule, in xlsx format, into .rst format for display on a
web page.

Assumes xlsx file has a "schedule" worksheet that will be used for
construction of an rst table.

Optionally looks for "links" tab with columns:
    ("link_alias","link_url","link_text")
These columns map between aliases for links in the schedule and actual link
urls.  Link aliases must:
    1. Start with "_"
    2. Must not contain [whitespace,.;:]
"""
__author__ = "Michael J. Harms"
__date__ = "2019-10-02"
__usage__ = "./xlsx_to_rst.py schedule.xlsx"

import numpy as np
import pandas as pd
from xlrd import XLRDError

import sys, re, copy

def _replace_links(input_string,link_dict={}):
    """
    Take an input string and replace link aliases with rst link strings.

    Link aliases are identified by ";_" OR ",_" OR " _" OR ":_".

    link_dict should key link_alias to (url, text).  If link_alias is
    not found in the dictionary, it is replaced by link_alias[1:], thus
    chopping off leading "_".
    """

    # Dictionary to hold link string/target pairs
    target_dict = {}

    # Strip white space from string
    this_string = input_string.strip()

    # If we have a string stub, return it
    if len(input_string) < 2:
        return input_string, {}

    # Look for patterns: ";_" OR ",_" OR " _" OR ":_"
    search_pattern = re.compile("[\,\s\;\:]\_|\A\_")

    # Look for place to break link: ";" OR "," OR ":" OR " " OR "."
    end_pattern = re.compile("[\,\s\;\:\.]")

    # Look for a match
    match = search_pattern.search(this_string)
    while match:

        # If started with "_", link_alias starts at match.span()[0]
        if this_string[match.span()[0]] == "_":
            start = match.span()[0]

        # If started with ",_" or the like, link_alias starts at match.span()[0] + 1
        else:
            start = match.span()[0] + 1

        # Chop string into before and after _ in link (front and back)
        front = this_string[:start]
        back  = this_string[start:]

        # Look for end of the link
        link_end = end_pattern.search(back)

        # If we find the end, split back into link_alias and trailing
        if link_end:
            link_alias = back[:link_end.span()[0]]
            trailing = back[link_end.span()[0]:]

        # If we do not find the end, the whole back is link_alias ... no trailing
        else:
            link_alias = back[:]
            trailing = ""

        # Extract url and text for constructing the link text
        try:
            url, text = link_dict[link_alias]

            if url == "":
                if text == "":
                    raise KeyError
                else:
                    # Replace the link_alias with the text, no url
                    link_string = text
            else:
                if text == "":
                    # Replace the link_alias with link_alias[1:] -> url
                    label = link_alias[1:]
                else:
                    # Replace the link_alias with the text -> url
                    label = text

                link_string = "`{}`_".format(label)
                url_string = ".. _`{}`: {}".format(label,url)
                try:
                    already_seen = target_dict[label]
                    if already_seen != url_string:
                        err = "The same link_text '{}' corresponds to more than one url\n".format(text)
                        raise ValueError(err)
                except KeyError:
                    target_dict[label] = url_string

        except KeyError:

            # Replace the link_alias with link_alias[1:]
            link_string = link_alias[1:]

        # Rebuild this_string with front + new link + trailing
        this_string = "{}{}{}".format(front,link_string,trailing)

        # Look for another link
        match = search_pattern.search(this_string)

    return this_string, target_dict

def _load_df(xlsx_file,worksheet,col_to_keep=None):
    """
    Read worksheet of xlsx_file as strings, replacing blank (nan) with ''.
    if col_to_keep is specified, only keep those columns
    """

    # Read file
    df = pd.read_excel(xlsx_file,sheet_name=worksheet,dtype=str)

    # Drop extra columns if requested
    if col_to_keep is not None:
        df = df.filter(items=col_to_keep,axis=1)

    # Convert NaN -> ""
    for i, c in enumerate(df):
        for j, r in enumerate(df[c]):
            try:
                if np.isnan(r) or r.strip() == "nan":
                    df.iloc[j,i] = ""
            except TypeError:
                pass

    return df


def parse_xlsx(schedule_file,col_to_keep=None):
    """
    Convert an excel spreadsheet into an rst table.
    """

    # Read schedule xlsx file
    df = _load_df(schedule_file,"schedule",col_to_keep)

    # Construct a dictionary of links from the "links" worksheet
    try:

        link_df = _load_df(schedule_file,"links")

        # Grab aliases
        try:
            aliases = [a.strip() for a in link_df["link_alias"]]
        except KeyError:
            err = "if a links sheet is given, it must have a link_alias column\n"
            raise ValueError(err)

        # Sanity checking on aliases
        if len(aliases) != len(set(aliases)):
            err = "all link_alias entries must be unique\n"
            raise ValueError(err)

        disallowed = re.compile("[\.\,\;\:\s]")
        for a in aliases:
            if not a.startswith("_"):
                err = "all link_alias entries must start with '_'\n"
                raise ValueError(err)
            if disallowed.search(a):
                err = "link_alias entries must not have whitespace or [,.:;]\n"
                raise ValueError(err)

        # Grab urls; "" if not specified
        try:
            urls = link_df["link_url"]
        except KeyError:
            urls = ["" for _ in range(len(aliases))]

        # Grab link text; "" if not specified
        try:
            text = link_df["link_text"]
        except KeyError:
            text = ["" for _ in range(len(aliases))]

        # Construct link dictionary
        link_dict = {}
        for i, a in enumerate(aliases):
            link_dict[a] = (urls[i],text[i])

    # If no links worksheet, link_dict = {}
    except XLRDError:
        link_dict = {}

    # Go through entry.  Search and replace _link_alias entries with
    # rst-style links
    target_dict = {}
    for i, k in enumerate(df.columns):
        for j, v in enumerate(df[k]):

            df.iloc[j,i], new_target_dict = _replace_links(v,link_dict)
            if len(new_target_dict) > 0:
                for k in new_target_dict.keys():
                    try:
                        already_seen = target_dict[k]
                        if already_seen != new_target_dict[k]:
                            err = "The same link_text '{}' corresponds to more than one url\n".format(k)
                            raise ValueError(err)
                    except KeyError:
                        target_dict[k] = new_target_dict[k]

    return df, target_dict

def column_merge(df,merge_list=None,elements_as_bullets=None):

    if merge_list is None:
        merge_list = list(df.columns)

    # Make sure that merge_list is sane
    tmp_merge_list = []
    for m in merge_list:

        # If it's just a string, stick the string into a list of strings
        if type(m) is str:
            tmp_merge_list.append([m])
            continue
        else:
            try:
                tmp_merge_list.append([])
                for e in m:

                    if type(e) is not str:
                        err = "elements in merge list must be strings\n"
                        raise TypeError(err)

                    try:
                        df[e]
                    except KeyError:
                        err = "element '{}' not found in data frame\n".format(e)
                        raise ValueError(err)

                    tmp_merge_list[-1].append(e)

            except TypeError:
                err = "elements in merge_list must be either string or list of strings\n"
                raise ValueError(err)

    merge_list = copy.deepcopy(tmp_merge_list)

    # Create fake elements_as_bullets if none given.
    if elements_as_bullets is None:
        elements_as_bullets = []
        for m in merge_list:
            elements_as_bullets.append([None for _ in range(len(m))])

    # Make sure that elements_as_bullets is sane
    tmp_elements_as_bullets = []
    for i in range(len(merge_list)):

        a = elements_as_bullets[i]

        if type(a) in [type(None),str]:
            tmp_elements_as_bullets.append([a])
        else:
            try:
                num_okay = sum([type(e) in [type(None),str] for e in a])
                if num_okay != len(a):
                    raise TypeError
                tmp_elements_as_bullets.append(a)

            except TypeError:
                err = "elements in elements_as_bullets must be None/str or a list of None/str\n"
                raise ValueError(err)

    elements_as_bullets = copy.deepcopy(tmp_elements_as_bullets)

    # Rows in df

    columns = [m[0] for m in merge_list]
    out_dict = dict([(c,[]) for c in columns])
    for i in range(len(df)):

        row = df.iloc[i,:]

        for j in range(len(merge_list)):

            column_name = merge_list[j][0]

            to_merge = []
            for k in range(len(merge_list[j])):
                field = row[merge_list[j][k]]
                if elements_as_bullets[j][k]:
                    field = field.split(elements_as_bullets[j][k])
                else:
                    field = [field]

                if len(field[0].strip()) == 0:
                    continue

                # For everything but the first element, put the column name
                # as a bold bullet for the row
                if k > 0:
                    to_merge.append("\n + **{}**:".format(merge_list[j][k].strip()))

                local_merge = []
                for f in field:
                    if k <= 0:
                        local_merge.append("{}\n".format(f.strip()))
                    else:
                        local_merge.append("{}".format(f.strip()))
                to_merge.append("; ".join(local_merge))

            out_dict[column_name].append(" ".join(to_merge))

    return pd.DataFrame(out_dict)




def column_to_rst(df,target_dict):

    # -------------------------------------------------------------------------
    # Build RST
    # -------------------------------------------------------------------------

    # Find length of columns for construction of rst.
    col_width = dict([(column,1) for column in df.columns])
    row_height = [1 for _ in range(len(df.iloc[:,0]))]
    for c in df.columns:

        for i, row in enumerate(df[c]):

            paragraphs = [p for p in str(row).split("\n")]
            if len(paragraphs) > row_height[i]:
                row_height[i] = len(paragraphs)

            for paragraph in paragraphs:
                paragraph_length = len("{}".format(paragraph))
                if paragraph_length > col_width[c]:
                    col_width[c] = paragraph_length

    # Construct elements of correct length to build table
    header_strings = []
    row_strings = []
    fmt_strings = []
    for c in df:
        header_strings.append("+=" + (col_width[c] + 1)*"=")
        row_strings.append("+-" + (col_width[c] + 1)*"-")
        fmt_strings.append("| {{:{:}}} ".format(col_width[c]))
    header_strings.append("+")
    row_strings.append("+")

    # Row and header lines
    row_dashes = "-".join(row_strings)
    header_dashes = "=".join(header_strings)

    # Start with a row
    out = [row_dashes]

    # Create names of columns
    tmp_out = []
    for i, c in enumerate(df):
        tmp_out.append(fmt_strings[i].format(c))
    tmp_out.append("|")
    out.append(" ".join(tmp_out))

    # Add header break
    out.append(header_dashes)

    # Go through all rows in the data frame
    for i, row in df.iterrows():

        # Go through all line breaks in the row
        for row_line in range(row_height[i]):

            # Go through all columns
            tmp_out = []
            for j, column in enumerate(df.columns):

                # Grab the paragraphs
                paragraphs = [p for p in str(df.iloc[i,j]).split("\n")]

                # Grab the particular line break from the paragraphs. If this
                # cell doesn't have that many paragraphs, just append empty
                # spaces
                try:
                    tmp_out.append(fmt_strings[j].format(paragraphs[row_line]))
                except IndexError:
                    tmp_out.append(fmt_strings[j].format(" "))

            tmp_out.append("|")
            out.append(" ".join(tmp_out))

        out.append(row_dashes)

    out = ["    {}".format(o) for o in out]

    # Construct links below the table (to keep the table human-readable)
    out.append("")

    out.append(".. all links")
    for k in target_dict:
        out.append("{}".format(target_dict[k]))

    out.append("")

    return out


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    try:
        schedule_file = argv[0]
    except IndexError:
        err = "Incorrect arguments. Usage:\n\n{}\n\n".format(__usage__)
        raise ValueError(err)

    df, target_dict = parse_xlsx(schedule_file)
    new_df = column_merge(df,
                        merge_list = [["Date"],
                                      ["Topic","Due","Preclass","Postclass"]],
                        elements_as_bullets = [None,
                                               [None,",",",",","]]
    )

    print("\n".join(column_to_rst(new_df,target_dict)))

if __name__ == "__main__":
    main()
