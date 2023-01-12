import sys
from api.enemy import Enemy

# Helper functions
def str_to_class(classname):
    return getattr(sys.modules[__name__], classname)
