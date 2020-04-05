#!/usr/bin/env python
__description__ = \
"""
Tool for randomly creating groups/zoom breakout rooms for groups of students
weighted by a proficiency score.
"""
__author__ = "Michael J. Harms"
__date__ = "2020-03-30"

import numpy as np
import pandas as pd

import json, random, re, random, argparse, sys, os
import urllib.request


class GroupNameGenerator:
    """
    Generate random group names by combining adjective/noun pairs.
    Filters for words less than or equal to max_word_len and discards
    expletives.
    """

    def __init__(self,max_word_len=8,loop_timeout=100):
        """
        max_word_len: longest word length allowed
        loop_timeout: after loop_timeout tries, give up making a new unique name
        """

        self._loop_timeout = loop_timeout

        bad_char = re.compile("\W")

        adj = self._download_json("https://github.com/dariusk/corpora/raw/master/data/words/adjs.json")
        adj = [a.lower() for a in adj["adjs"] if len(a) <= max_word_len]

        noun = self._download_json("https://github.com/dariusk/corpora/raw/master/data/words/nouns.json")
        noun = [n.lower() for n in noun["nouns"] if len(n) <= max_word_len]

        expletives = self._download_json("https://github.com/dariusk/corpora/raw/master/data/words/expletives.json")
        expletives = [e.lower() for e in expletives]
        expletives.append("genitals")
        expletives.append("genitalia")
        expletives.append("puberty")

        self.noun = [n for n in noun if not bad_char.search(n) and n not in expletives]
        self.adj = [a for a in adj if not bad_char.search(a) and a not in expletives]

        self._groups_generated = {}

    def _download_json(self,url):

        response = urllib.request.urlopen(url)
        return json.loads(response.read().decode('ascii'))


    @property
    def current_group(self):

        counter = 0
        while True:

            adj = random.choice(self.adj)
            noun = random.choice([n for n in self.noun if n.startswith(adj[0])])
            group = "{}_{}".format(adj,noun)

            # Make sure that the newest group is unique
            try:
                self._groups_generated[group]
            except KeyError:
                self._groups_generated[group] = None
                break

            if counter > self._loop_timeout:
                err = "could not find another unique name ({} total generated)\n".format(len(self._groups_generated))
                raise ValueError(err)

            counter += 1


        return group

def create_partners(scores,score_noise=2.0,num_chunks=4):
    """
    Create random partners in a class, with pairing biased such that most-
    scoreed students are paired with least-scoreed students. This is done by
    sorting the class based on the array scores, breaking the class into
    num_chunks chunks, and then making pairs by moving in from outermost to
    innermost chunks to create pairs. If there is an odd number of students, one
    group of three is created.

    arguments
    ---------

    scores: array of scores

    score_noise: standard deviation of noise to add to scores.  noise ensures that the
                 same students aren't always at the top and the bottom, and thus that they
                 don't always get paired.

    num_chunks: how many chunks to break the class into for pairing.  a value of 4 would
                break the class into quartiles, then randomly assign pairs from the
                1st and 4th quartile, then from the 2nd and 3rd quartile.  This value
                must be even.

    returns
    -------

    list of lists containing integer ind
    """

    # Names is list of integers corresponding to the order in which the
    # scores were fed in.
    names = range(len(scores))

    # Add gaussian noise to the scores
    noisy_scores = np.array(scores) + np.random.normal(0,2,len(scores))

    # Sort students by score from lowest to highest
    score_name = []
    for i in range(len(names)):
        score_name.append((noisy_scores[i],names[i]))
    score_name.sort()

    # number of ways to split the class.  force to be even
    if num_chunks % 2 != 0:
        num_chunks = num_chunks - 1

    if num_chunks > len(score_name):
        err = "Number of chunks exceeds the number of students.\n"
        raise ValueError(err)

    partners = []

    # Deal with the fact that number of students might not be divisible by
    # num_chunks by shaving the top and the bottom students and making them
    # partners until it's properly divisible.
    remainder = len(score_name) % num_chunks
    while remainder > 1:
        partners.append([score_name[0][1],score_name[-1][1]])
        score_name = score_name[1:-1]
        remainder = remainder - 2

    # If we've got a student leftover, there are an odd number of students.
    # Store lowest student for later
    spare_student = None
    if remainder == 1:
        spare_student = score_name[0]
        score_name = score_name[1:]

    # Now create chunks
    chunk_size = int(len(score_name)/num_chunks)
    chunks = [score_name[i:i+chunk_size]
              for i in range(0,len(score_name),chunk_size)]

    # Now make partners moving from outside chunks to inside chunks
    for i in range(int(len(chunks)/2)):

        lower_edge = chunks[i][:]
        upper_edge = chunks[len(chunks)-1-i][:]

        # randomize within chunks
        random.shuffle(lower_edge)
        random.shuffle(upper_edge)

        # Create partners
        for j in range(len(lower_edge)):
            partners.append([lower_edge[j][1],upper_edge[j][1]])

    # If there was a spare student, add them to a random group to make a triple
    if spare_student is not None:
        index = random.choice(range(len(partners)))
        partners[index].append(spare_student[1])

    # Shuffle the partners so the lowest student doesn't always appear first
    random.shuffle(partners)


    return partners

def simple_break(scores,group_size,score_noise=None):
    """
    Break a vector of scores into groups of group_size.  Tries to assign
    one person from each score category. (For a group size of 4, this would
    mean low, okay, good, great members of a group).

    score_noise specifies how much noise to add to the score.  This is useful,
    particularly for relatively small groups, because it means you end up
    with different groups each time you run it. If None -> 0.1*std_dev(score);
    otherwise, it is interpreted as the std_dev of the noise to add.  If 0, no
    noise is added.

    For groups of two, you might consider create_partners rather than
    simple_break.
    """

    # Figure out what sort of noise to add to the scores.  If None,
    # give 0.1*standard deviation of scores as noise. If 0, add no noise.
    # otherwise, use score_noise as the standard deviation for the noisy
    # generator.
    if score_noise is None:
        score_noise = np.random.normal(0,np.std(scores)/10.,len(scores))
    else:
        if score_noise == 0:
            score_noise = np.zeros(len(scores))
        else:
            score_noise = np.random.normal(0,score_noise,len(scores))

    # Add gaussian noise to the scores
    noisy_scores = np.array(scores) + np.random.normal(0,2,len(scores))

    # Figure out how many groups to include
    num_groups = len(scores) // break_size

    # Sort names by scores
    to_chop = [(s,i) for i, s in enumerate(noisy_scores)]
    to_chop.sort()

    # Find extras that don't fit into the groups
    num_extras = len(scores) % num_groups

    # If there are extra people, rip them from the exact center of the
    # score list and stick them on the very end.
    extra_peeps = []
    if num_extras > 0:
        center_start = (len(to_chop) // 2) + (num_extras // 2)
        for c in range(center_start,center_start-num_extras,-1):
            extra_peeps.append(to_chop.pop(c))
    to_chop.extend(extra_peeps)

    # Create list of break groups
    break_groups = []
    for b in range(break_size):
        break_groups.append(to_chop[(b*num_groups):((b+1)*num_groups)])
    if num_extras > 0:
        break_groups.append(to_chop[((b+1)*num_groups):])

    # Shuffle within each break group
    for bg in break_groups:
        random.shuffle(bg)

    final_groups = []
    for i in range(num_groups):
        final_groups.append([])
        for j in range(len(break_groups)):
            try:
                member = break_groups[j][i][1]

                final_groups[i].append(member)
            except IndexError:
                pass

    return final_groups


def assign_groups(df,score_column="score",id_column="email",group_size=2,
                  use_zoom=False):

    try:
        score = df[score_column]
    except KeyError:
        err = "input dataframe does not have column '{}'\n".format(score_column)
        raise ValueError(err)

    if group_size < 1 or group_size > len(score) // 2:
        err = "group_size must be between 1 and num_students/2\n"
        raise ValueError(err)

    if use_zoom:
        try:
            email = df[id_column]
        except KeyError:
            err = "if writing a zoom breakout room file, the input dataframe\n"
            err += "must have an id_column specifying student email used to log\n"
            err += "in to zoom.\n"
            raise ValueError(err)

    if group_size == 2:
        groups = create_partners(score)
    else:
        groups = simple_break(score,group_size)

    final_groups = [None for _ in range(len(score))]
    G = GroupNameGenerator()
    for group in groups:

        group_name = G.current_group
        for member in group:
            final_groups[member] = group_name

    if use_zoom:
        out_dict = {"Pre-assign Room Name":final_groups,
                    "Email Address":df["email"]}
        final_df = pd.DataFrame(out_dict)
        final_df = final_df.sort_values("Pre-assign Room Name")
    else:
        final_df = df.copy()
        final_df["group_assignment"] = final_groups

    return final_df

class _NonDefaultAction(argparse.Action):
    """
    Subclass of argparse.Action that reports whether a non-default value of the
    argument was used.
    """
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, self.dest+'_nondefault', True)


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('spreadsheet',type=str,nargs=1,
                        help='spreadsheet containing student identifiers and scores')
    parser.add_argument('--score-column','-s',dest="score_column",
                        type=str,default="score",nargs=1,
                        help="column in spreadsheet with scores for group assignments",
                        action=_NonDefaultAction)
    parser.add_argument('--id-column','-i',dest="id_column",
                        type=str,default="email",nargs=1,
                        help="column in spreadsheet with student identifiers for assignments",
                        action=_NonDefaultAction)
    parser.add_argument('--group-size','-g',dest="group_size",default=2,
                        type=int,nargs=1,help="group size",
                        action=_NonDefaultAction)
    parser.add_argument('--zoom','-z', dest="use_zoom",action='store_true',
                        help="generate a zoom-compatible .csv output")
    parser.add_argument('--out-file','-o',dest="out_file",default=None,
                        type=str,nargs=1,
                        help="name out output file (filetype determined by extension)",
                        action=_NonDefaultAction)

    args = parser.parse_args(argv)


    spreadsheet = args.spreadsheet[0]

    # Grab score_column
    if hasattr(args,"score_column_nondefault"):
        score_column = args.score_column[0]
    else:
        score_column = args.score_column

    # Grab id_column
    if hasattr(args,"id_column_nondefault"):
        id_column = args.id_column[0]
    else:
        id_column = args.id_column

    # Grab group_size
    if hasattr(args,"group_size_nondefault"):
        group_size = args.group_size[0]
    else:
        group_size = args.group_size

    use_zoom = args.use_zoom

    # Grab out_file
    if hasattr(args,"out_file_nondefault"):
        out_file = args.out_file[0]
    else:
        out_file = args.out_file

    if spreadsheet.split(".")[-1] in ["xlsx","xls"]:
        df = pd.read_excel(spreadsheet)
    elif spreadsheet.split(".")[-1] == ".csv":
        df = pd.read_csv(spreadsheet)
    else:
        err = "spreadsheet type must be .xlsx or .csv\n"
        raise ValueError(err)

    group_df = assign_groups(df,
                             score_column=score_column,
                             id_column=id_column,
                             group_size=group_size,
                             use_zoom=use_zoom)

    if out_file is None:
        print(group_df.to_csv())
    else:
        if os.path.isfile(out_file):
            err = "file '{}' already exists\n".format(out_file)
            raise FileExistsError(err)

        if out_file.split(".")[-1] == "xlsx":
            group_df.to_excel(out_file)
        elif out_file.split(".")[-1] == "csv":

            if use_zoom:
                group_df.to_csv(out_file,index=False)
            else:
                group_df.to_csv(out_file)
        else:
            err = "output file format must be .xslx or .csv\n"
            raise ValueError(err)






if __name__ == "__main__":
    main()
