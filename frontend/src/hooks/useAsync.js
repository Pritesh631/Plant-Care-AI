import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../services/api.js'

/** Runs an async loader on mount; exposes data, loading, error and reload. */
export default function useAsync(loader) {
  const [state, setState] = useState({ data: null, loading: true, error: null })

  const run = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      setState({ data: await loader(), loading: false, error: null })
    } catch (err) {
      setState({ data: null, loading: false, error: errorMessage(err) })
    }
  }, [loader])

  useEffect(() => { run() }, [run])

  return { ...state, reload: run }
}
