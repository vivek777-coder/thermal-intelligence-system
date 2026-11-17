/**
 * Shared i18n helper for the Thermal Intelligence Platform.
 *
 * Supports: English (en), Hindi (hi), Hinglish (hinglish).
 * Usage:
 *   import { t, setLocale, getLocale, Locale } from '@packages/i18n';
 *   t('app.title');                         // uses current locale
 *   t('alert.probable_cause', { confidence: 87 });  // with interpolation
 */

import en from './en.json';
import hi from './hi.json';
import hinglish from './hinglish.json';

export type Locale = 'en' | 'hi' | 'hinglish';

const locales: Record<Locale, Record<string, string>> = {
  en,
  hi,
  hinglish,
};

let currentLocale: Locale = 'en';

/**
 * Set the active locale.
 */
export function setLocale(locale: Locale): void {
  if (!(locale in locales)) {
    console.warn(`[i18n] Unknown locale "${locale}", falling back to "en".`);
    currentLocale = 'en';
    return;
  }
  currentLocale = locale;
}

/**
 * Get the active locale.
 */
export function getLocale(): Locale {
  return currentLocale;
}

/**
 * Get all available locales.
 */
export function getAvailableLocales(): Locale[] {
  return Object.keys(locales) as Locale[];
}

/**
 * Translate a key, optionally interpolating `{placeholder}` tokens.
 *
 * Falls back to English if the key is missing in the current locale,
 * and returns the raw key if not found in any locale.
 */
export function t(
  key: string,
  params?: Record<string, string | number>,
  locale?: Locale,
): string {
  const lang = locale ?? currentLocale;
  let value = locales[lang]?.[key] ?? locales.en[key] ?? key;

  if (params) {
    for (const [param, replacement] of Object.entries(params)) {
      value = value.replace(new RegExp(`\\{${param}\\}`, 'g'), String(replacement));
    }
  }

  return value;
}

export default { t, setLocale, getLocale, getAvailableLocales };
