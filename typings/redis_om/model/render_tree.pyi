"""
This type stub file was generated by pyright.
"""

"""
This code adapted from the library "pptree," Copyright (c) 2017 Clément Michard
and released under the MIT license: https://github.com/clemtoy/pptree
"""
def render_tree(current_node, nameattr=..., left_child=..., right_child=..., indent=..., last=..., buffer=...): # -> str:
    """Print a tree-like structure, `current_node`.

    This is a mostly-direct-copy of the print_tree() function from the ppbtree
    module of the pptree library, but instead of printing to standard out, we
    write to a StringIO buffer, then use that buffer to accumulate written lines
    during recursive calls to render_tree().
    """
    ...

