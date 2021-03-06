# markdown-pygments.py
#!/usr/bin/env python 
import sys
import os
import markdown

def main(args=None):
    if (args is None or len(args) < 2):
        print "Error, input file missing, usage:"
        print "  markdown-pygments.py <markdown formatted file>"
        return

    markdownInFile = os.path.abspath(args[1])

    (dir, file) = os.path.split(markdownInFile)
    (file, ext) = os.path.splitext(file)
    markdownOutFile = os.path.join(dir, ".".join([file,'html']))

    print "in:  ", markdownInFile
    print "out: ", markdownOutFile

    with open(markdownInFile, 'r') as f: text = f.read()
    html = markdown.markdown(text, ['codehilite'])
    with open(markdownOutFile, 'w') as f: f.write(html)

if __name__ == '__main__':
    main(sys.argv)