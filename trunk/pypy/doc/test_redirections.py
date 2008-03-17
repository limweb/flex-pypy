
import py 
from pypy.doc.conftest import option
redir = py.magic.autopath().dirpath('redirections') 

def checkexist(path):
    print "checking", path
    assert path.ext == '.html'
    assert path.new(ext='.txt').check(file=1) 

def checkredirection(oldname, newname):
    print "checking", newname
    newpath = redir.dirpath(newname.split('#')[0])
    checkexist(newpath)
    # HACK: create the redirecting HTML file here...
    # XXX obscure fishing
    if option.generateredirections and '#' not in oldname:
        generate_redirection(oldname, newname)

def test_eval(): 
    d = eval(redir.read(mode='r')) 
    return d

def test_redirections(): 
    d = test_eval() 
    for oldname, newname in d.items():
        yield checkredirection, oldname, newname

def test_navlist(): 
    navlist = eval(redir.dirpath('navlist').read())
    for entry in navlist:
        yield checkexist, redir.dirpath(entry)

# ____________________________________________________________

def generate_redirection(oldname, newname):
    print "redirecting from", oldname
    oldpath = redir.dirpath(oldname)
    url = newname    # relative URL
    oldpath.write("""<html>
    <head>
        <meta http-equiv="refresh"
              content="2 ; URL=%s" />
        <META HTTP-EQUIV="CACHE-CONTROL" CONTENT="NO-CACHE">
        <META HTTP-EQUIV="expires" CONTENT="0">
    </head>
    <body>
        <p>
            you should be redirected to
            <a href="%s">%s</a>
        </p>
    </body>
</html>
""" % (url, url, url))
