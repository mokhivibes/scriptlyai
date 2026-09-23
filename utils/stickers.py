# file_id values from the "ScriptlyAI Animated" sticker set
# (scriptlyai_animated_by_ScriptlyAI_bot), WEBM/VP9 video stickers built
# from assets/stickers/*_nobg.png - each animated per-sticker (welcome:
# grow + brightness shimmer, processing: traveling ripple across the
# equalizer bars, done: checkmark pop-in with a settling bounce, error: a
# shake) and uploaded via bot.create_new_sticker_set(). Supersedes an
# earlier static-PNG set (scriptlyai_pack_by_ScriptlyAI_bot), left
# in place on Telegram's side rather than deleted since nothing
# references it anymore. A Telegram file_id is permanent once uploaded -
# no need to re-upload or re-fetch these on each send.
STICKER_WELCOME = "CAACAgIAAxUAAWqxwnZpO5e1-hFRepndT_NauvFIAAIMsgACNHOQSU4yM2CHpzlNPQQ"
# 2026-09-23: replaced via replaceStickerInSet - the original render had a
# small stray teal dot (leftover from background removal) near the bottom
# right corner, static across every frame. Patched frame-by-frame in
# assets/stickers/processing.webm and re-uploaded; file_id changed.
STICKER_PROCESSING = "CAACAgIAAxUAAWq0HrFlWQyqoHNfCxOJdLRbk4D-AAIrswACO3OgSYU83OGnGim0PQQ"
# 2026-09-23: replaced via replaceStickerInSet - the original design
# combined a big "S" letter (network-node overlay) with the checkmark
# overlapping it, which read as cluttered/unclear at sticker size. Rebuilt
# as a standalone checkmark only (assets/stickers/done_nobg.png,
# done.webm - same pop-in-with-bounce animation, no S, no equalizer
# bars); file_id changed.
STICKER_DONE = "CAACAgIAAxUAAWq0KvusAfAVFwV3fQONcXvxkKOQAAJHqQAC2ZWhSTnXNd3x0oRhPQQ"
STICKER_ERROR = "CAACAgIAAxUAAWqxwnY04CszPoWyUv_09pPqLL0NAAK0pwACJvmQSVkfh21UhsliPQQ"
