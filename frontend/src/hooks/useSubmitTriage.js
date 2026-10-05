import { useCallback, useState } from "react";

import { createTriage } from "../services/api";

/** Wraps POST /api/triage with loading, error, per-field error and result state. */
export function useSubmitTriage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [result, setResult] = useState(null);

  // Resolves to the created record on success, or null on failure.
  const submit = useCallback(async (payload) => {
    setIsSubmitting(true);
    setError(null);
    setFieldErrors({});
    setResult(null);
    try {
      const data = await createTriage(payload);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      setFieldErrors(err.fieldErrors ?? {});
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const reset = useCallback(() => {
    setError(null);
    setFieldErrors({});
    setResult(null);
  }, []);

  return { submit, reset, isSubmitting, error, fieldErrors, result };
}