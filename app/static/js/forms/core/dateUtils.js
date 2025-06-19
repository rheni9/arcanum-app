/**
 * @file dateUtils.js
 * @description
 * Date and time validation and comparison utilities for Arcanum forms.
 * Includes functions to validate format, compare dates, and convert local
 * Europe/Kyiv input to UTC timestamps for consistency.
 */

import { isEmpty } from "./baseUtils.js";

/* ============================================================================
   Format Validation
============================================================================ */

/**
 * Validates whether the input is a real calendar date in YYYY-MM-DD format.
 * 
 *  Supports: YYYY-MM-DD, DD/MM/YYYY, D.M.YYYY, D.M.YY.
 *
 * @param {string} dateStr - The input string to check.
 * @returns {{ valid: boolean, reason?: string }} Validation result and reason.
 */
/**
 * Attempts to validate and parse a date from allowed formats.
 *
 * @param {string} dateStr - The input string to check.
 * @returns {{ valid: boolean, reason?: string, normalized?: string }} Result info.
 */
export function isDateValid(dateStr) {
  if (isEmpty(dateStr)) return { valid: false, reason: "empty" };

  const formats = [
    {
      name: "YYYY-MM-DD",
      regex: /^(\d{4})-(\d{2})-(\d{2})$/,
      parse: (m) => [Number(m[1]), Number(m[2]), Number(m[3])]
    },
    {
      name: "DD/MM/YYYY",
      regex: /^(\d{2})\/(\d{2})\/(\d{4})$/,
      parse: (m) => [Number(m[3]), Number(m[2]), Number(m[1])]
    },
    {
      name: "D.M.YYYY",
      regex: /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/,
      parse: (m) => [Number(m[3]), Number(m[2]), Number(m[1])]
    },
    {
      name: "D.M.YY",
      regex: /^(\d{1,2})\.(\d{1,2})\.(\d{2})$/,
      parse: (m) => {
        const yy = Number(m[3]);
        const fullYear = yy + (yy < 50 ? 2000 : 1900);
        return [fullYear, Number(m[2]), Number(m[1])];
      }
    }
  ];

  for (const format of formats) {
    const match = dateStr.match(format.regex);
    if (match) {
      const [year, month, day] = format.parse(match);
      const date = new Date(year, month - 1, day);
      if (
        date.getFullYear() === year &&
        date.getMonth() === month - 1 &&
        date.getDate() === day
      ) {
        // Return the normalized date in YYYY-MM-DD format
        const norm = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
        return { valid: true, normalized: norm };
      } else {
        return { valid: false, reason: "calendar" };
      }
    }
  }

  return { valid: false, reason: "format" };
}


/**
 * Validates whether the input is a proper 24-hour time (HH:MM or HH:MM:SS).
 *
 * @param {string} timeStr - The input string to check.
 * @returns {boolean} True if valid time format.
 */
export function isTimeValid(timeStr) {
  const parts = timeStr.split(":").map(Number);
  if (parts.length < 2 || parts.length > 3) return false;

  const [h, m, s = 0] = parts;
  return (
    Number.isInteger(h) && h >= 0 && h < 24 &&
    Number.isInteger(m) && m >= 0 && m < 60 &&
    Number.isInteger(s) && s >= 0 && s < 60
  );
}

/**
 * Compares two YYYY-MM-DD date strings.
 *
 * @param {string} start - Start date.
 * @param {string} end - End date.
 * @returns {boolean} True if start is before or equal to end.
 */
export function compareDates(start, end) {
  const a = new Date(start);
  const b = new Date(end);
  return a <= b;
}

/* ============================================================================
   Date/Time Comparison with UTC Now (Europe/Kyiv Aware)
============================================================================ */

/**
 * Converts a Europe/Kyiv-local date and time string to a UTC Date object.
 *
 * @param {string} dateStr - Date in YYYY-MM-DD format.
 * @param {string} [timeStr="00:00"] - Time in HH:MM[:SS] format.
 * @returns {Date} UTC Date object.
 */
export function getKyivDateTime(dateStr, timeStr = "00:00") {
  const [year, month, day] = dateStr.split("-").map(Number);
  const [hour, minute, second = "00"] = timeStr.split(":").map(Number);

  // Create naive UTC date based on input
  const naiveUTC = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
  const offsetMillis = getKyivOffsetMillis(naiveUTC);

  // Subtract Kyiv offset to get actual UTC time
  return new Date(naiveUTC.getTime() - offsetMillis);
}

/**
 * Computes UTC offset (in milliseconds) for Europe/Kyiv at a given UTC date.
 *
 * @param {Date} utcDate - The date to compute Kyiv offset for.
 * @returns {number} Offset in milliseconds.
 */
export function getKyivOffsetMillis(utcDate) {
  const fmt = new Intl.DateTimeFormat("en-US", {
    timeZone: "Europe/Kyiv",
    timeZoneName: "short"
  });

  const tzPart = fmt.formatToParts(utcDate).find(p => p.type === "timeZoneName");
  const match = tzPart?.value?.match(/GMT([+-]\d+)/);
  const offsetHours = match ? parseInt(match[1], 10) : 0;

  return offsetHours * 60 * 60 * 1000;
}

/**
 * Checks if a given date and optional time (Kyiv local) is in the past or now
 * compared to current UTC timestamp.
 *
 * @param {string} dateStr - Date in YYYY-MM-DD format.
 * @param {string|null} [timeStr=null] - Time in HH:MM or HH:MM:SS (optional).
 * @returns {boolean} True if not in the future.
 */
export function isPastOrNow(dateStr, timeStr = null) {
  if (isEmpty(dateStr)) return true;
  if (!isDateValid(dateStr)) return false;
  if (timeStr && !isTimeValid(timeStr)) return false;

  const submitted = getKyivDateTime(dateStr, timeStr || "00:00");
  const now = new Date();

  return submitted <= now;
}
