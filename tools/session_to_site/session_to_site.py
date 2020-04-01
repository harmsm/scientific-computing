
from jinja2 import Environment, PackageLoader, select_autoescape

def render(session,template_file):

    env = Environment(loader=PackageLoader("session_to_site","templates"),
                      autoescape=select_autoescape("html"))

    template = env.get_template(template_file)

    return template.render(session=session)
