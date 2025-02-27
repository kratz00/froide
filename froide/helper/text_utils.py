import re
from html.entities import name2codepoint

from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags
from django.conf import settings

try:
    from lxml import html as html_parser
except ImportError:
    html_parser = None


SEPARATORS = re.compile(r'(\s*-{5}\w+ \w+-{5}\s*|^--\s*$)', re.UNICODE | re.M)


def unescape(text):
    '''
    From http://effbot.org/zone/re-sub.htm#unescape-html
    Removes HTML or XML character references and entities from a text string.

    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    '''
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub(r'&#?\w+;', fixup, text)


def split_text_by_separator(text, separator=None):
    if separator is None:
        separator = SEPARATORS
    split_text = separator.split(text)
    if len(split_text) == 1:
        split_text.append('')
    if len(split_text) > 2:
        split_text = [split_text[0], '\n'.join(split_text[1:])]
    return split_text


def redact_subject(content, user=None):
    if user:
        account_service = user.get_account_service()
        content = account_service.apply_message_redaction(content)
    content = redact_content(content)
    return content[:255]


def redact_plaintext(content, is_response=True, user=None):
    content = redact_content(content)

    greeting_replacement = str(_("<< Greeting >>"))

    if not settings.FROIDE_CONFIG.get('public_body_officials_public'):
        if is_response:
            content = remove_closing(
                content
            )
        else:
            greetings = settings.FROIDE_CONFIG.get('greetings')
            if greetings:
                content = replace_custom(
                    greetings,
                    greeting_replacement,
                    content
                )

    if user:
        account_service = user.get_account_service()
        content = account_service.apply_message_redaction(content)

    return content


def redact_content(content):
    content = replace_email_name(content, _("<<name and email address>>"))
    content = replace_email(content, _("<<email address>>"))

    if settings.FROIDE_CONFIG.get('custom_replacements'):
        content = replace_custom(settings.FROIDE_CONFIG['custom_replacements'],
            str(_('<<removed>>')), content)
    return content


def replace_word(needle, replacement, content):
    return re.sub(r'(^|[\W_])%s($|[\W_])' % re.escape(needle),
                    '\\1%s\\2' % replacement, content, re.U)


EMAIL = r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'
EMAIL_RE = re.compile(EMAIL, flags=re.IGNORECASE)
EMAIL_NAME_RE = re.compile('<%s>' % EMAIL, flags=re.IGNORECASE)


def replace_email_name(text, replacement=""):
    return EMAIL_NAME_RE.sub(str(replacement), text)


def replace_email(text, replacement=""):
    return EMAIL_RE.sub(str(replacement), text)


def find_all_emails(text):
    return EMAIL_RE.findall(text)


def replace_custom(regex_list, replacement, content):
    for regex in regex_list:
        match = regex.search(content)
        if match is not None and len(match.groups()):
            content = content.replace(match.group(1),
                replacement)
    return content


def remove_part(regexes, content, func=None):
    for regex in regexes:
        match = regex.search(content)
        if match is not None:
            content = func(content, match)
            break
    return content


def remove_closing(content, regexes=None):
    if regexes is None:
        regexes = settings.FROIDE_CONFIG.get('closings', [])
    return remove_part(regexes, content, func=lambda c, m: c[:m.end()].strip())


def remove_closing_inclusive(content):
    regexes = settings.FROIDE_CONFIG.get('closings', [])
    return remove_part(regexes, content, func=lambda c, m: c[:m.start()].strip())


def remove_greeting_inclusive(content):
    regexes = settings.FROIDE_CONFIG.get('greetings', [])
    return remove_part(regexes, content, func=lambda c, m: c[m.end():].strip())


def make_strong(x):
    return '**%s**' % x.text_content()


def make_italic(x):
    return '*%s*' % x.text_content()


def make_link(x):
    return '[%s](%s)%s' % (
        x.text_content(),
        x.attrib.get('href', ''),
        x.tail if x.tail else ''
    )


def make_paragraph(el):
    el.append(html_parser.Element("br"))
    convert_element(el)


HTML_CONVERTERS = {
    'a': make_link,
    'strong': make_strong,
    'b': make_strong,
    'i': make_italic,
    'em': make_italic,
    'p': make_paragraph,
    'br': lambda x: '\n%s' % (x.tail if x.tail else ''),
}

HTML_GARBAGE = ('style',)


def convert_html_to_text(html_str):
    """
    If lxml is available, convert to Markdown (but badly)
    otherwise just strip_tags
    """
    if html_parser is None:
        return strip_tags(html_str)

    root = html_parser.fromstring(html_str)
    try:
        body = root.xpath('./body')[0]
    except IndexError:
        # No body element
        body = root

    for tag in HTML_GARBAGE:
        els = body.xpath('.//' + tag)
        for el in els:
            el.getparent().remove(el)

    convert_element(body)

    text = html_parser.tostring(
        body,
        pretty_print=True,
        method='text',
        encoding='utf-8'
    ).decode('utf-8')

    return '\n'.join(x.strip() for x in text.splitlines()).strip()


def convert_element(root_element):
    for tag, func in HTML_CONVERTERS.items():
        els = root_element.xpath('.//' + tag)
        for el in els:
            replacement = func(el)
            if replacement is not None:
                repl_tag = html_parser.Element("span")
                repl_tag.text = replacement
                el.getparent().replace(el, repl_tag)
