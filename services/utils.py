def clean_skin_tones(text_to_clean):
    if not text_to_clean:
        return ""

    replacements = {
        "💪🏻": "💪",
        "💪🏼": "💪",
        "💪🏽": "💪",
        "💪🏾": "💪",
        "💪🏿": "💪",
        "🤝🏻": "🤝",
        "🤝🏼": "🤝",
        "🤝🏽": "🤝",
        "🤝🏾": "🤝",
        "🤝🏿": "🤝"
    }

    for tone, base in replacements.items():
        text_to_clean = text_to_clean.replace(tone, base)

    return text_to_clean
