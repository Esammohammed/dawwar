import React from 'react';
import { Search, RotateCcw } from 'lucide-react';
import { useFilterStore } from '../stores/filterStore';
import { useTranslation } from '../i18n/i18nContext';
import { GovernorateSelect, CitySelect } from './LocationSelects';
import styles from './FilterBar.module.css';

const FilterBar = ({ onSearch }) => {
  const { t } = useTranslation();
  const {
    type, governorate, city, minPrice, maxPrice, bedrooms, finishing, hasInstallments,
    setFilter, resetFilters
  } = useFilterStore();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (onSearch) onSearch();
  };

  const handleGovernorateChange = (e) => {
    setFilter('governorate', e.target.value);
    setFilter('city', '');
  };

  return (
    <form className={styles.wrapper} onSubmit={handleSearchSubmit}>
      <div className={styles.grid}>
        
        <div className={styles.fieldGroup}>
          <label className={styles.label}>{t('filter.propertyType')}</label>
          <select value={type} onChange={(e) => setFilter('type', e.target.value)} className={styles.select}>
            <option value="">{t('filter.allTypes')}</option>
            <option value="resale">{t('filter.resale')}</option>
            <option value="developer_unit">{t('filter.developerUnit')}</option>
          </select>
        </div>

        <div className={styles.fieldGroup}>
          <label className={styles.label}>{t('filter.governorate')}</label>
          <GovernorateSelect
            value={governorate}
            onChange={handleGovernorateChange}
            className={styles.select}
            placeholder={t('filter.allGovs')}
          />
        </div>

        <div className={styles.fieldGroup}>
          <label className={styles.label}>{t('filter.city')}</label>
          <CitySelect
            governorate={governorate}
            value={city}
            onChange={(e) => setFilter('city', e.target.value)}
            className={styles.select}
            placeholder={t('filter.allCities')}
          />
        </div>

        <div className={styles.fieldGroup}>
          <label className={styles.label}>{t('filter.bedrooms')}</label>
          <select value={bedrooms} onChange={(e) => setFilter('bedrooms', e.target.value)} className={styles.select}>
            <option value="">{t('filter.anyBedrooms')}</option>
            <option value="1">1</option>
            <option value="2">2</option>
            <option value="3">3</option>
            <option value="4">4+</option>
          </select>
        </div>

        <div className={styles.fieldGroup}>
          <label className={styles.label}>{t('filter.maxPrice')}</label>
          <input
            type="number"
            placeholder="e.g. 3000000"
            value={maxPrice}
            onChange={(e) => setFilter('maxPrice', e.target.value)}
            className={styles.input}
          />
        </div>

        <div className={styles.checkboxGroup}>
          <input
            type="checkbox"
            id="installments"
            checked={hasInstallments}
            onChange={(e) => setFilter('hasInstallments', e.target.checked)}
            className={styles.checkbox}
          />
          <label htmlFor="installments" className={styles.label}>{t('filter.installmentsOnly')}</label>
        </div>

        <div className={styles.btnGroup}>
          <button type="submit" className={styles.searchBtn}>
            <Search size={18} />
            {t('filter.search')}
          </button>
          <button type="button" onClick={resetFilters} className={styles.resetBtn} title={t('filter.reset')}>
            <RotateCcw size={18} />
          </button>
        </div>

      </div>
    </form>
  );
};

export default FilterBar;
