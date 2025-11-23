#!/usr/bin/env python3
"""
Subtitle Translator - واجهة ويب محسنة
متوافقة مع Aegisub (ASS/SRT)
"""
 
import gradio as gr
import pysubs2
from deep_translator import GoogleTranslator
from pathlib import Path
import tempfile
import re
import os
import hashlib
import json
 
# Cache للترجمات المكررة
translation_cache = {}
 
 
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
 
 
def get_cache_key(text: str, source: str, target: str, provider: str) -> str:
    """Generate cache key for translation"""
    content = f"{text}|{source}|{target}|{provider}"
    return hashlib.md5(content.encode()).hexdigest()
 
 
def translate_with_openai(texts: list, source_lang: str, target_lang: str, api_key: str) -> list:
    """Translate using OpenAI API for better context-aware translations"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
 
        # Prepare batch prompt
        lang_names = {
            'ar': 'Arabic', 'en': 'English', 'ja': 'Japanese', 'ko': 'Korean',
            'zh-CN': 'Simplified Chinese', 'zh-TW': 'Traditional Chinese',
            'fr': 'French', 'de': 'German', 'es': 'Spanish', 'it': 'Italian',
            'pt': 'Portuguese', 'ru': 'Russian', 'tr': 'Turkish'
        }
 
        target_name = lang_names.get(target_lang, target_lang)
 
        # Join texts with separator
        separator = "\n---SUBTITLE_SEP---\n"
        combined_text = separator.join(texts)
 
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional anime subtitle translator. Translate ALL of the following subtitles into {target_name}. Every subtitle line must be fully translated into {target_name}. No skipping is allowed. Do not leave any subtitle line untranslated. No English words or sentences are allowed unless they are proper names that cannot be translated. If an English phrase has a clear equivalent in {target_name}, always translate it. Keep the same number of lines and maintain the separator '---SUBTITLE_SEP---' between each subtitle. Preserve any formatting tags in curly braces like {{\\pos}} or {{\\an8}}. Do not add explanations, notes, or comments. Only return the translations, nothing else."
                },
                {
                    "role": "user",
                    "content": combined_text
                }
            ],
            temperature=0.2
        )
 
        translated_text = response.choices[0].message.content
        return translated_text.split(separator)
 
    except ImportError:
        raise Exception("مكتبة openai غير مثبتة. قم بتثبيتها: pip install openai")
    except Exception as e:
        raise Exception(f"خطأ في OpenAI API: {str(e)}")
 
 
def translate_with_google_batch(texts: list, source_lang: str, target_lang: str) -> list:
    """Translate batch of texts using Google Translate"""
    src = 'auto' if source_lang == 'auto' else source_lang
    translator = GoogleTranslator(source=src, target=target_lang)
 
    results = []
    for text in texts:
        if not text or not text.strip():
            results.append(text)
            continue
 
        # Extract and preserve ASS tags
        tag_pattern = r'(\{[^}]*\})'
        parts = re.split(tag_pattern, text)
 
        translated_parts = []
        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                translated_parts.append(part)
            elif part.strip():
                try:
                    # Check cache
                    cache_key = get_cache_key(part, src, target_lang, 'google')
                    if cache_key in translation_cache:
                        translated_parts.append(translation_cache[cache_key])
                    else:
                        translated = translator.translate(part)
                        translation_cache[cache_key] = translated
                        translated_parts.append(translated if translated else part)
                except Exception:
                    translated_parts.append(part)
            else:
                translated_parts.append(part)
 
        results.append(''.join(translated_parts))
 
    return results
 
 
def preview_subtitles(file):
    """Preview first 10 lines of subtitle file"""
    if file is None:
        return "لم يتم رفع ملف"
 
    try:
        subs = pysubs2.load(file.name)
        dialogue_lines = [event for event in subs.events if not event.is_comment][:10]
 
        preview = "📋 معاينة أول 10 أسطر:\n\n"
        for i, event in enumerate(dialogue_lines, 1):
            preview += f"{i}. {event.text}\n"
 
        if len([e for e in subs.events if not e.is_comment]) > 10:
            preview += f"\n... و {len([e for e in subs.events if not e.is_comment]) - 10} سطر آخر"
 
        return preview
    except Exception as e:
        return f"❌ خطأ في قراءة الملف: {str(e)}"
 
 
def translate_subtitle(file, target_lang, source_lang, provider, api_key, dual_subs, batch_size, progress=gr.Progress()):
    """Main translation function with improvements"""
 
    if file is None:
        return None, "❌ الرجاء رفع ملف ترجمة", ""
 
    if provider == "openai" and not api_key:
        return None, "❌ الرجاء إدخال OpenAI API Key", ""
 
    try:
        # Load subtitle file
        progress(0.1, desc="جاري تحميل الملف...")
        subs = pysubs2.load(file.name)
        original_subs = pysubs2.load(file.name)  # Keep original for dual subs
 
        input_path = Path(file.name)
 
        # Filter dialogue lines
        dialogue_lines = [event for event in subs.events if not event.is_comment]
 
        if not dialogue_lines:
            return None, "❌ لا توجد نصوص للترجمة في الملف", ""
 
        total = len(dialogue_lines)
        progress(0.2, desc=f"جاري الترجمة... (0/{total})")
 
        # Batch translation for better performance
        batch_size = int(batch_size)
        translated_count = 0
 
        if provider == "openai":
            # OpenAI batch translation
            for i in range(0, total, batch_size):
                batch = dialogue_lines[i:i+batch_size]
                texts = [event.text for event in batch]
 
                translated_texts = translate_with_openai(texts, source_lang, target_lang, api_key)
 
                for j, event in enumerate(batch):
                    if j < len(translated_texts):
                        if dual_subs:
                            original_text = event.text
                            event.text = f"{translated_texts[j]}\\N{original_text}"
                        else:
                            event.text = translated_texts[j]
 
                translated_count += len(batch)
                progress(0.2 + (0.7 * translated_count / total), desc=f"جاري الترجمة... ({translated_count}/{total})")
        else:
            # Google Translate batch
            for i in range(0, total, batch_size):
                batch = dialogue_lines[i:i+batch_size]
                texts = [event.text for event in batch]
 
                translated_texts = translate_with_google_batch(texts, source_lang, target_lang)
 
                for j, event in enumerate(batch):
                    if j < len(translated_texts):
                        if dual_subs:
                            original_text = event.text
                            event.text = f"{translated_texts[j]}\\N{original_text}"
                        else:
                            event.text = translated_texts[j]
 
                translated_count += len(batch)
                progress(0.2 + (0.7 * translated_count / total), desc=f"جاري الترجمة... ({translated_count}/{total})")
 
        # Save translated file
        suffix = "_dual" if dual_subs else ""
        output_filename = f"{input_path.stem}_{target_lang}{suffix}{input_path.suffix}"
        output_path = Path(tempfile.gettempdir()) / output_filename
        subs.save(str(output_path))
 
        # Generate preview of translated content
        preview = "📋 معاينة الترجمة (أول 5 أسطر):\n\n"
        for i, event in enumerate(dialogue_lines[:5], 1):
            preview += f"{i}. {event.text}\n"
 
        status = f"✅ تمت الترجمة بنجاح!\n\n"
        status += f"📄 عدد الأسطر: {total}\n"
        status += f"🌐 اللغة: {target_lang}\n"
        status += f"🔧 المحرك: {provider.upper()}\n"
        status += f"📦 حجم الدفعة: {batch_size}\n"
        status += f"📁 الملف: {output_filename}"
 
        if dual_subs:
            status += "\n🔄 ترجمة مزدوجة: نعم"
 
        progress(1.0, desc="تم!")
 
        return str(output_path), status, preview
 
    except Exception as e:
        return None, f"❌ خطأ: {str(e)}", ""
 
 
# Create Gradio interface
with gr.Blocks() as app:
 
    gr.Markdown(
        """
        # 🎬 Subtitle Translator
        ### أداة ترجمة ملفات الترجمة - متوافقة مع Aegisub
        """
    )
 
    with gr.Row():
        with gr.Column():
            file_input = gr.File(
                label="📁 ملف الترجمة (ASS/SRT)",
                file_types=[".ass", ".srt", ".ssa"],
                type="filepath"
            )
 
            preview_btn = gr.Button("👁️ معاينة", variant="secondary")
            preview_text = gr.Textbox(
                label="معاينة الملف الأصلي",
                lines=6,
                interactive=False
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
 
            with gr.Row():
                provider = gr.Radio(
                    choices=[("Google (مجاني)", "google"), ("OpenAI (أفضل جودة)", "openai")],
                    value="google",
                    label="🔧 محرك الترجمة"
                )
 
            api_key = gr.Textbox(
                label="🔑 OpenAI API Key",
                type="password",
                placeholder="sk-...",
                visible=True
            )
 
            with gr.Row():
                batch_size = gr.Slider(
                    minimum=1,
                    maximum=100,
                    value=50,
                    step=10,
                    label="📦 حجم الدفعة (أكبر = أسرع)"
                )
 
                dual_subs = gr.Checkbox(
                    label="🔄 ترجمة مزدوجة (سطرين)",
                    value=False
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
                lines=8,
                interactive=False
            )
 
            translated_preview = gr.Textbox(
                label="معاينة الترجمة",
                lines=6,
                interactive=False
            )
 
    # Connect buttons
    preview_btn.click(
        fn=preview_subtitles,
        inputs=[file_input],
        outputs=[preview_text]
    )
 
    translate_btn.click(
        fn=translate_subtitle,
        inputs=[file_input, target_lang, source_lang, provider, api_key, dual_subs, batch_size],
        outputs=[output_file, status_text, translated_preview]
    )
 
    gr.Markdown(
        """
        ---
        ### ملاحظات:
        - **Google**: مجاني، سريع، جودة جيدة
        - **OpenAI**: جودة أفضل للسياق، يحتاج API Key
        - الترجمة المزدوجة تضيف الترجمة فوق النص الأصلي
        - حجم دفعة أكبر = سرعة أعلى
        """
    )
 
 
if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )