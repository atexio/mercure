import os
import pypandoc
import shutil


CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(CURRENT_PATH, 'docs')
README_PATH = os.path.join(CURRENT_PATH, 'README.md')
README_DOC_PATH = os.path.join(DOC_PATH, 'readme')


def save_part(lines):
    """save last part on rst file"""
    # has content ?
    if len(lines) > 2:
        # get path
        title = lines[0].replace(' ', '_')
        path = os.path.join(README_DOC_PATH, '%s.rst' % title)

        # get content
        content = '\n'.join(lines[:-2])
        content = content.replace('docs/img/', ' ../img/')
        print(content)

        # save
        pypandoc.convert_text(content, 'rst', format='md', outputfile=path)

    # flush last part
    return lines[-2:]


# create directory
if os.path.exists(README_DOC_PATH):
    shutil.rmtree(README_DOC_PATH)
if not os.path.exists(README_DOC_PATH):
    os.mkdir(README_DOC_PATH)


# convert README.md into rst format and read lines
lines = []
for line in pypandoc.convert(README_PATH, 'md').split('\n'):
    lines.append(line)

    # save part on h1 line
    if '=' in line and not line.replace('=', ''):
        lines = save_part(lines)


# end on file: save last part
save_part(lines)
os.system('cd %s && make html' % DOC_PATH)
