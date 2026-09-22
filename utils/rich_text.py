from telegram import MessageEntity

# Sentinel marking where genuinely dynamic content (a user's own Telegram
# first name) gets inserted into a *_PARTS list - see build_bold_message.
DYNAMIC = object()


def build_bold_message(parts):
    """
    Builds a (text, entities) pair from an ordered list of (segment, bold)
    tuples, computing each bold entity's offset/length in UTF-16 code
    units - the unit Telegram's own MessageEntity offsets use, NOT Python
    character count (an emoji outside the Basic Multilingual Plane, like
    most of the ones used in this bot's messages, is 1 Python character
    but 2 UTF-16 code units, so len() would silently misplace every
    entity after the first emoji).

    This exists specifically so a message can safely mix real bold
    formatting with genuinely unpredictable content (a user's Telegram
    first name, which can contain literal *, _, or other characters a
    Markdown parser would treat as syntax). Markdown/MarkdownV2 parse the
    whole string for syntax characters, so one stray character in
    dynamic content can corrupt or fail the entire message - entities
    sidestep that failure mode entirely, since bold spans are declared
    structurally (by position) rather than by scanning the text for
    markup. Dynamic segments are simply never wrapped in a bold entity,
    so nothing in them can affect formatting elsewhere in the message,
    no matter what characters they contain.
    """

    text = ""
    entities = []
    offset = 0

    for segment, bold in parts:
        length = len(segment.encode("utf-16-le")) // 2
        if bold:
            entities.append(MessageEntity(type=MessageEntity.BOLD, offset=offset, length=length))
        text += segment
        offset += length

    return text, entities


def resolve_parts(parts, dynamic_value):
    """Substitutes the DYNAMIC sentinel with the real value (e.g. first_name)."""
    return [(dynamic_value if segment is DYNAMIC else segment, bold) for segment, bold in parts]
