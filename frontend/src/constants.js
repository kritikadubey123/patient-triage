// Client-side mirror of VITAL_LIMITS in backend/schemas.py (and BOUNDS in train.py).
// The backend is the source of truth and always re-validates; these limits only
// give the user instant feedback. If you change one place, change all three.
export const VITAL_LIMITS = {
  age: { label: "Age", min: 0, max: 110, unit: "years", integer: true },
  heart_rate: { label: "Heart rate", min: 30, max: 220, unit: "bpm", integer: true },
  systolic_bp: { label: "Systolic BP", min: 50, max: 260, unit: "mmHg", integer: true },
  temperature: { label: "Temperature", min: 32, max: 43, unit: "°C", integer: false },
};