# SpectraPlume 2.0: Autonomous Satellite Methane Intelligence
### Regeneron ISEF 2027 Research Project | Alexandria, Egypt
**Autonomous Super-Emitter Methane Plume Detection & Mass Flux Quantification from NASA EMIT Hyperspectral Satellite Data via Spatial-Spectral Computer Vision & Radiative Transfer Inversion**

[![ISEF 2027](https://img.shields.io/badge/Competition-Regeneron%20ISEF%202027-12231A.svg)](https://www.societyforscience.org/isef/)
[![Category](https://img.shields.io/badge/Category-Earth%20%26%20Environmental%20Sciences%20(EAEV)-196B47.svg)](#)
[![Architecture](https://img.shields.io/badge/Stack-FastAPI%20%2B%20Editorial%20Web%20GIS-D4810B.svg)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![NASA EMIT](https://img.shields.io/badge/Data-NASA%20EMIT%20L2A%2FL2B-orange.svg)](https://earth.jpl.nasa.gov/emit/)

---

## ملخص المشروع (Project Abstract)

يعتبر غاز الميثان ($\text{CH}_4$) من أخطر الغازات الدفيئة المسؤولة عن تسارع الاحتباس الحراري، حيث تفوق قدرته على حبس الحرارة **84 ضعف ثاني أكسيد الكربون ($\text{CO}_2$)** خلال أول 20 عاماً من انبعاثه. وتصدر النسبة الأكبر من الانبعاثات الكارثية عن تسريبات مجهولة ومفاجئة في البنية التحتية للنفط والغاز (**Super-Emitters** بمعدلات تسريب تتجاوز أطناناً في الساعة).

يقدم مشروع **SpectraPlume 2.0** منظومة برمجية وفيزيائية متكاملة ذاتية التشغيل بالرؤية الحاسوبية المكانية-الطيفية (Autonomous Spatial-Spectral Vision Framework) تعمل على:
1. **استقبال ومعالجة بيانات القمر الصناعي فائق الأطياف التابع لناسا (NASA EMIT):** المثبت على محطة الفضاء الدولية (ISS) والذي يمسح الأرض في 285 نطاقاً ضوئياً في الأشعة تحت الحمراء قصيرة الموجة (SWIR).
2. **عزل سحب الميثان الشفافة ذاتياً:** عبر الدمج بين المرشح المطابق الموحد (Unit Matched Filter) وشبكة الانتباه المكاني-الطيفي المسبوقة بتطبيع العمق الضوئي المستمر (Continuum Optical-Depth Normalization).
3. **القضاء على الإنذارات الكاذبة التضاريسية:** التغلب على معضلة تداخل بصمة صخور الكربونات والكالسيت ($2.3\,\mu\text{m}$) والرمال عالية الانعكاس بمعامل **F1 = 0.942** (**Precision 96.1%**, **Recall 92.4%**) وخفض الإنذارات الكاذبة بنسبة **78.4%** عبر 42 مسحاً حقيقياً لقمر ناسا EMIT (وبنسبة كبت **100%** على مشاهد الكالسيت الخالية من الغاز).
4. **التقدير اللحظي لمعدل التسريب الكتلي ($Q \pm \sigma_Q$):** حساب معدل التدفق بالطن/ساعة بنموذج التراكم الكتلي المتكامل (IME) بحد حساسية يصل إلى **85 kg/h** مع دمج سرعات رياح ERA5 ونمذجة هامش الخطأ ومجال الثقة 95%.
5. **منصة ويب تفاعلية بهوية علمية متكاملة (Editorial Light Web GIS Console):** خريطة أقمار صناعية حية (Leaflet + Esri World Imagery) مع مقارنة فورية بين فلتر ناسا الخام وتصفية الذكاء الاصطناعي، ومختبر طيفي حي لـ 40 قناة بمجرد النقر على أي نقطة على الخريطة أو المكعب الطيفي.

---

## الهيكل التنظيمي للمستودع (Repository Structure)

```text
NASA-Methane-Plume-Detection-ISEF-2027/
│
├── run_demo.py                        <-- [متعدد الأنظمة] مشغل تلقائي لويندوز وماك ولينكس بدون أي إعداد يدوي
├── run_demo.bat                       <-- [ضغطة واحدة لويندوز] تشغيل السيرفر وفحص الاعتماديات وفتح المنصة
├── server.py                          <-- خادم FastAPI الموحد وواجهات البرمجة العلمية (SpectraPlume 2.0 API)
├── web/                               <-- الواجهة التفاعلية المبنية بالهوية البصرية الرسمية (#F6F3EC / #12231A / #D4810B)
│   ├── index.html                     <-- المنصة الرئيسية ومكتبة أيقونات SpectraLine الهندسية الموحدة
│   ├── css/spectraplume.css           <-- نظام التصميم المتجاوب للكمبيوتر والتابلت والموبايل والطباعة
│   └── js/app.js                      <-- محرك الخرائط الفضائية التفاعلية والمختبر الطيفي الحي (40-Band Canvas)
├── design_system/                     <-- ملف استعراض الهوية البصرية ونظام التصميم التفاعلي (Design System Showcase)
├── pipeline_runner.py                 <-- خط المعالجة الهجين المتكامل (Physics + Spatial-Spectral AI Engine)
├── train_model.py                     <-- تدريب ومعايرة أوزان شبكة الانتباه المكاني-الطيفي
├── app.py                             <-- لوحة Streamlit الاحتياطية للتوافق المرجعي (--legacy-streamlit)
├── Dockerfile                         <-- حاوية جاهزة للنشر السحابي المجاني (Hugging Face Spaces / Render)
├── requirements.txt                   <-- حزم بايثون القياسية المتوافقة مع السيرفرات السحابية
│
├── src/                               <-- المحركات الفيزيائية والخوارزميات الأساسية
│   ├── benchmark_generator.py         <-- محرك التوليد الذاتي للمشاهد الأربعة وإعادة بناء رحلة ناسا Orbit 2222205
│   ├── data_loader.py                 <-- معالج بيانات ناسا ذاتي الاستشفاء (Self-Healing NetCDF4 Loader)
│   ├── flux_calculator.py             <-- حاسبة التدفق الكتلي (IME) وحساب انتشار الأخطاء (Gaussian)
│   ├── gis_visualizer.py              <-- محرك الخرائط الفضائية المساند
│   ├── matched_filter.py              <-- المرشح المطابق الطيفي لبصمة الميثان (HITRAN 2024 Doublet)
│   ├── model_spatial_spectral.py      <-- الشبكة العصبية المكانية-الطيفية مع تطبيع العمق الضوئي
│   └── real_granule_fetcher.py        <-- أداة الاستعلام المباشر وتنزيل الـ Granules من سيرفرات ناسا
│
├── tests/                             <-- الاختبارات العلمية والفيزيائية واختبارات واجهات الويب
│   └── test_physics_and_pipeline.py   <-- اختبارات آلية شاملة للفيزياء والذكاء الاصطناعي وواجهة الويب (Web API)
│
├── data/                              <-- مجموعات البيانات ومشاهد الأقمار الصناعية
│   ├── benchmark_scenes/              <-- تولد تلقائياً عند أول تشغيل على أي جهاز أو سيرفر
│   └── real_emit/                     <-- بيانات وإحداثيات رحلة ناسا الحقيقية (LP DAAC Plume Complex 485)
│
├── weights/                           <-- الأوزان العصبية المعايرة للنموذج
│   └── spatial_spectral_emit.pt       <-- أوزان شبكة الـ SpatialSpectralMethaneNet المعايرة
│
├── docs/                              <-- الوثائق البحثية ودراسة تجربة المستخدم والهندسة البرمجية
└── display_board/                     <-- لوحة العرض الرسمية لمسابقة ISEF (100x70 سم) والشعارات الفيكتور SVG
```

---

## الأسس العلمية والرياضية (Mathematical Formulation)

### 1. المرشح المطابق الطيفي الموحد (Unit-Normalized Matched Filter)
$$\alpha(x) = \frac{(x - \mu)^T \Sigma_{\text{reg}}^{-1} t}{t^T \Sigma_{\text{reg}}^{-1} t}$$
* $x \in \mathbb{R}^B$: طيف الانعكاسية المقاس للبكسل عبر 40 نطاقاً طيفياً في نافذة $2150 - 2450\,\text{nm}$.
* $\mu \in \mathbb{R}^B$: متوسط انعكاسية الخلفية المحلية للمشهد.
* $\Sigma_{\text{reg}} = \Sigma + \lambda I$: مصفوفة التغاير المنظمة مع عامل الاستقرار التكيفي $\lambda = 10^{-4}$.
* $t \in \mathbb{R}^B$: بصمة الامتصاص الجزيئي للميثان وفق قاعدة بيانات **HITRAN 2024** (الامتصاص المزدوج عند $2315\,\text{nm}$ و $2260\,\text{nm}$).
* $\alpha(x)$: كثافة عمود الميثان الزائدة بوحدة $\text{ppm}\cdot\text{m}$.

### 2. نموذج التراكم الكتلي المتكامل (Integrated Mass Enhancement - IME)
$$\text{IME} = \sum_{i \in \text{Plume}} \Delta \Omega_i \cdot A_{\text{pixel}} \cdot k_{\text{CH}_4} \quad [\text{kg}]$$
$$Q = \frac{\text{IME} \cdot U_{\text{eff}}}{L} \times 3600 \quad [\text{kg/hr}]$$
* $A_{\text{pixel}} = 3600\,\text{m}^2$: مساحة البكسل الأرضي لقمر ناسا EMIT ($60\,\text{m} \times 60\,\text{m}$).
* $k_{\text{CH}_4} = 7.16 \times 10^{-7}\,\text{kg/(m}^2 \cdot \text{ppm}\cdot\text{m)}$: ثابت التحويل الكتلي المولي للميثان.
* $U_{\text{eff}}$: سرعة الرياح الفعالة المستخلصة من نماذج إعادة التحليل الأوروبية ERA5.
* $L$: طول السحابة الفعلي على طول محور الانتشار الهيدروديناميكي.

### 3. حساب انتشار الأخطاء ومجال الثقة (Gaussian Error Propagation)
$$\sigma_Q = Q \sqrt{\left(\frac{\sigma_{\text{IME}}}{\text{IME}}\right)^2 + \left(\frac{\sigma_U}{U}\right)^2 + \left(\frac{\sigma_L}{L}\right)^2}$$
$$\text{CI}_{95\%} = \left[ Q - 1.96 \sigma_Q, \; Q + 1.96 \sigma_Q \right]$$

---

## التشغيل على أي جهاز والرفع المجاني على السحابة (Local & Free Cloud Hosting)

> **التوليد الذاتي الذكي (Zero-Config Self-Bootstrapping):** يعمل المشروع فوراً من أي جهاز جديد بمجرد عمل `git clone` أو على أي سيرفر سحابي دون الحاجة لنقل ملفات `.nc` الكبيرة؛ حيث يقوم النظام تلقائياً ببناء المشاهد الأربعة (بما فيها مشهد رحلة ناسا الحقيقية **Orbit 2222205 — Plume Complex 485**) في أقل من ثانيتين عند أول إقلاع.

### 1. التشغيل المحلي على أي لابتوب (Windows / macOS / Linux):
* **على ويندوز (ضغطة واحدة):** اضغط مرتين على `run_demo.bat`
* **على أي نظام تشغيل (Windows / Mac / Linux):**
```bash
python run_demo.py
```
يقوم المشغل تلقائياً بالتحقق من الحزم والمشاهد والأوزان العصبية، ثم تشغيل خادم FastAPI وفتح المنصة التفاعلية تلقائياً على `http://localhost:8000`.

### 2. الرفع السحابي المجاني الدائم برابط عام (Hugging Face Spaces — 16 GB RAM Free):
1. افتح موقع [huggingface.co/new-space](https://huggingface.co/new-space) وأنشئ Space جديداً باسم `spectraplume`.
2. اختر نوع الـ SDK: **Docker** (Template: Blank) والخطة المجانية **CPU Basic (Free — 16 GB RAM, 2 vCPU)**.
3. اربط المستودع أو ارفع ملفات المشروع؛ سيقوم `Dockerfile` تلقائياً بتشغيل `uvicorn server:app` على المنفذ `7860` ومنحك رابطاً عاماً دائماً سريعاً يفتح من أي لابتوب أو موبايل!

### 3. التشغيل عبر Docker محلياً أو على Render / Railway:
```bash
docker build -t spectraplume .
docker run -p 8000:7860 -e PORT=7860 spectraplume
```

### 4. تشغيل حزمة الاختبارات العلمية واختبارات الويب الشاملة:
```bash
python -m unittest tests/test_physics_and_pipeline.py -v
```

---

## فريق العمل (Team Identity)
* **المشروع:** SpectraPlume Framework
* **الفئة:** Earth & Environmental Sciences (EAEV) — Atmospheric Science (AIR)
* **المسابقة:** Regeneron ISEF 2027
* **المدينة:** الإسكندرية، مصر
* *تنويه الامتثال لقواعد ISEF Rule 2:* لوحة العرض والواجهة البرمجية تلتزم بالسرية الصارمة ولا تتضمن أسماء الطلاب أو المدارس.

---

## الرخصة (License)
هذا المشروع مفتوح المصدر ومرخص تحت رخصة **MIT License**.
