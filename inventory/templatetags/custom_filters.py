import logging

from django import template

logger = logging.getLogger("inventory")

register = template.Library()

# The longest HTML tag I expect to find in fieldnote.note
MAX_TAG_LENGTH = 9


@register.filter
def get_field_display(obj, field_name):
    """Custom filter to access dynamic attributes"""
    text = getattr(obj, field_name, "")
    if field_name == "display_summary":
        # strip HTML from fieldnote.note when there is no .summary
        text = generate_summary(text)
    return text


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")


@register.filter
def generate_summary(text, max_chars=200):
    """Custom filter to strip HTML tags from a text string.

    Truncates the summary to length max_chars"""
    text = text.split("<br>")[0]
    i = text.find("<")
    while True:
        if i < 0:
            # No more possible tags to excise
            break
        # tags can have attributes after a space, before the closing >
        j_bracket = text.find(">", i)
        j_space = text.find(" ", i)
        j = min(j_bracket, len(text) if j_space < 0 else j_space)
        # HTML tags will typically not be longer than MAX_TAG_LENGTH chars
        if j - i <= MAX_TAG_LENGTH:
            # Excise this tag
            text = text[:i] + text[j_bracket + 1 :]
            i = text.find("<")
        else:
            # Log a warning if we find someting longer.
            logger.warning(
                f"Unexpectedly long tag: {text[i: j + 1]}, length: {j - i} expected max: {MAX_TAG_LENGTH}"
            )
            i = text.find("<", i + 1)
    return text[:max_chars]
