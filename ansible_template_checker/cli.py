""" pre-commit check on jinja2 templates for Ansible"""
import sys
import os
from jinja2 import Environment, DictLoader, Undefined
from jinja2.exceptions import (TemplateSyntaxError, TemplateAssertionError,
                               UndefinedError, TemplateNotFound)


# This class exists so we don't have to try to import all possible variables.
# Using this method means we'll not be able to check for undefined variables,
# but force this check to be more of a syntax checker.
# https://stackoverflow.com/q/6190348
class SilentUndefined(Undefined):  # pylint: disable=too-few-public-methods
    """ Ignore failure on undef errors when rendering templates """
    def _fail_with_undefined_error(self, *args, **kwargs):
        return ''

    __add__ = __radd__ = __mul__ = __rmul__ = __div__ = __rdiv__ = \
        __truediv__ = __rtruediv__ = __floordiv__ = __rfloordiv__ = \
        __mod__ = __rmod__ = __pos__ = __neg__ = __call__ = \
        __getitem__ = __lt__ = __le__ = __gt__ = __ge__ = __int__ = \
        __float__ = __complex__ = __pow__ = __rpow__ = \
        _fail_with_undefined_error


def get_ansible_filters():
    """ Get Filters from ansible for testing validity of filters """
    ansible_filters = dict()
    try:
        from ansible.plugins import filter_loader
    except ImportError:
        try:
            from ansible.plugins.loader import filter_loader
        except ImportError:
            pass

    plugins = [x for x in filter_loader.all()]
    for plugin in plugins:
        ansible_filters.update(plugin.filters())

    return ansible_filters


def process_templates(templates):
    template_data = {}
    for template in templates:
        with open(template) as tmp:
            template_data[template] = tmp.read()

    loader = DictLoader(template_data)
    env = Environment(loader=loader, undefined=SilentUndefined)
    ansible_filters = get_ansible_filters()

    for k, val in ansible_filters.items():
        env.filters[k] = val

    ret = 0
    for template in env.list_templates():
        try:
            tmpl = env.get_template(template)
            # env.parse(template_data[template])
            tmpl.render()
        except (TemplateAssertionError, TemplateSyntaxError) as exc:
            print("FAILED: %s in (%s) on line %s." % (exc,
                                                      template,
                                                      exc.lineno))
            ret = 1
        except UndefinedError as exc:
            print("Undef! %s in %s" % (exc, template))
            ret = 1
            # this needs to just pass as we're not inheriting ansible vars,
            # but if this triggers with SilentUndefined above, we should know
        except TypeError as exc:
            pass
        except TemplateNotFound as exc:
            # This seems to fire from inheritence, but due to the way we grab
            # templates, we should know the templates exist because we read
            # them from the OS.
            # print "Template not found: %s" % exc
            pass
    return ret

def main():
    """ Check Templates in provided path """
    if len(sys.argv) < 2:
        print("Please provide a path for testing")
        exit(1)

    if str(sys.argv[1]).startswith('/'):
        path = sys.argv[1]
    elif str(sys.argv[1]) == '.':
        path = os.getcwd()
    elif os.path.isfile(sys.argv[1]):
        path = os.path.abspath(sys.argv[1])
    else:
        path = '%s/%s' % (os.getcwd(), sys.argv[1])

    if not os.path.isdir(path) and not os.path.isfile(path):
        print("Provided arg (%s) is not a file or directory." % sys.argv[1])
        exit(1)

    templates = []

    if os.path.isdir(path):
        for i in os.walk(path):
            for fname in i[2]:
                if fname.endswith('.j2'):
                    templates.append('%s/%s' % (i[0], fname))
    else:
        templates.append(path)

    ret = process_templates(templates)

    exit(ret)


if __name__ == "__main__":
    main()
