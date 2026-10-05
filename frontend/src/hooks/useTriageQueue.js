import { useCallback, useEffect, useRef, useState } from "react";

import { fetchQueue } from "../services/api";

/**
 * Loads the prioritised queue and refreshes it every `pollMs` milliseconds.
 *
 * - `isLoading` is true only until the FIRST response, so the table never
 *   flashes a skeleton on every poll.
 * - If a later poll fails, the last good data stays on screen and `error` is set.
 */
export function useTriageQueue(pollMs = 5000) {
  const [queue, setQueue] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const controllerRef = useRef(null);

  const load = useCallback(async () => {
    // Cancel any request still in flight so a slow, old response can never
    // overwrite a newer one.
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const data = await fetchQueue(controller.signal);
      setQueue(data);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      if (err.name === "AbortError") return;
      setError(err.message);
    } finally {
      if (!controller.signal.aborted) setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const intervalId = setInterval(load, pollMs);
    return () => {
      clearInterval(intervalId);
      controllerRef.current?.abort();
    };
  }, [load, pollMs]);

  return { queue, isLoading, error, lastUpdated, refresh: load };
}