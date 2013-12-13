#!/usr/bin/env python 

# python
import os
import glob
import sys

input_path=os.getcwd()

if len(sys.argv) > 1 :
	input_file=sys.argv[1]
	infile = os.path.join(input_path, input_file)
	f= open(infile, 'rb') 
	content= unicode(f.read(), 'gb18030') 
	f.close() 
	f= open(infile, 'wb') 
	f.write(content.encode('utf-8')) 
	f.close()
else:
	for infile in glob.glob(os.path.join(input_path, '*.txt')):
		f= open(infile, 'rb') 
		content= unicode(f.read(), 'gb18030') 
		f.close() 
		f= open(infile, 'wb') 
		f.write(content.encode('utf-8')) 
		f.close()
