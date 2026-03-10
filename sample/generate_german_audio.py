"""
Generate a sample German medical dictation MP3/WAV for testing.

Requirements (install once):
    pip install gtts pydub
    # also needs ffmpeg installed on your system

Run:
    python generate_german_audio.py
"""

# ── German medical dictation text ────────────────────────────────────────────
DICTATION_TEXT = """
Patient Herr Müller, 58 Jahre alt, stellt sich heute mit seit drei Wochen 
anhaltenden Schmerzen im linken Knie vor. 

Die Schmerzen verstärken sich beim Treppensteigen und bei längerem Gehen. 
Der Patient berichtet außerdem über eine gelegentliche Schwellung im Kniebereich, 
besonders abends nach körperlicher Belastung.

Klinische Untersuchung: Es zeigt sich eine leichte Schwellung im medialen 
Kompartiment des linken Kniegelenks. Druckschmerz über dem medialen Gelenkspalt. 
Bewegungsumfang eingeschränkt, Flexion bis 110 Grad möglich. 
Keine Instabilität der Bänder. Meniskuszeichen fraglich positiv.

Diagnose: Verdacht auf mediale Gonarthrose links, 
beziehungsweise mediale Meniskusläsion.

Weiteres Vorgehen: Röntgenaufnahme des linken Kniegelenks in zwei Ebenen. 
MRT des linken Kniegelenks zur weiteren Abklärung. 
Schmerztherapie mit Ibuprofen 400 Milligramm bis zu dreimal täglich bei Bedarf. 
Wiedervorstellung in zwei Wochen oder früher bei Beschwerdeverschlimmerung.
""".strip()


def generate_with_gtts():
    """Generate using Google Text-to-Speech (needs internet)."""
    try:
        from gtts import gTTS
        import os

        print("Generating German medical dictation audio with gTTS...")
        tts = gTTS(text=DICTATION_TEXT, lang="de", slow=False)

        mp3_path = "dictation_german.mp3"
        tts.save(mp3_path)
        print(f"✓ Saved: {mp3_path}")
        print(f"  Size: {os.path.getsize(mp3_path) / 1024:.1f} KB")
        print()
        print("Run the pipeline:")
        print(f"  uv run medical-dictation run {mp3_path}")

    except ImportError:
        print("gTTS not installed. Run:  pip install gtts")
        raise


def generate_with_pyttsx3():
    """Generate using pyttsx3 (fully offline, needs German voice installed)."""
    try:
        import pyttsx3

        engine = pyttsx3.init()

        # Try to set a German voice
        voices = engine.getProperty("voices")
        german_voice = next(
            (v for v in voices if "german" in v.name.lower() or "de" in v.id.lower()),
            None,
        )
        if german_voice:
            engine.setProperty("voice", german_voice.id)
            print(f"Using voice: {german_voice.name}")
        else:
            print("Warning: No German voice found, using system default.")
            print("Install a German TTS voice for best results.")

        engine.setProperty("rate", 140)  # slightly slower for medical clarity
        engine.setProperty("volume", 1.0)

        wav_path = "dictation_german.wav"
        print(f"Generating audio → {wav_path} ...")
        engine.save_to_file(DICTATION_TEXT, wav_path)
        engine.runAndWait()
        print(f"✓ Saved: {wav_path}")
        print()
        print("Run the pipeline:")
        print(f"  uv run medical-dictation run {wav_path}")

    except ImportError:
        print("pyttsx3 not installed. Run:  pip install pyttsx3")
        raise


if __name__ == "__main__":
    import sys

    method = sys.argv[1] if len(sys.argv) > 1 else "gtts"

    print("=" * 60)
    print("German Medical Dictation — Sample Audio Generator")
    print("=" * 60)
    print()
    print("Text to be spoken:")
    print("-" * 40)
    print(DICTATION_TEXT[:300] + "...")
    print("-" * 40)
    print()

    if method == "pyttsx3":
        generate_with_pyttsx3()
    else:
        generate_with_gtts()
