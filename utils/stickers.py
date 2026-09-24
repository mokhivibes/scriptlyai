# file_id values from the "ScriptlyAI Animated" sticker set
# (scriptlyai_animated_by_ScriptlyAI_bot), WEBM/VP9 video stickers built
# from assets/stickers/*_nobg.png - each animated per-sticker (welcome:
# grow + brightness shimmer, processing: traveling ripple across the
# equalizer bars, done: shine sweeps across a checkmark then holds, error:
# an X mark settles into a quick shake then holds - both done/error loop
# seamlessly, first frame == last frame) and uploaded via
# bot.create_new_sticker_set(). Supersedes an earlier static-PNG set
# (scriptlyai_pack_by_ScriptlyAI_bot), left in place on Telegram's side
# rather than deleted since nothing references it anymore.
#
# IMPORTANT: a file_id is normally permanent once uploaded, BUT calling
# replaceStickerInSet on ANY sticker in this set reissues file_ids for
# EVERY sticker in the set, not just the one replaced (confirmed
# 2026-09-24 - after replacing only the done sticker, welcome/processing/
# error's file_ids had all silently changed too). After any
# replaceStickerInSet call, re-fetch the whole set via getStickerSet and
# update ALL FOUR constants below, even ones that weren't touched -
# leaving a stale one here means that sticker silently fails to send.
STICKER_WELCOME = "CAACAgIAAxkDAAIDkGq02YMfPVKUmXpoKy9ec0Gmg2M5AAIMsgACNHOQSU4yM2CHpzlNPQQ"
STICKER_PROCESSING = "CAACAgIAAxUAAWq1WWDR4b4wZzfMc1YKeR8tfknzAAIrswACO3OgSYU83OGnGim0PQQ"
STICKER_DONE = "CAACAgIAAxUAAWq1WWAeIv3leOODQM4KazDitPQpAAKQowACnjOpSahNqnjV33pAPQQ"
STICKER_ERROR = "CAACAgIAAxUAAWq1XDFm8_lMEOkUXXsmIpd5pEhSAAKlrAACBwepSf13exsD5LABPQQ"
