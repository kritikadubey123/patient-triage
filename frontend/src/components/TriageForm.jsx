import { useState } from "react";

import { VITAL_LIMITS } from "../constants";
import { useSubmitTriage } from "../hooks/useSubmitTriage";
import PriorityBadge from "./PriorityBadge";

const EMPTY_VALUES = {
  patient_name: "",
  age: "",
  heart_rate: "",
  systolic_bp: "",
  temperature: "",
};

// Instant client-side checks. The backend validates again, so this is about UX,
// not security. Returns { fieldName: "message" } for every invalid field.
function validate(values) {
  const errors = {};

  const name = values.patient_name.trim();
  if (!name) errors.patient_name = "Name is required";
  else if (!/\p{L}/u.test(name)) errors.patient_name = "Name must contain a letter";

  for (const [field, { min, max, unit, integer }] of Object.entries(VITAL_LIMITS)) {
    const raw = values[field].trim();
    if (raw === "") {
      errors[field] = "Required";
      continue;
    }
    const num = Number(raw);
    if (!Number.isFinite(num)) errors[field] = "Enter a number";
    else if (integer && !Number.isInteger(num)) errors[field] = "Whole numbers only";
    else if (num < min || num > max) errors[field] = `Must be between ${min} and ${max} ${unit}`;
  }
  return errors;
}

function Field({ id, label, unit, error, children }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1 flex items-baseline justify-between text-sm font-medium">
        <span>{label}</span>
        {unit && <span className="text-xs font-normal text-slate-500">{unit}</span>}
      </label>
      {children}
      {error && (
        <p id={`${id}-error`} className="mt-1 text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

export default function TriageForm({ onSubmitted }) {
  const [values, setValues] = useState(EMPTY_VALUES);
  const [touched, setTouched] = useState({});
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const { submit, reset, isSubmitting, error, fieldErrors, result } = useSubmitTriage();

  const clientErrors = validate(values);

  // Show a client error once the field was visited (or after a submit attempt);
  // otherwise show an error that came back from the server.
  const errorFor = (field) =>
    touched[field] || submitAttempted ? clientErrors[field] ?? fieldErrors[field] : fieldErrors[field];

  const handleChange = (event) => {
    const { name, value } = event.target;
    setValues((prev) => ({ ...prev, [name]: value }));
    if (error || result) reset(); // clear stale server messages as soon as the user edits
  };

  const handleBlur = (event) => {
    setTouched((prev) => ({ ...prev, [event.target.name]: true }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitAttempted(true);
    if (Object.keys(clientErrors).length > 0) return; // don't call the API with bad data

    const created = await submit({
      patient_name: values.patient_name.trim(),
      age: Number(values.age),
      heart_rate: Number(values.heart_rate),
      systolic_bp: Number(values.systolic_bp),
      temperature: Number(values.temperature),
    });

    if (created) {
      setValues(EMPTY_VALUES);
      setTouched({});
      setSubmitAttempted(false);
      onSubmitted?.(created);
    }
  };

  const inputClass = (field) =>
    `w-full rounded-md border px-3 py-2 text-sm shadow-sm outline-none transition focus:ring-2 disabled:bg-slate-100 ${
      errorFor(field)
        ? "border-red-400 focus:border-red-500 focus:ring-red-200"
        : "border-slate-300 focus:border-blue-500 focus:ring-blue-200"
    }`;

  const inputProps = (field) => ({
    id: field,
    name: field,
    value: values[field],
    onChange: handleChange,
    onBlur: handleBlur,
    disabled: isSubmitting,
    className: inputClass(field),
    "aria-invalid": Boolean(errorFor(field)),
    "aria-describedby": errorFor(field) ? `${field}-error` : undefined,
  });

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
    >
      <h2 className="text-lg font-semibold">New patient</h2>

      <Field id="patient_name" label="Patient name" error={errorFor("patient_name")}>
        <input type="text" maxLength={100} autoComplete="off" placeholder="e.g. Asha Verma" {...inputProps("patient_name")} />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        {Object.entries(VITAL_LIMITS).map(([field, { label, unit, min, max, integer }]) => (
          <Field key={field} id={field} label={label} unit={unit} error={errorFor(field)}>
            <input
              type="number"
              inputMode={integer ? "numeric" : "decimal"}
              step={integer ? 1 : 0.1}
              min={min}
              max={max}
              placeholder={`${min}–${max}`}
              {...inputProps(field)}
            />
          </Field>
        ))}
      </div>

      {error && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && (
        <div role="status" className="rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
          <p className="mb-1 font-medium">Added {result.patient_name} to the queue</p>
          <div className="flex items-center gap-2">
            <PriorityBadge priority={result.prediction.predicted_priority} />
            <span>{Math.round(result.prediction.confidence_score * 100)}% confidence</span>
          </div>
        </div>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="flex w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:cursor-not-allowed disabled:bg-blue-400"
      >
        {isSubmitting && (
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
            aria-hidden="true"
          />
        )}
        {isSubmitting ? "Assessing…" : "Assess priority"}
      </button>
    </form>
  );
}