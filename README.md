# Subtitle Translator

أداة ترجمة ملفات الترجمة متوافقة مع Aegisub

## المميزات

- دعم صيغ ASS و SRT و SSA
- الحفاظ على تنسيقات Aegisub (الأنماط، التأثيرات، المواقع)
- ترجمة مجانية عبر Google Translate
- واجهة ويب سهلة الاستخدام (Gradio)
- واجهة سطر أوامر (CLI)

## التثبيت

```bash
pip install -r requirements.txt
```

## الاستخدام

### واجهة الويب (مستحسن)

```bash
python app.py
```
ثم افتح المتصفح على: http://localhost:7860

### سطر الأوامر (CLI)

```bash
# ترجمة إلى العربية
python subtitle_translator.py input.ass -t ar

# ترجمة من اليابانية إلى الإنجليزية
python subtitle_translator.py input.srt -t en -s ja

# تحديد ملف الإخراج
python subtitle_translator.py input.ass -t ar -o output.ass

# عرض اللغات المدعومة
python subtitle_translator.py --list
```

## رموز اللغات الشائعة

| الرمز | اللغة |
|-------|-------|
| ar | العربية |
| en | English |
| ja | Japanese |
| ko | Korean |
| zh-CN | Chinese |
| fr | French |
| es | Spanish |

## ملاحظات

- الأداة تحافظ على جميع تنسيقات ASS مثل `{\pos}`, `{\an}`, `{\c}` وغيرها
- يتم حفظ الملف المترجم بنفس الصيغة الأصلية
- للحصول على أفضل نتائج، حدد لغة المصدر باستخدام `-s`
