#!/usr/bin/env python3
"""
Traduce posts de content/es/ a content/ca/ y content/en/
usando la API de Anthropic (Claude).

Uso:
  python translate.py                        # traduce todo lo nuevo
  python translate.py --force                # retraducir aunque ya exista
  python translate.py --file posts/mi-post.md  # un archivo concreto

Requiere:
  pip install anthropic
  export ANTHROPIC_API_KEY=sk-ant-...
"""

import os
import sys
import argparse
import anthropic

SRC_DIR    = "content/es"
TARGETS    = {"ca": "Catalan", "en": "English"}
MODEL      = "claude-haiku-4-5-20251001"   # rápido y barato para traducciones

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def translate(text: str, target_lang: str, target_name: str) -> str:
    prompt = f"""Translate the following Hugo Markdown file from Spanish to {target_name}.

Rules:
- Preserve ALL frontmatter fields and YAML structure exactly
- Only translate the VALUES of: title, excerpt, and the body text
- Do NOT translate: keys, dates, draft, URLs, code blocks, proper nouns (Fab Lab, Hugo, etc.)
- Keep the same Markdown formatting (##, **, etc.)
- Return ONLY the translated file content, no explanation

File to translate:
---
{text}
"""
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def get_target_path(src_path: str, lang: str) -> str:
    # content/es/posts/foo.md → content/ca/posts/foo.md
    rel = os.path.relpath(src_path, SRC_DIR)
    return os.path.join(f"content/{lang}", rel)


def translate_file(src_path: str, force: bool = False):
    with open(src_path, encoding="utf-8") as f:
        source = f.read()

    for lang, lang_name in TARGETS.items():
        dst_path = get_target_path(src_path, lang)
        if os.path.exists(dst_path) and not force:
            print(f"  ↷  skip  {dst_path} (ya existe, usa --force para retraducir)")
            continue

        print(f"  →  traduciendo a {lang_name}: {dst_path}")
        translated = translate(source, lang, lang_name)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        with open(dst_path, "w", encoding="utf-8") as f:
            f.write(translated)
        print(f"  ✓  guardado: {dst_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Retraducir aunque ya exista")
    parser.add_argument("--file",  help="Archivo concreto relativo a content/es/")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: falta ANTHROPIC_API_KEY")
        sys.exit(1)

    if args.file:
        path = os.path.join(SRC_DIR, args.file)
        if not os.path.exists(path):
            print(f"No encontrado: {path}")
            sys.exit(1)
        print(f"\nTraduciendo: {path}")
        translate_file(path, force=args.force)
    else:
        # Todos los .md en content/es (excepto _index.md)
        for root, _, files in os.walk(SRC_DIR):
            for fname in files:
                if fname.endswith(".md") and fname != "_index.md":
                    translate_file(os.path.join(root, fname), force=args.force)

    print("\nListo.")


if __name__ == "__main__":
    main()
