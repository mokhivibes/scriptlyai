from telegram import MessageEntity

# Sentinel marking where genuinely dynamic content (a user's own Telegram
# first name) gets inserted into a *_PARTS list - see build_bold_message.
DYNAMIC = object()

# Style sentinel for build_bold_message: wraps a segment in a CODE entity
# (monospace, tap-to-copy in every Telegram client) instead of bold. Used
# for transcript/translation/summary text - genuinely unpredictable
# content that can't safely go through parse_mode="Markdown" (see
# build_bold_message's docstring), but still benefits from being
# monospaced so a tap copies it.
CODE = object()


def build_bold_message(parts):
    """
    Builds a (text, entities) pair from an ordered list of (segment, style)
    tuples, computing each entity's offset/length in UTF-16 code units -
    the unit Telegram's own MessageEntity offsets use, NOT Python
    character count (an emoji outside the Basic Multilingual Plane, like
    most of the ones used in this bot's messages, is 1 Python character
    but 2 UTF-16 code units, so len() would silently misplace every
    entity after the first emoji).

    `style` is one of:
      - False - plain text
      - True - wrapped in a bold entity
      - CODE (this module's sentinel) - wrapped in a monospace/code entity
      - a string - treated as a custom_emoji_id; `segment` should be a
        single placeholder emoji character (e.g. a plain Unicode emoji),
        which Telegram replaces with that custom emoji's artwork for
        clients that support it (falls back to the placeholder character
        otherwise, so the message degrades gracefully rather than
        breaking).

    This exists specifically so a message can safely mix real formatting
    with genuinely unpredictable content (a user's Telegram first name,
    which can contain literal *, _, or other characters a Markdown parser
    would treat as syntax). Markdown/MarkdownV2 parse the whole string
    for syntax characters, so one stray character in dynamic content can
    corrupt or fail the entire message - entities sidestep that failure
    mode entirely, since spans are declared structurally (by position)
    rather than by scanning the text for markup. Dynamic segments are
    simply never wrapped in an entity, so nothing in them can affect
    formatting elsewhere in the message, no matter what characters they
    contain.
    """

    text = ""
    entities = []
    offset = 0

    for segment, style in parts:
        length = len(segment.encode("utf-16-le")) // 2
        if style is True:
            entities.append(MessageEntity(type=MessageEntity.BOLD, offset=offset, length=length))
        elif style is CODE:
            entities.append(MessageEntity(type=MessageEntity.CODE, offset=offset, length=length))
        elif isinstance(style, str):
            entities.append(MessageEntity(
                type=MessageEntity.CUSTOM_EMOJI, offset=offset, length=length, custom_emoji_id=style
            ))
        text += segment
        offset += length

    return text, entities


def resolve_parts(parts, dynamic_value):
    """Substitutes the DYNAMIC sentinel with the real value (e.g. first_name)."""
    return [(dynamic_value if segment is DYNAMIC else segment, style) for segment, style in parts]
