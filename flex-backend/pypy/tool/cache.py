"""
Caches that can freeze when the annotator needs it.
"""

#
# _freeze_() protocol:
#     user-defined classes can define a method _freeze_(), which
#     is called when a prebuilt instance is found.  If the method
#     returns True, the instance is considered immutable and becomes
#     a SomePBC().  Otherwise it's just SomeInstance().  The method
#     should force away any laziness that remains in the instance.
#
# Cache class:
#     a cache meant to map a finite number of keys to values.
#     It is normally extended lazily, until it contains all possible
#     keys.  The _annspecialcase_ attribute of the getorbuild() method
#     forces the annotator to decode the argument's annotations,
#     which must be constants or SomePBCs, actually call the
#     method with all possible combinations, and gather the results.
#     The idea is to completely fill the cache at annotation-time,
#     using the information collected by the annotator itself about
#     what the keys can actually be.
#
#     Cache must be subclassed, and a _build() method provided.
#     Be sure to call the parent __init__() if you override it.
#


class Cache(object):
    def __init__(self):
        self.content = {}
        self._building = {}

    def getorbuild(self, key):
        try:
            return self.content[key]
        except KeyError:
            if key in self._building:
                raise Exception, "%s recursive building of %r" % (
                    self, key)
            self._building[key] = True
            try:
                result = self._build(key)
                self.content[key] = result
            finally:
                del self._building[key]
            self._ready(result)
            return result
    getorbuild._annspecialcase_ = "specialize:memo"

    def _ready(self, result):
        pass

    def _freeze_(self):
        # needs to be SomePBC, but otherwise we can't really freeze the
        # cache because more getorbuild() calls might be discovered later
        # during annotation.
        return True
