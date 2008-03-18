import os
def cmd(c):
    print c
    if os.system(c): raise RuntimeError

def main():
    try:
        cmd('./py2flex.sh')
        cmd('~/flex/bin/mxmlc -warnings=false  output.mxml')
        cmd('firefox ./output.swf')
    except:
        pass
if __name__=='__main__': main()
