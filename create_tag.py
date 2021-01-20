import os
import re


def read_version():
    with open(os.path.join('freezegun', '__init__.py')) as f:
        m = re.search(r'''__version__\s*=\s*['"]([^'"]*)['"]''', f.read())
        if m:
            return m.group(1)
        raise ValueError("couldn't find version")


def create_tag():
    from subprocess import call
    version = read_version()
    errno = call(['git', 'tag', '--annotate', version, '--message', 'Version %s' % version])
    if errno == 0:
        print("Added tag for version %s" % version)


if __name__ == '__main__':
    create_tag()
