import argostranslate.translate

# Load installed translation packages
argostranslate.translate.load_installed_languages()


def translate_text(text, target_language="en", source_language="fr"):
    if not text.strip():
        return ""
    try:
        # Get the list of installed languages
        installed_languages = argostranslate.translate.get_installed_languages()

        # Find the source and target languages
        from_lang = next((lang for lang in installed_languages if lang.code == source_language), None)
        to_lang = next((lang for lang in installed_languages if lang.code == target_language), None)

        if from_lang and to_lang:
            # Get the translation object and perform translation
            translation = from_lang.get_translation(to_lang)
            return translation.translate(text)
        else:
            return "[Translation model not installed]"
    except Exception as e:
        print(f"Translation error: {e}")
        return "[Translation failed]"
