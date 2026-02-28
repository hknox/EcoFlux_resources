from django import template

register = template.Library()


@register.filter
def get_field_display(obj, field_name):
    """Custom filter to access dynamic attributes"""
    text = getattr(obj, field_name, "")
    if field_name == "display_summary":
        # strip HTML tags from fieldnote.note if there is no .summary
        text = generate_summary(text)
    return text


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, "")


@register.filter
def generate_summary(text, max_chars=200):
    """Custom filter to strip HTML tags from a text string.

    Truncates the summary to lenght max_chars"""
    text = text.split("<br>")[0]
    i = text.find("<")
    while True:
        if i == -1:
            # No more possible tags to excise
            break
        j = text.find(">")
        # HTML tags will typically not be longer than 9 chars
        if j - i <= 9:
            # Excise this tag
            text = text[:i] + text[j + 1 :]
            i = text.find("<")
        else:
            i = text.find("<", i + 1)
    return text[:max_chars]
