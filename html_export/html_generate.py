#!/usr/bin/env python3
import html
import json
import os
import sys

try:
    import dominate
    from dominate.tags import meta, style, div, p, button, script
except ImportError:
    print(
        'Module dominate not installed. Use \'pip install dominate\' for '
        'installation and try again.',
        file=sys.stderr,
    )
    sys.exit(1)


def _create_subgroup(key, elem):
    """
    Create collapsible group with either leaves or nested subgroups. Adds
    :class:`~dominate.tags.button` and :class:`~dominate.tags.div` elements

    :param str key: key of dict entry and title of group
    :param dict elem: dict with elements of the group
    """
    # create collapsible button with key
    button(key.title(), cls='accordion')
    # create panel with either another subgroup or key/value pairs as panel
    for ek, ev in elem.items():
        if isinstance(ev, dict):
            with div(cls='panel'):
                _create_subgroup(ek, ev)
        else:
            _create_leaf(ek, ev)


def _create_leaf(key, value):
    """
    Create leaf element with key/value.

    :param str key: key of dict entry and title of attribute
    :param value: value of dict entry
    """
    # create panel
    return div(p(r'<b>' + str(key) + r':</b> ' + str(value)), cls='panel')


def to_html(mstate):
    """
    Create a static HTML representation of a given machine state.

    :param mstate: machine state json as `string`
    :type mstate: `str` or `dict`
    :returns: str -- html representation of `mstate`
    """
    doc = dominate.document(title='MachineState')
    # parse JSON string if needed
    if isinstance(mstate, str):
        mstate = json.loads(mstate)

    # load CSS
    dir_path = os.path.dirname(__file__)
    with open(os.path.join(dir_path, 'style.css')) as f:
        style_cont = f.read()
    # load JS
    with open(os.path.join(dir_path, 'script.js')) as f:
        script_cont = f.read()

    # create head and insert CSS
    with doc.head:
        meta(name='viewport', content='width=device-width, initial-scale=1')
        style(style_cont)

    # create collapse/expand buttons
    with doc:
        button('Expand all', cls='option expandable')
        button('Collapse all', cls='option collapsible')
    # create list structure in body
    with doc:
        for k, v in mstate.items():
            if isinstance(v, dict):
                # subgroup
                with div():
                    _create_subgroup(k, v)
            else:
                # leaf element
                _create_leaf(k, v)
        # add JS logic
        script(script_cont)
    rendered_str = doc.render()
    # replace html escape chars before returning rendered string
    return html.unescape(rendered_str)
