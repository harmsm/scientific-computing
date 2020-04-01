#!/usr/bin/env python3
__description__ = \
"""
Generate slack "polly" quiz prompts from a simple input text file.
"""
__usage__ = "polly_generator.py quiz_file [question_numbers]"
__author__ = "Michael J. Harms"
__date__ = "2017-04-06"

import sys

def parse_question_file(quiz_file,questions_to_include=None):
    """
    Take a file with quiz questions and return a string that can be parsed by
    "polly" for generation of quizzes on slack.  
    
    arguments:
    ----------

    quiz_file is a list of quiz questions where questions are on lines that do
    not start with space, while answers do start with a space. 

    question
        answer_1
        answer_2 
        ...

    questions_to_include is a string that looks like a python-style list slice.
    0:-1 would, for example, return all entries.  0:2 would return the first
    two.  If None, all questions are returned.


    returns:
    --------

    returns a list of polly-style strings that look like:
    /polly "question" "answer1" answer2" ...
    """

    # read quiz file
    f = open(quiz_file,'r')
    lines = f.readlines()
    f.close()

    # strip blank lines and comments ("#")
    lines = [l for l in lines if l.strip() != "" and l.strip()[0] != "#"]

    num_questions = 0
    for l in lines:
        if not l.startswith(" "):
            num_questions += 1

    # parse questions_to_include_string
    if questions_to_include != None:

        questions_to_include = questions_to_include.strip()
        try:

            split_include = questions_to_include.split(":")

            # parse questions to include using ":".  If this has more than two
            # ":" splits, throw an error.
            if len(split_include) == 1:
                if int(split_include[0]) < 0:
                    x = num_questions + int(split_include[0])
                    split_include = [x,x+1]
                else:
                    split_include.append(int(split_include[0]) + 1)
            elif len(split_include) == 2:

                if split_include[0] == "":
                    split_include[0] = 0
                
                if split_include[1] == "":
                    split_include[1] = num_questions 

            for i in range(len(split_include)):
                split_include[i] = int(split_include[i])



        except ValueError:
            err = "could not parse question numbers.  these should look like python list slices.\n"
            raise ValueError(err)

    # If no questions_to_include, just give all 
    else:
        split_include = [0,num_questions] 
      
    # Create a list of questions by walking through 
    questions = []
    for l in lines:

        # If a new questions, make a new question
        if not l.startswith(" "):
            questions.append((l.strip(),[]))
        # Otherwise, record an answer
        else:
            questions[-1][1].append(l.strip())

    # make 'polly' readable output
    final_out = []
    for q in questions[split_include[0]:split_include[1]]:
        out = []
        out.append("/polly")
        out.append("\"{}\"".format(q[0]))
        for a in q[1]:
            out.append("\"{}\"".format(a))
    
        out.append("\n")
        final_out.append(" ".join(out))

    return final_out


def main(argv=None):
    """
    Parse command line.
    """

    if argv == None:
        argv = sys.argv[1:]

    try:
        input_file = argv[0]
    except IndexError:
        err = "you must specify an input file with questions. usage:\n\n{}\n\n".format(__usage__)
        raise IndexError(err)

    try:
        question_numbers = argv[1]
    except IndexError:
        question_numbers = None

    final_out = parse_question_file(input_file,question_numbers)

    return final_out

# If run from the command line...
if __name__ == "__main__":
    print("\n".join(main()))


