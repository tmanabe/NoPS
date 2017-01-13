#!/usr/bin/env python
# coding: utf-8

from NoPS import NoPS
from glob import glob
import os
from sys import argv
from urllib import request


if len(argv) != 3:
    print('Usage: python %s <html_dir|URL_list> target_dir' % argv[0])
    exit(1)

input_path = argv[1].rstrip('/')
target_dir = argv[2].rstrip('/')

if not os.path.isdir(target_dir):
    os.makedirs(target_dir)

if os.path.isdir(input_path):
    for pi in glob(os.path.join(input_path, '*.html')):
        filename = os.path.basename(pi)
        basename = filename.rsplit('.', 1)[0]
        po = os.path.join(target_dir, basename + '.json')
        if os.path.exists(po):
            print('Warning: File exists. Skipping. (File: %s)' % filename)
            continue
        nops = NoPS()
        with open(pi) as f:
            nops.feed(f.read())
        with open(po, 'w') as f:
            f.write(nops.dumps(filename))  # Base element is required.
else:
    i = 0
    with open(input_path) as fi:
        for url in fi:
            p = os.path.join(target_dir, '%i.json' % i)
            i += 1
            url = url.rstrip()
            if os.path.exists(p):
                print('Warning: File exists. Skipping. (URL: %s)' % url)
                continue
            nops = NoPS()
            nops.feed(request.urlopen(url).read().decode('utf-8'))
            with open(p, 'w') as fo:
                fo.write(nops.dumps(url))
