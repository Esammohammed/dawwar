import React, { useEffect, useState } from 'react';
import { useTranslation } from '../i18n/i18nContext';
import { GOVERNORATES } from '../constants/egyptLocations';
import styles from './LocationSelects.module.css';

const OTHER_VALUE = '__other__';

// mode="listing" (default): option values are the English display strings used
//   by Listing.governorate/city and User.city — free-text backend fields.
// mode="profile": option values are the slugs backing the validated
//   User.governorate choices field.
const keyFor = (gov, mode) => (mode === 'profile' ? gov.slug : gov.en);

export const GovernorateSelect = ({
  value, onChange, className, name = 'governorate', required = false, mode = 'listing', placeholder,
}) => {
  const { t, language } = useTranslation();
  return (
    <select name={name} value={value} onChange={onChange} className={className} required={required}>
      <option value="">{placeholder || t('location.selectGovernorate')}</option>
      {GOVERNORATES.map((gov) => (
        <option key={gov.slug} value={keyFor(gov, mode)}>
          {language === 'ar' ? gov.ar : gov.en}
        </option>
      ))}
    </select>
  );
};

export const CitySelect = ({
  governorate, value, onChange, className, name = 'city', required = false, mode = 'listing', placeholder,
}) => {
  const { t, language } = useTranslation();
  const cities = GOVERNORATES.find((gov) => keyFor(gov, mode) === governorate)?.cities || [];
  const isKnownCity = !value || cities.some((city) => city.value === value);
  const [otherMode, setOtherMode] = useState(!isKnownCity);

  // A fresh (empty) value means the caller reset the city, e.g. after the
  // governorate changed — drop back to the dropdown until something is picked.
  useEffect(() => {
    if (!value) setOtherMode(false);
  }, [governorate]); // eslint-disable-line react-hooks/exhaustive-deps

  const emit = (newValue) => onChange({ target: { name, value: newValue } });

  const handleSelectChange = (e) => {
    if (e.target.value === OTHER_VALUE) {
      setOtherMode(true);
      emit('');
    } else {
      emit(e.target.value);
    }
  };

  if (otherMode) {
    return (
      <div className={styles.otherWrap}>
        <input
          type="text"
          name={name}
          value={value}
          onChange={onChange}
          placeholder={t('location.otherCityPlaceholder')}
          className={className}
          required={required}
          disabled={!governorate}
        />
        <button type="button" className={styles.backLink} onClick={() => { setOtherMode(false); emit(''); }}>
          {t('location.backToList')}
        </button>
      </div>
    );
  }

  return (
    <select
      name={name}
      value={value}
      onChange={handleSelectChange}
      className={className}
      required={required}
      disabled={!governorate}
    >
      <option value="">
        {placeholder || (governorate ? t('location.selectCity') : t('location.selectGovernorateFirst'))}
      </option>
      {cities.map((city) => (
        <option key={city.value} value={city.value}>
          {language === 'ar' ? city.ar : city.value}
        </option>
      ))}
      {governorate && <option value={OTHER_VALUE}>{t('location.otherCity')}</option>}
    </select>
  );
};
