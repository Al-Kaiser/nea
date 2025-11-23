# Subtitle Translator

أداة ترجمة ملفات الترجمة متوافقة مع Aegisub

## المميزات

- دعم صيغ ASS و SRT و SSA
- الحفاظ على تنسيقات Aegisub (الأنماط، التأثيرات، المواقع)
- ترجمة مجانية عبر Google Translate
- واجهة سطر أوامر سهلة

## التثبيت

```bash
pip install -r requirements.txt
```

## الاستخدام

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
