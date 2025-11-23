#!/usr/bin/env python3
"""
Subtitle Translator - أداة ترجمة ملفات الترجمة
متوافقة مع Aegisub (ASS/SRT)
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

import pysubs2
from deep_translator import GoogleTranslator
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama for Windows support
init()


def print_success(msg: str):
    print(f"{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")


def print_error(msg: str):
    print(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")


def print_info(msg: str):
    print(f"{Fore.CYAN}ℹ {msg}{Style.RESET_ALL}")


def get_supported_languages() -> dict:
    """Return commonly used language codes"""
    return {
        'ar': 'العربية',
        'en': 'English',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh-CN': 'Chinese (Simplified)',
        'zh-TW': 'Chinese (Traditional)',
        'fr': 'French',
        'de': 'German',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'tr': 'Turkish',
        'hi': 'Hindi',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'ms': 'Malay',
    }


def translate_text(text: str, translator: GoogleTranslator) -> str:
    """Translate text while preserving ASS formatting tags"""
    if not text or not text.strip():
        return text

    # Extract and preserve ASS override tags like {\pos(x,y)}, {\an8}, etc.
    import re

    # Pattern to match ASS override blocks
    tag_pattern = r'(\{[^}]*\})'

    # Split text into tags and content
    parts = re.split(tag_pattern, text)

    translated_parts = []
    for part in parts:
        if part.startswith('{') and part.endswith('}'):
            # Preserve formatting tags
            translated_parts.append(part)
        elif part.strip():
            # Translate actual text
            try:
                translated = translator.translate(part)
                translated_parts.append(translated if translated else part)
            except Exception:
                translated_parts.append(part)
        else:
            translated_parts.append(part)

    return ''.join(translated_parts)


def translate_subtitles(
    input_file: str,
    output_file: Optional[str],
    target_lang: str,
    source_lang: str = 'auto',
    batch_size: int = 50
) -> bool:
    """
    Translate subtitle file while preserving Aegisub compatibility

    Args:
        input_file: Path to input subtitle file (ASS/SRT)
        output_file: Path to output file (optional)
        target_lang: Target language code
        source_lang: Source language code (default: auto-detect)
        batch_size: Number of lines to translate per batch

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load subtitle file
        print_info(f"جاري تحميل الملف: {input_file}")
        subs = pysubs2.load(input_file)

        # Determine output file path
        if not output_file:
            input_path = Path(input_file)
            output_file = str(input_path.parent / f"{input_path.stem}_{target_lang}{input_path.suffix}")

        # Initialize translator
        translator = GoogleTranslator(source=source_lang, target=target_lang)

        # Filter dialogue lines (skip comments)
        dialogue_lines = [event for event in subs.events if not event.is_comment]

        if not dialogue_lines:
            print_error("لا توجد نصوص للترجمة في الملف")
            return False

        print_info(f"عدد الأسطر: {len(dialogue_lines)}")
        print_info(f"الترجمة إلى: {target_lang}")

        # Translate with progress bar
        print_info("جاري الترجمة...")

        for event in tqdm(dialogue_lines, desc="الترجمة", unit="سطر"):
            if event.text:
                event.text = translate_text(event.text, translator)

        # Save translated file
        subs.save(output_file)
        print_success(f"تم حفظ الملف المترجم: {output_file}")

        return True

    except FileNotFoundError:
        print_error(f"الملف غير موجود: {input_file}")
        return False
    except Exception as e:
        print_error(f"خطأ: {str(e)}")
        return False


def list_languages():
    """Display supported languages"""
    print("\nاللغات المدعومة:")
    print("-" * 40)
    languages = get_supported_languages()
    for code, name in languages.items():
        print(f"  {code:<8} {name}")
    print("-" * 40)
    print("\nللمزيد من اللغات، استخدم رمز اللغة ISO 639-1")
    print("مثال: fa للفارسية، uk للأوكرانية\n")


def main():
    parser = argparse.ArgumentParser(
        description="أداة ترجمة ملفات الترجمة - متوافقة مع Aegisub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  %(prog)s input.ass -t ar                    # ترجمة إلى العربية
  %(prog)s input.srt -t en -s ja              # ترجمة من اليابانية إلى الإنجليزية
  %(prog)s input.ass -t ar -o output.ass      # تحديد ملف الإخراج
  %(prog)s --list                             # عرض اللغات المدعومة
        """
    )

    parser.add_argument('input', nargs='?', help='ملف الترجمة (ASS/SRT)')
    parser.add_argument('-t', '--target', help='لغة الترجمة (مثال: ar, en, ja)')
    parser.add_argument('-s', '--source', default='auto', help='لغة المصدر (افتراضي: تلقائي)')
    parser.add_argument('-o', '--output', help='ملف الإخراج (اختياري)')
    parser.add_argument('--list', action='store_true', help='عرض اللغات المدعومة')

    args = parser.parse_args()

    # Show languages list
    if args.list:
        list_languages()
        return 0

    # Validate required arguments
    if not args.input:
        parser.print_help()
        return 1

    if not args.target:
        print_error("يجب تحديد لغة الترجمة باستخدام -t")
        print("مثال: subtitle_translator.py input.ass -t ar")
        return 1

    # Check if input file exists
    if not os.path.exists(args.input):
        print_error(f"الملف غير موجود: {args.input}")
        return 1

    # Validate file extension
    ext = Path(args.input).suffix.lower()
    if ext not in ['.ass', '.srt', '.ssa']:
        print_error(f"صيغة غير مدعومة: {ext}")
        print("الصيغ المدعومة: ASS, SRT, SSA")
        return 1

    # Translate
    success = translate_subtitles(
        input_file=args.input,
        output_file=args.output,
        target_lang=args.target,
        source_lang=args.source
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
