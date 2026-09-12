from faster_whisper import WhisperModel


# Whisper Medium gives better accuracy for English, Russian, and Arabic.
model = WhisperModel(
    "medium",
    device="cpu",
    compute_type="int8"
)


def transcribe_audio(audio_path: str, language: str = None):
    """
    Convert an audio file into text using Whisper Medium.

    If a language is provided, Whisper uses that language.
    Otherwise, Whisper automatically detects the language.
    """

    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5
    )

    transcript = []

    for segment in segments:
        transcript.append(segment.text.strip())

    return " ".join(transcript), info.language