from .add_path import add_path

with add_path(__file__, "..", "deps"):
    from .commands import *
