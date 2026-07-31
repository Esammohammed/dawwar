import React from 'react';
import { Building2, Phone, Mail, MapPin } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          
          {/* Brand Col */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-white">
                <Building2 className="w-6 h-6" />
              </div>
              <span className="text-2xl font-bold text-white">دوّار</span>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              سوق العقارات الأسرع نمواً في مصر. نربط البائع بالمشتري مباشرة مع متابعة فورية للأطروحات الحكومية والمشروعات السكنية.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-white font-bold mb-4">روابط سريعة</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><a href="/listings" className="hover:text-sky-400 transition-colors">عقارات إعادة البيع</a></li>
              <li><a href="/projects" className="hover:text-sky-400 transition-colors">مشروعات المطورين</a></li>
              <li><a href="/gov-news" className="hover:text-sky-400 transition-colors">أخبار وطروحات الإسكان</a></li>
              <li><a href="/sell" className="hover:text-sky-400 transition-colors">أضف عقارك مجاناً</a></li>
            </ul>
          </div>

          {/* Governorates */}
          <div>
            <h4 className="text-white font-bold mb-4">أشهر المدن</h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li><a href="/listings?city=6%20أكتوبر" className="hover:text-sky-400 transition-colors">6 أكتوبر والشيخ زايد</a></li>
              <li><a href="/listings?city=القاهرة%20الجديدة" className="hover:text-sky-400 transition-colors">القاهرة الجديدة والتجمع</a></li>
              <li><a href="/listings?city=العاصمة%20الإدارية" className="hover:text-sky-400 transition-colors">العاصمة الإدارية الجديدة</a></li>
              <li><a href="/listings?city=الشروق" className="hover:text-sky-400 transition-colors">الشروق وبدر</a></li>
            </ul>
          </div>

          {/* Contact info */}
          <div>
            <h4 className="text-white font-bold mb-4">تواصل معنا</h4>
            <div className="space-y-3 text-sm text-slate-400">
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-sky-400" />
                <span>+20 100 000 0000</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-sky-400" />
                <span>support@dawwar.eg</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-sky-400" />
                <span>القاهرة، جمهورية مصر العربية</span>
              </div>
            </div>
          </div>

        </div>

        <div className="pt-8 border-t border-slate-800 text-center text-xs text-slate-500">
          © {new Date().getFullYear()} دوّار (Dawwar). جميع الحقوق محفوظة.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
