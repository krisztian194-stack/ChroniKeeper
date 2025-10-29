import json
import os

class LanguageLookup:
    def __init__(self, lookup_path="language/tag_map.json", default_lang="en"):
        self.lookup_path = lookup_path
        self.default_lang = default_lang
        self.maps = self.load_lookup()

    def load_lookup(self):
        if os.path.exists(self.lookup_path):
            with open(self.lookup_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            print(f"[WARN] Missing tag map file: {self.lookup_path}")
            return {"en": {}, "hu": {}}

    # ------------------------------
    # Translate tag from one language to another
    # ------------------------------
    def translate_tag(self, tag: str, src_lang: str, dst_lang: str):
        tag = tag.lower().strip()
        if src_lang == dst_lang:
            return tag

        src_map = self.maps.get(src_lang, {})
        dst_map = self.maps.get(dst_lang, {})

        # Step 1: find English equivalent if not already English
        if src_lang != "en":
            en_key = None
            for en_tag, trans in src_map.items():
                if trans.lower() == tag:
                    en_key = en_tag
                    break
            if not en_key:
                return tag  # fallback if unknown
        else:
            en_key = tag

        # Step 2: translate English to target
        if dst_lang == "en":
            return en_key
        return dst_map.get(en_key, en_key)

    # ------------------------------
    # Convert list of tags
    # ------------------------------
    def translate_tags(self, tags, src_lang, dst_lang):
        return [self.translate_tag(t, src_lang, dst_lang) for t in tags]
