from pypy.interpreter.mixedmodule import MixedModule
    
class Module(MixedModule):
    appleveldefs = {
         '__doc__' :  'app_codecs.__doc__',
         '__name__' :  'app_codecs.__name__',
         'ascii_decode' :  'app_codecs.ascii_decode',
         'ascii_encode' :  'app_codecs.ascii_encode',
         'charbuffer_encode' :  'app_codecs.charbuffer_encode',
         'charmap_decode' :  'app_codecs.charmap_decode',
         'charmap_encode' :  'app_codecs.charmap_encode',
         'escape_decode' :  'app_codecs.escape_decode',
         'escape_encode' :  'app_codecs.escape_encode',
         'latin_1_decode' :  'app_codecs.latin_1_decode',
         'latin_1_encode' :  'app_codecs.latin_1_encode',
         'lookup' :  'app_codecs.lookup',
         'lookup_error' :  'app_codecs.lookup_error',
         'mbcs_decode' :  'app_codecs.mbcs_decode',
         'mbcs_encode' :  'app_codecs.mbcs_encode',
         'raw_unicode_escape_decode' :  'app_codecs.raw_unicode_escape_decode',
         'raw_unicode_escape_encode' :  'app_codecs.raw_unicode_escape_encode',
         'readbuffer_encode' :  'app_codecs.readbuffer_encode',
         'register' :  'app_codecs.register',
         'register_error' :  'app_codecs.register_error',
         'unicode_escape_decode' :  'app_codecs.unicode_escape_decode',
         'unicode_escape_encode' :  'app_codecs.unicode_escape_encode',
         'unicode_internal_decode' :  'app_codecs.unicode_internal_decode',
         'unicode_internal_encode' :  'app_codecs.unicode_internal_encode',
         'utf_16_be_decode' :  'app_codecs.utf_16_be_decode',
         'utf_16_be_encode' :  'app_codecs.utf_16_be_encode',
         'utf_16_decode' :  'app_codecs.utf_16_decode',
         'utf_16_encode' :  'app_codecs.utf_16_encode',
         'utf_16_ex_decode' :  'app_codecs.utf_16_ex_decode',
         'utf_16_le_decode' :  'app_codecs.utf_16_le_decode',
         'utf_16_le_encode' :  'app_codecs.utf_16_le_encode',
         'utf_7_decode' :  'app_codecs.utf_7_decode',
         'utf_7_encode' :  'app_codecs.utf_7_encode',
         'utf_8_decode' :  'app_codecs.utf_8_decode',
         'utf_8_encode' :  'app_codecs.utf_8_encode',
         'encode': 'app_codecs.encode',
         'decode': 'app_codecs.decode'
    }
    interpleveldefs = {
    }
