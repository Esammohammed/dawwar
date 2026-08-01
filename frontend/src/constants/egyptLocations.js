// Canonical Egypt governorate + city reference data — the single source every
// location picker in the app (search filters, sell-your-unit, profile address)
// reads from, so they never drift out of sync with each other again.
//
// `slug` mirrors backend accounts.Governorate (a validated choices field on
// User.governorate). `en`/`ar` are the display strings used wherever the
// backend field is free text instead (Listing.governorate/city, User.city) —
// keep `slug` in sync with backend/apps/accounts/models.py if it ever changes.
export const GOVERNORATES = [
  {
    slug: 'cairo', en: 'Cairo', ar: 'القاهرة',
    cities: [
      { value: 'Nasr City', ar: 'مدينة نصر' },
      { value: 'Maadi', ar: 'المعادي' },
      { value: 'New Cairo', ar: 'القاهرة الجديدة' },
      { value: 'New Capital', ar: 'العاصمة الإدارية' },
      { value: 'Heliopolis', ar: 'مصر الجديدة' },
      { value: 'Zamalek', ar: 'الزمالك' },
      { value: 'Madinaty', ar: 'مدينتي' },
      { value: 'Shorouk', ar: 'الشروق' },
      { value: 'Obour', ar: 'العبور' },
    ],
  },
  {
    slug: 'giza', en: 'Giza', ar: 'الجيزة',
    cities: [
      { value: '6th of October', ar: '6 أكتوبر' },
      { value: 'Sheikh Zayed', ar: 'الشيخ زايد' },
      { value: 'Dokki', ar: 'الدقي' },
      { value: 'Mohandessin', ar: 'المهندسين' },
      { value: 'Haram', ar: 'الهرم' },
      { value: 'Zayed New City', ar: 'زايد الجديدة' },
    ],
  },
  {
    slug: 'alexandria', en: 'Alexandria', ar: 'الإسكندرية',
    cities: [
      { value: 'Smouha', ar: 'سموحة' },
      { value: 'Miami', ar: 'ميامي' },
      { value: 'Sidi Gaber', ar: 'سيدي جابر' },
      { value: 'Montaza', ar: 'المنتزه' },
    ],
  },
  {
    slug: 'qalyubia', en: 'Qalyubia', ar: 'القليوبية',
    cities: [
      { value: 'Banha', ar: 'بنها' },
      { value: 'Shubra El Kheima', ar: 'شبرا الخيمة' },
    ],
  },
  {
    slug: 'sharqia', en: 'Sharqia', ar: 'الشرقية',
    cities: [
      { value: 'Zagazig', ar: 'الزقازيق' },
      { value: '10th of Ramadan', ar: 'العاشر من رمضان' },
    ],
  },
  {
    slug: 'dakahlia', en: 'Dakahlia', ar: 'الدقهلية',
    cities: [
      { value: 'Mansoura', ar: 'المنصورة' },
      { value: 'Mit Ghamr', ar: 'ميت غمر' },
    ],
  },
  {
    slug: 'beheira', en: 'Beheira', ar: 'البحيرة',
    cities: [
      { value: 'Damanhour', ar: 'دمنهور' },
      { value: 'Kafr El Dawwar', ar: 'كفر الدوار' },
    ],
  },
  {
    slug: 'gharbia', en: 'Gharbia', ar: 'الغربية',
    cities: [
      { value: 'Tanta', ar: 'طنطا' },
      { value: 'El Mahalla El Kubra', ar: 'المحلة الكبرى' },
    ],
  },
  {
    slug: 'monufia', en: 'Monufia', ar: 'المنوفية',
    cities: [
      { value: 'Shibin El Kom', ar: 'شبين الكوم' },
      { value: 'Sadat City', ar: 'مدينة السادات' },
    ],
  },
  {
    slug: 'kafr_el_sheikh', en: 'Kafr El Sheikh', ar: 'كفر الشيخ',
    cities: [
      { value: 'Kafr El Sheikh City', ar: 'كفر الشيخ' },
      { value: 'Desouk', ar: 'دسوق' },
    ],
  },
  {
    slug: 'damietta', en: 'Damietta', ar: 'دمياط',
    cities: [
      { value: 'Damietta City', ar: 'دمياط' },
      { value: 'New Damietta', ar: 'دمياط الجديدة' },
    ],
  },
  { slug: 'port_said', en: 'Port Said', ar: 'بورسعيد', cities: [{ value: 'Port Said City', ar: 'بورسعيد' }] },
  { slug: 'ismailia', en: 'Ismailia', ar: 'الإسماعيلية', cities: [{ value: 'Ismailia City', ar: 'الإسماعيلية' }] },
  { slug: 'suez', en: 'Suez', ar: 'السويس', cities: [{ value: 'Suez City', ar: 'السويس' }] },
  { slug: 'north_sinai', en: 'North Sinai', ar: 'شمال سيناء', cities: [{ value: 'Arish', ar: 'العريش' }] },
  {
    slug: 'south_sinai', en: 'South Sinai', ar: 'جنوب سيناء',
    cities: [
      { value: 'Sharm El Sheikh', ar: 'شرم الشيخ' },
      { value: 'Dahab', ar: 'دهب' },
    ],
  },
  {
    slug: 'red_sea', en: 'Red Sea', ar: 'البحر الأحمر',
    cities: [
      { value: 'Hurghada', ar: 'الغردقة' },
      { value: 'Marsa Alam', ar: 'مرسى علم' },
      { value: 'El Gouna', ar: 'الجونة' },
      { value: 'Sahl Hasheesh', ar: 'سهل حشيش' },
    ],
  },
  {
    slug: 'matrouh', en: 'Matrouh', ar: 'مطروح',
    cities: [
      { value: 'Marsa Matrouh', ar: 'مرسى مطروح' },
      { value: 'North Coast', ar: 'الساحل الشمالي' },
      { value: 'New Alamein', ar: 'العلمين الجديدة' },
      { value: 'Sidi Abdel Rahman', ar: 'سيدي عبد الرحمن' },
    ],
  },
  { slug: 'new_valley', en: 'New Valley', ar: 'الوادي الجديد', cities: [{ value: 'Kharga', ar: 'الخارجة' }] },
  { slug: 'fayoum', en: 'Fayoum', ar: 'الفيوم', cities: [{ value: 'Fayoum City', ar: 'الفيوم' }] },
  { slug: 'beni_suef', en: 'Beni Suef', ar: 'بني سويف', cities: [{ value: 'Beni Suef City', ar: 'بني سويف' }] },
  { slug: 'minya', en: 'Minya', ar: 'المنيا', cities: [{ value: 'Minya City', ar: 'المنيا' }] },
  { slug: 'assiut', en: 'Assiut', ar: 'أسيوط', cities: [{ value: 'Assiut City', ar: 'أسيوط' }] },
  { slug: 'sohag', en: 'Sohag', ar: 'سوهاج', cities: [{ value: 'Sohag City', ar: 'سوهاج' }] },
  { slug: 'qena', en: 'Qena', ar: 'قنا', cities: [{ value: 'Qena City', ar: 'قنا' }] },
  { slug: 'luxor', en: 'Luxor', ar: 'الأقصر', cities: [{ value: 'Luxor City', ar: 'الأقصر' }] },
  { slug: 'aswan', en: 'Aswan', ar: 'أسوان', cities: [{ value: 'Aswan City', ar: 'أسوان' }] },
];
