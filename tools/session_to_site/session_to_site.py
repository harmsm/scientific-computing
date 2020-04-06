
import jinja2
import os
#from jinja2 import Environment, PackageLoader, select_autoescape

def render(session,template_file):

    template_file = os.path.split(template_file)[1]
    template_file_dir = os.path.split(template_file)[0]

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_file_dir))



    #env = Environment(loader=PackageLoader("session_to_site","templates"),
    #                  autoescape=select_autoescape("html"))

    template = env.get_template(template_file)

    return template.render(session=session)
