#!/usr/bin/env python3
"""
Subtitle Translator - واجهة ويب
متوافقة مع Aegisub (ASS/SRT)
"""

import gradio as gr
import pysubs2
from deep_translator import GoogleTranslator
from pathlib import Path
import tempfile
import re


def get_language_choices():
    """Return language choices for dropdown"""
    return [
        ("العربية", "ar"),
        ("English", "en"),
        ("日本語 (Japanese)", "ja"),
        ("한국어 (Korean)", "ko"),
        ("中文 简体 (Chinese Simplified)", "zh-CN"),
        ("中文 繁體 (Chinese Traditional)", "zh-TW"),
        ("Français", "fr"),
        ("Deutsch", "de"),
        ("Español", "es"),
        ("Italiano", "it"),
        ("Português", "pt"),
        ("Русский", "ru"),
        ("Türkçe", "tr"),
        ("हिन्दी", "hi"),
        ("ไทย", "th"),
        ("Tiếng Việt", "vi"),
        ("Bahasa Indonesia", "id"),
        ("فارسی", "fa"),
    ]


def translate_text(text: str, translator: GoogleTranslator) -> str:
    """Translate text while preserving ASS formatting tags"""
    if not text or not text.strip():
        return text

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


def translate_subtitle(file, target_lang, source_lang, progress=gr.Progress()):
    """Main translation function for Gradio interface"""

    if file is None:
        return None, "❌ الرجاء رفع ملف ترجمة"

    try:
        # Load subtitle file
        progress(0.1, desc="جاري تحميل الملف...")
        subs = pysubs2.load(file.name)

        # Get file info
        input_path = Path(file.name)

        # Initialize translator
        src = 'auto' if source_lang == 'auto' else source_lang
        translator = GoogleTranslator(source=src, target=target_lang)

        # Filter dialogue lines
        dialogue_lines = [event for event in subs.events if not event.is_comment]

        if not dialogue_lines:
            return None, "❌ لا توجد نصوص للترجمة في الملف"

        # Translate with progress
        total = len(dialogue_lines)
        for i, event in enumerate(dialogue_lines):
            if event.text:
                event.text = translate_text(event.text, translator)
            progress((i + 1) / total, desc=f"جاري الترجمة... {i+1}/{total}")

        # Save to temp file
        output_filename = f"{input_path.stem}_{target_lang}{input_path.suffix}"
        output_path = Path(tempfile.gettempdir()) / output_filename
        subs.save(str(output_path))

        status = f"✅ تمت الترجمة بنجاح!\n\n"
        status += f"📄 عدد الأسطر: {total}\n"
        status += f"🌐 اللغة: {target_lang}\n"
        status += f"📁 الملف: {output_filename}"

        return str(output_path), status

    except Exception as e:
        return None, f"❌ خطأ: {str(e)}"


# Create Gradio interface
with gr.Blocks(
    title="Subtitle Translator",
    css="""
    .rtl { direction: rtl; text-align: right; }
    """
) as app:

    gr.Markdown(
        """
        # 🎬 Subtitle Translator
        ### أداة ترجمة ملفات الترجمة - متوافقة مع Aegisub
        """,
        elem_classes="rtl"
    )

    with gr.Row():
        with gr.Column():
            file_input = gr.File(
                label="📁 ملف الترجمة (ASS/SRT)",
                file_types=[".ass", ".srt", ".ssa"],
                type="filepath"
            )

            target_lang = gr.Dropdown(
                choices=get_language_choices(),
                value="ar",
                label="🌐 لغة الترجمة"
            )

            source_lang = gr.Dropdown(
                choices=[("تلقائي", "auto")] + get_language_choices(),
                value="auto",
                label="📝 لغة المصدر"
            )

            translate_btn = gr.Button(
                "🚀 ترجمة",
                variant="primary",
                size="lg"
            )

        with gr.Column():
            output_file = gr.File(
                label="📥 تحميل الملف المترجم"
            )

            status_text = gr.Textbox(
                label="📊 الحالة",
                lines=5,
                interactive=False,
                elem_classes="rtl"
            )

    # Connect button to function
    translate_btn.click(
        fn=translate_subtitle,
        inputs=[file_input, target_lang, source_lang],
        outputs=[output_file, status_text]
    )

    gr.Markdown(
        """
        ---
        ### ملاحظات:
        - الأداة تحافظ على جميع تنسيقات ASS (المواقع، الألوان، التأثيرات)
        - للحصول على أفضل نتائج، حدد لغة المصدر يدوياً
        - الصيغ المدعومة: ASS, SRT, SSA
        """,
        elem_classes="rtl"
    )


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
