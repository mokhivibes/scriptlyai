# Custom emoji IDs for the branded platform icons shown in the welcome/
# start messages (see rich_text.py's build_bold_message for how these get
# used as entities). Sourced from two different places - see the ids.txt
# files this session generated under /tmp/emoji_check* for provenance:
#
# - YOUTUBE and X: built from scratch as simple animated Lottie shapes
#   (utils/rich_text.py-style pulse) and uploaded to a bot-owned custom
#   emoji set (scriptlyai_icons_by_ScriptlyAI_bot) - X was later reverted
#   back to a static icon from the public "Twitter_X" pack per user
#   preference (this style read better than the custom animated one).
# - INSTAGRAM and TIKTOK: from the public "ApplicationEmoji" pack
#   (larger, full-bleed icons - user preferred these over the smaller
#   versions in "SocialEmojis").
# - FACEBOOK: from the public "SocialEmojis" pack.
#
# A Telegram custom_emoji_id is permanent once it exists - no re-fetching
# needed, and these work in any bot's messages regardless of which pack
# or account originally created them (Premium is only required to CREATE
# a new custom emoji, not to reference an existing one).
YOUTUBE = "5301046338362844056"
INSTAGRAM = "5319160079465857105"
TIKTOK = "5327982530702359565"
FACEBOOK = "6319109091100723141"
X_TWITTER = "5440750315852803515"
