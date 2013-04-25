#!/usr/bin/env python

import os
import re
import sys
import imp
from collections import defaultdict

class Finder:
    full_rx = {
            'normal': re.compile(r'(^|\n|:)\s*import ([\w.]+)'),
            'from': re.compile(r'(^|\n|:)\s*from ([\w.]+)')
    }
    one_rx = {
            'normal': re.compile(r'(^|\n|:)\s*import (\w+)'),
            'from': re.compile(r'(^|\n|:)\s*from (\w+)')
    }
    def __init__(self, config):
        self.config = defaultdict(bool)
        self.config.update(config)
        self.imports = defaultdict(set)

    def main(self, basedir):
        self.base = basedir
        for dirpath, dirnames, filenames in os.walk(basedir):
            print '.',
            sys.stdout.flush()
            if self.config['check-init'] and '__init__.py' not in filenames:
                continue
            for fname in filenames:
                if fname.endswith('.py'):
                    self.process(dirpath, fname)
        print

    def process(self, dirpath, filename):
        full = os.path.join(dirpath, filename)
        text = open(full).read()
        if self.config['full']:
            rx = self.full_rx
        else:
            rx = self.one_rx
        normals = rx['normal'].findall(text)
        fromis = rx['from'].findall(text)
        for _, modname in normals + fromis:
            self.imports[modname].add(full)

    def get_modules(self):
        bases = {}
        for modname, files in self.imports.iteritems():
            parts = modname.split('.')
            base = parts[0]
            rest = '.'.join(parts[1:])
            if base not in bases:
                bases[base] = [self.find_module(base, files)]
            bases[base].append([rest] + list(files))
        return bases

    def display(self, modules):
        groups = {'built-in':[], 'mine':[], 'other':[]}
        for name, items in modules.iteritems():
            where = items[0]
            if where[1].startswith(self.base):
                groups['mine'].append((name, items))
            elif where[1].startswith('/usr/'):
                groups['built-in'].append((name, items))
            else:
                groups['other'].append((name, items))
        for group in ('built-in', 'mine', 'other'):
            print 'GROUP ', group
            for name, items in sorted(groups[group]):
                where = items[0]
                #if where[1].startswith('/usr/lib'):
                    #where = (None, '<built-in>', None)
                main = '\t%s\t:: [%d] from %d files :: %s' % (name.ljust(20),
                        len(items[2:]),
                        sum(len(sub[1:]) for sub in items[1:]),
                        where[1])
                print main
                if self.config['show-files'] > 0:
                    for fname in items[1][1:self.config['show-files']+1]:
                        print '\t\t', fname
                if self.config['show-subs']:
                    for submod in items[2:]:
                        print '\t\t> %s' % submod[0]
                        if self.config['show-files']:
                            for fname in submod[1:self.config['show-files']+1]:
                                print '\t\t\t', fname

    def find_module(self, base, fromfiles):
        # print 'looking for', base, fromfiles
        try:
            return imp.find_module(base)
        except ImportError:
            pass
        for fname in fromfiles:
            path = os.path.dirname(fname)
            # print 'finding', base, self.base, path
            try:
                return imp.find_module(base, [self.base, path])
            except ImportError:
                continue
        return [None, '', None]
        # raise Exception("Can't find the module %s, referenced by %s" % (base, fromfiles))

if __name__ == '__main__':
    if len(sys.argv)<2:
        print 'Usage: find.py [dir-name]'
        sys.exit(2)
    c = {}
    c['full'] = True
    c['show-files'] = 1
    f = Finder(c)
    f.main(sys.argv[1])
    mods = f.get_modules()
    f.display(mods)

# vim: et sw=4 sts=4
