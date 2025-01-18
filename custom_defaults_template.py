from defaults import Defaults as base

##Custom defaults: allows overriding defaults.py. If maskeditor.py finds a file names "custom_defaults.py", 
# it will attmept to import the Defaults object from it instead of from defaults.py. Rename this file to custom_defaults.py
# and any overrides specified below will be propagated to the main program. see defaults.py for parameters and data typing


class Defaults(base):
    # defaultFG:str = "#40FF0000";
    # defaultBG:str = "#3500FF00";
    pass