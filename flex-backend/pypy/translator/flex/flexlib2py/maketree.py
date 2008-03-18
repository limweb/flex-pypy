#!/usr/bin/env python

from __future__ import with_statement
import subprocess
import os
import os.path
import re
import sys
import operator as op
import string
import logging



__doc__ = """
Program to convert an intermediate text format that contains the package names,
classes and function/attribute declarations for the entire Flex/Flash 
ActionScript Library. The information used to generate this intermediate file
is extracted from the HTML documents of the online libraries.

Usage:
    maketree INPUT_FILE OUTPUT_DIRECTORY

Sample format of input file:

    p: package1.name
    c: ClassName1
    i: ../../flash.net.SuperClass
    i: ../../flash.net.SuperSuperClass1
    a: attribute1:Boolean
    a: attribute1:Boolean
    k: public static const CONSTVAL1:String = "binary"
    f: public function InstanceFunction1():Boolean
    f: protected function InstanceFunction2():void
    f: public static function StaticFunction1(arg1:Object):void
    c: ClassName1
    ...
    p: package2.name
    c: ClassName3
    ...
"""



class chdir:
    """
    Implementation of "with chdir(path):" statement.
    """
    def __init__(self, dirpath):
        self.dirpath = dirpath
    
    def __enter__(self):
        self.old = os.getcwd()
        os.chdir(self.dirpath)
    
    def __exit__(self, type, value, tb):
        os.chdir(self.old)



def mkdir_ensure(path, isModule=False):
    """
    Ensure that a certain directory path exists.
    
    If the isModule argument is True, it wil create a __init__.py file inside the
    directory.
    """
    subprocess.call(['mkdir', '-p', path])
    init_file = os.path.join(path, '__init__.py')
    if isModule and not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write('# automatically generated #\n')


def builtin_types_as2py(type_as):
    """
    Convert a builtin ActionScript 3 type into a native python equivalent.
    """
    d = {
        'String': 'str',
        'Object': 'object',
        'uint':   'long',
        'Number': 'float',
        'Boolean': 'bool',
        'Array':  'list',
        'void': 'None', 
    }
    if d.has_key(type_as):
        return d[type_as]
    return type_as

def _type_as2py(typ):
    typ = typ or 'str'
    typ = builtin_types_as2py(typ)
    if typ in ['object', 'Function', 'void', '*', '**']:
        typ = 'str'
        return True, typ
    return False, typ


class AS3Tree(object):
    """
    Represents an entire ActionScript 3 library.
    """
    
    def __init__(self):
        self.packages = dict()

    def addPackage(self, pack):
        self.packages[pack.name] = pack
        
    def to_py(self, path):
        mkdir_ensure(path)
        os.chdir(path)
        for name, pack in self.packages.items():
            pack.to_py()


class AS3Package(object):
    """
    Represents an ActionScript 3 package.
    """
    
    def __init__(self, name):
        self.name = name
        self.classes = dict()
    
    def addClass(self, clas):
        """
        Add a class to the package.
        """
        self.classes[clas.name] = clas


    def _inheritanceTreeToList(self, class_name, d):
        """
        Recursive aux function to convert a inheritance tree to a list that 
        is ordered to comply with class dependencies.
        """
        result = []
        if d.has_key(class_name):
            for subclass in d[class_name]:
                assert type(subclass) is AS3Class
                result.append(subclass)
                result.extend(self._inheritanceTreeToList(subclass.name, d))
        return result


    def _orderClassesByInheritance(self):
        """
        Return this package's class objects ordered to comply with class dependencies.
        """
        d = {}
        for name, clas in self.classes.items():
            i = clas.inheritance
            
            if not i or i == 'Error' or i.find('.') >= 0:
               i = 'Object'
               
            if d.has_key(i):
                d[i].append(clas)
            else:
                d[i] = [clas]

        result = self._inheritanceTreeToList('Object', d)
        assert len(result) == len(self.classes)
        return result

    
    def to_py(self):
        classes = self._orderClassesByInheritance()
        assert self.name
        pth = self.name.replace('.', '/')
        pth, fil = pth.rsplit('/', 1)
        mkdir_ensure(pth, isModule=True)
        
        with chdir(pth):
            s = ''
            imps = set()
            for clas in classes:
                i = clas.to_py_inherit_module()
                if i:
                    imps.add(i)
                s += clas.to_py()
        
            with open(fil + '.py', 'w') as fd:
                for i in imps:
                    fd.write("import %s\n" % i)
                fd.write(s)
    

class AS3Class(object):
    """
    Represents an ActionScript 3 class.
    """
    
    def __init__(self, parent=None, name=None, package=None):
        self.parent = parent
        self.name = name
        self.package = package
        self.functions = []
        self.constants = []
        self.attributes = []
        self.inheritance = None
        
    def addFunction(self, func):
        self.functions.append(func)
    
    def addConstant(self, cons):
        self.constants.append(cons)

    def addAttribute(self, attr):
        self.attributes.append(attr)
    
    def addInheritance(self, name):
        assert name
        if not self.inheritance:
            if name.startswith(self.parent.name):
                name = name[len(self.parent.name) + 1:]
            self.inheritance = name
    
    def to_py_inherit_module(self):
        i = self.to_py_inheritance()
        i = i.rstrip(string.ascii_letters).rstrip('.')
        return i
    
    def to_py_inheritance(self):
        if not self.inheritance:
            return 'object'
        return self.inheritance

    def to_py(self):
        """
        Generate a rpython class.
        """
        inherit = self.to_py_inheritance()
        inherit = builtin_types_as2py(inherit)
        if inherit == 'object':
            inherit = 'BasicExternal'
        
        self_path = "%s.%s" % (self.parent.name, self.name)
        s = "\nadd_import('%s')\n" % self_path
        s += "class %s(%s):\n" % (self.name, inherit)
        s += "    _render_class = '%s'\n" % self_path
        
        if not any((self.functions, self.attributes, self.constants)):
            s += '    pass\n'
        
        s += '    _fields = {\n'
        for attr in self.attributes:
            s += attr.to_py()
        s += '    }\n'
        
        for cons in self.constants:
            s += cons.to_py()

        s += '    _methods = {\n'
        for func in self.functions:
            s += func.to_py()
        s += '    }\n'
                
        return s


class AS3Constant(object):
    """
    Represents a constant attribute of an ActionScript 3 class.
    """

    def __init__(self, raw='', name='', typ='', val=''):
        self.raw = raw
        self.typ = typ
        self.name = name
        self.val = val

    def to_py(self):
        val = self.val or 'None'
        return "    %s = %s\n" % (self.name, val)


class AS3Attribute(object):
    """
    Represents an attribute of an ActionScript 3 class.
    """
    
    def __init__(self, raw='', name='', typ=''):
        self.raw = raw
        self.name = name
        self.typ = typ
        
    def to_py(self):
        isSpecial, typ = _type_as2py(self.typ)
        return "        '%s': %s,\n" % (self.name, typ or 'None')


class AS3Function(object):
    """
    Represents an instance/class function of a ActionScript 3 class.
    """
    
    def __init__(self, parent=None, raw='', name='', typ='', args=[], isStatic=False):
        self.parent = parent
        self.raw = raw
        assert typ, raw
        self.typ = typ
        self.name = name
        self.args = args
        self.isStatic = isStatic

    def to_py(self):
        s = ''
        name = self.name

        if name == self.parent.name:
            # __init__()
            return ''

        if self.isStatic:
            # TODO
            return ''
        
        args = ""
        for arg in self.args:
            todo = ''
            isSpecialCase, typ = _type_as2py(arg.typ)
            if isSpecialCase:
                todo = ' # Fix This (type %s)' % arg.typ
            args += '\n            ' + typ + ',' + todo

        isSpecialCase, typ = _type_as2py(self.typ)
        s += "        '%s': MethodDesc([%s\n        ], %s),\n\n" % (name, args, typ)
        return s
        


class AS3FunctionArgument(object):
    """
    Represents a function argument belonging to an ActionScript 3 class.
    """


    def __init__(self, raw='', name='', typ='', value='', isEllipsis=False):
        self.raw = raw
        self.name = name
        self.typ = typ
        self.value = value
        self.isEllipsis = isEllipsis
    
    def __repr__(self):
        return '<%s: %s >' % (self.__class__.__name__, self.raw)
        
    def to_py(self):
        return self.name #+ ':' + str(builtin_types_as2py(self.typ))



class Parser(object):
    
    def __init__(self):
        self.tree = AS3Tree()
        self.last_p = None
        self.last_c = None
    
    def _package(self, s):
        p = AS3Package(name=s)
        self.tree.addPackage(p)
        self.last_p = p
        self.last_c = None
    
    def _class(self, s):
        c = AS3Class(name=s, package=self.last_p, parent=self.last_p)
        self.last_p.addClass(c)
        self.last_c = c
    
    _re_function_arg = re.compile(r'^\s*(?P<ellipsis>\.{3})?\s*(?P<name>\w+)\s*(:\s*(?P<typ>[\w*]+))?\s*(=\s*(?P<val>.*))?\s*$')
    def _function_arg(self, raw):
        """
        Parses a function argument, returns an AS3FunctionArgument object.
        """
        m = Parser._re_function_arg.search(raw)
        if not m:
            logging.warn('Function argument not valid: %s' % raw)
            return False
        d = m.groupdict()
        arg = AS3FunctionArgument(raw=raw, name=d['name'], isEllipsis=bool(d['ellipsis']), typ=d['typ'])
        return arg
    
    
    def _function_parse(self, raw):
        """
        Parse the raw value of an f: line.
        """
        l, r = raw.split(' function ', 1)
        isStatic = l.find('static') >= 0
        name, args, typ = re.split('[()]', r, 2)
        typ = typ.rsplit(':', 1)
        if typ:
            typ = typ[-1].strip()
        args = filter(len, re.split('\s*,\s*', args))
        resu = []
        for arg in args:
            arg = self._function_arg(arg)
            if arg:
                resu.append(arg)
            else:
                logging.error("Could not parse a function of %s.%s: %s" % 
                    (self.last_p.name, self.last_c.name, raw))
                break
        return name, resu, typ, isStatic
    
    
    def _function(self, raw):
        """
        Takes the raw value of an f: line, adds an AS3Function object to the current class.
        """
        name, args, typ, isStatic = self._function_parse(raw)
        f = AS3Function(parent=self.last_c, raw=raw, name=name, args=args, typ=typ, isStatic=isStatic)
        self.last_c.addFunction(f)


    def _inherit(self, raw):
        """
        Get the superclass of the current class.
        """
        assert raw
        self.last_c.addInheritance(raw)
        if not self.last_c.inheritance:
            del self.last_p.classes[self.last_c.name]
            name = self.last_p.name + '.' + self.last_c.name
            logging.warning("Class %s has no superclass: will be ignored." % name)


    def _attribute(self, raw):
        """
        Takes the raw value of an a: line, returns an AS3Attribute object.
        """
        name, typ = re.split('\s*:\s*', raw.strip())
        name = name.rstrip().split(" ")[-1]
        a = AS3Attribute(raw=raw, name=name, typ=typ)
        self.last_c.addAttribute(a)


    _re_constant = re.compile(r'(?P<name>\w+)\s*:\s*(?P<typ>[\w\*]+)\s*(=\s*(?P<val>.*))?')
    def _constant(self, raw):
        """
        Parse the raw value of a k: line.
        """
        m = Parser._re_constant.search(raw)
        assert m, "Could not parse const attribute:\n\t%s" % raw
        if m:
            d = m.groupdict()
            name = d['name']
            typ = d['typ']
            val = d['val']
            k = AS3Constant(raw=raw, name=name, typ=typ, val=val)
            self.last_c.addConstant(k)


    def _line(self, line):
        """
        Process one line. Ignore lines with unknown prefixes.
        """
        c, s = line[:3], line[3:].rstrip()
        if   c == 'p: ': self._package(s)
        elif c == 'c: ': self._class(s)
        elif c == 'f: ': self._function(s)
        elif c == 'a: ': self._attribute(s)
        elif c == 'k: ': self._constant(s)
        elif c == 'i: ': self._inherit(s)


    def parse(self, filename):
        """
        Takes the filename of the intermediate dump file, returns an AS3Tree object.
        """
        for line in open(filename, 'r'):
            self._line(line)
        return self.tree


filename, dirname = sys.argv[1:3]
parser = Parser()
tree = parser.parse(filename)
tree.to_py(os.path.abspath(dirname))
