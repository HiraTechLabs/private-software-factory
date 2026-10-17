# مصنع البرمجيات الخاص

مسار واحد ثابت لكل تغيير، على مجموعة أدوات معلنة ومثبّتة، مع اعتماد بشرٍ لكل عملية
دمج أو إطلاق إلى الإنتاج. هذا المستودع هو «المشروع صفر»: يلتزم بقواعده بنفسه (انظر AGENTS.md).

## التثبيت

يتطلب بايثون 3.11+.

```sh
pip install -e ".[dev]"
```

## التشغيل

ربط الخادم بـ 127.0.0.1 فقط؛ النسخة الأولى بلا مصادقة (القرار 0007):

```sh
uvicorn factory.main:app --host 127.0.0.1
```

ثم افتح لوحة التحكم على `http://127.0.0.1:8000/` وكتالوج الواجهة على `/ui`.

## الفحوص

يجب أن تنجح كلها محلياً وفي CI:

```sh
ruff check .
ruff format --check .
pytest
python scripts/graph_check.py --check
python scripts/ui_lint.py
python scripts/build_tokens.py --check
```

## بنية المستودع

```text
AGENTS.md            قواعد هذا المستودع الملزمة (اقرأه أولاً)
docs/decisions/      سجل القرارات (ADRs)
docs/architecture/   graph.yaml + الرسم المولد graph.md
docs/ui/             نظام الواجهة وملاحظات الخطوط
design/              design/tokens.json (مصدر الحقيقة للتصميم)
scripts/             الفحوصات: graph_check و ui_lint و build_tokens
src/factory/         كود التطبيق: main.py و manifest.py و ui_vocab.py والقوالب والتنسيقات
data/projects/       المشاريع المسجلة (مستثناة من git)
.github/workflows/   CI
```

الحوكمة كلها في AGENTS.md وهو المرجع النافذ لهذا المستودع.
