from django import template
from django.utils.html import escape
from django.utils.text import normalize_newlines
from django.utils.safestring import SafeData, mark_safe


register = template.Library()


@register.filter(is_safe=True, needs_autoescape=True)
def markup(value, autoescape=True):
    """
    Markup the strings:
    "h. Text" becomes <h5>Text</h5>
    "(Text)" becomes (<span class="text-muted">Text</span>)
    "rem. Text" becomes <span class="text-muted">Text</span>
    Слава и ныне becomes red
    Convert all newlines in a piece of plain text to HTML line breaks
    (``<br>``).
    """
    autoescape = autoescape and not isinstance(value, SafeData)
    value = normalize_newlines(value)
    if autoescape:
        value = escape(value)

    lines = []
    for line in value.split("\n"):
        _line = line.strip()

        if "(" in _line:
            _line = _line.replace("(", '(<span class="text-muted">')
        if ")" in _line:
            _line = _line.replace(")", '</span>)')

        if _line.startswith("h."):
            _line = "<h5>{}</h5>".format(_line[2:])
        elif _line.startswith("rem."):
            _line = '<span class="text-muted">{}</span>'.format(_line[4:])
        elif _line.startswith("Слава, и ныне"):
            _line = _line.replace("Слава, и ныне", '<span class="text-danger">Слава, и ныне</span>')
        elif _line.startswith("Слава"):
            _line = _line.replace("Слава", '<span class="text-danger">Слава</span>')
        elif _line.startswith("И ныне"):
            _line = _line.replace("И ныне", '<span class="text-danger">И ныне</span>')

        lines.append(_line)
    return mark_safe("<br/>".join(lines))

