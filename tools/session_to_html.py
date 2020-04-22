#/usr/bin/env python
__description__ = \
"""
Render a webpage summarizing a scientific computing class session.
"""
__author__ = "Michael J. Harms"
__date__ = "2020-03-30"

import session_to_site

import jinja2
import argparse, sys, json


def session_to_html(control,template_file):

    try:
        threads = session_to_site.parse_slack_channel(control["slack"]["zipfile"],
                                                      control["slack"]["channel"])

        control["threads"] = threads
    except KeyError:
        pass 

    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader,
                                      autoescape=jinja2.select_autoescape("html"))
    template = template_env.get_template(template_file)
    output = template.render(session=control)

    f = open("index.html","w")
    f.write(output) #"parent.html"))
    f.close()


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    json_file = argv[0]
    control = json.load(open(json_file,'r'))[0]
    template_file = argv[1]




    #from jinja2 import Template
    #with open(template_file) as file_:
#        template = Template(file_.read())
#    template.render(


    session_to_html(control,template_file)

    return

    """

    parser = argparse.ArgumentParser(description=__description__)
    parser.add_argument('spreadsheet',type=str,nargs=1,
                        help='spreadsheet containing student identifiers and scores')
    parser.add_argument('--score-column','-s',dest="score_column",
                        type=str,default="score",nargs=1,
                        help="column in spreadsheet with scores for group assignments")
    parser.add_argument('--group-size','-g',dest="group_size",default=2,
                        type=int,nargs=1,help="group size")
    parser.add_argument('--zoom','-z', dest="use_zoom",action='store_true',
                        help="generate a zoom-compatible .csv output")
    parser.add_argument('--out-file','-o',dest="out_file",default=None,
                        type=str,nargs=1,
                        help="name out output file (filetype determined by extension)")

    args = parser.parse_args(argv)

    spreadsheet = args.spreadsheet[0]
    score_column = args.score_column
    group_size = args.group_size
    use_zoom = args.use_zoom
    out_file = args.out_file[0]

    if spreadsheet.split(".")[-1] in ["xlsx","xls"]:
        df = pd.read_excel(spreadsheet)
    elif spreadsheet.split(".")[-1] == ".csv":
        df = pd.read_csv(spreadsheet)
    else:
        err = "spreadsheet type must be .xlsx or .csv\n"
        raise ValueError(err)

    group_df = assign_groups(df,
                             score_column=score_column,
                             group_size=group_size,
                             use_zoom=use_zoom)

    if out_file is None:
        print(df.to_string())
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

    """




if __name__ == "__main__":
    main()
