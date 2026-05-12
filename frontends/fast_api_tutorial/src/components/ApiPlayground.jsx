import { useState, useRef } from 'react'
import { BASE_URL } from '../topics.js'

function syntaxHighlight(json) {
  if (typeof json !== 'string') json = JSON.stringify(json, null, 2)
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    match => {
      if (/^"/.test(match)) {
        return /:$/.test(match)
          ? `<span class="json-key">${match}</span>`
          : `<span class="json-string">${match}</span>`
      }
      if (/true|false/.test(match)) return `<span class="json-bool">${match}</span>`
      if (/null/.test(match)) return `<span class="json-null">${match}</span>`
      return `<span class="json-number">${match}</span>`
    }
  )
}

function buildUrl(path, fields, values) {
  let url = BASE_URL + path
  const pathFields = fields.filter(f => f.in === 'path')
  for (const f of pathFields) {
    const val = values[f.name]
    if (val !== undefined && val !== '') {
      url = url.replace(`{${f.name}}`, encodeURIComponent(val))
    }
  }
  const queryFields = fields.filter(f => f.in === 'query')
  const params = new URLSearchParams()
  for (const f of queryFields) {
    const val = values[f.name]
    if (val !== undefined && val !== '') {
      if (f.name === 'q-list') {
        val.split(',').forEach(v => params.append('q-list', v.trim()))
      } else {
        params.set(f.name, val)
      }
    }
  }
  const qs = params.toString()
  if (qs) url += '?' + qs
  return url
}

function FileInput({ name, onChange }) {
  const [fileName, setFileName] = useState(null)
  const ref = useRef()

  function handleChange(e) {
    const file = e.target.files[0]
    setFileName(file ? file.name : null)
    onChange(name, file ?? null)
  }

  return (
    <div className="file-input-wrapper">
      <div className={`file-input-display ${fileName ? 'has-file' : ''}`}>
        <span>📎</span>
        <span>{fileName ?? 'Choose file…'}</span>
      </div>
      <input type="file" ref={ref} onChange={handleChange} />
    </div>
  )
}

export default function ApiPlayground({ endpoint }) {
  const [values, setValues] = useState({})
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [streamLines, setStreamLines] = useState([])

  function set(name, val) {
    setValues(v => ({ ...v, [name]: val }))
  }

  async function send() {
    setLoading(true)
    setResponse(null)
    setStreamLines([])

    const url = buildUrl(endpoint.path, endpoint.fields, values)
    const method = endpoint.method
    const headers = {}

    // Custom headers from header fields
    for (const f of endpoint.fields.filter(f => f.in === 'header')) {
      const val = values[f.name]
      if (val !== undefined && val !== '') {
        headers[f.name] = val
      }
    }

    let body = undefined

    const bodyField = endpoint.fields.find(f => f.in === 'body')
    const formFields = endpoint.fields.filter(f => f.in === 'form')
    const fileFields = endpoint.fields.filter(f => f.in === 'file')

    if (bodyField) {
      try {
        body = JSON.stringify(JSON.parse(values[bodyField.name] ?? '{}'))
        headers['Content-Type'] = 'application/json'
      } catch {
        setResponse({ error: 'Invalid JSON in body', status: null, time: null })
        setLoading(false)
        return
      }
    } else if (formFields.length > 0 || fileFields.length > 0) {
      const fd = new FormData()
      for (const f of formFields) {
        const val = values[f.name]
        if (val !== undefined && val !== '') fd.append(f.name, val)
      }
      for (const f of fileFields) {
        const file = values[f.name]
        if (file) fd.append(f.name, file)
      }
      body = fd
    }

    const t0 = performance.now()
    try {
      if (endpoint.streaming) {
        const res = await fetch(url, { method, headers, credentials: 'include' })
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        const elapsed = Math.round(performance.now() - t0)
        setResponse({ status: res.status, ok: res.ok, time: elapsed, streaming: true })
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value)
          setStreamLines(l => [...l, text.trim()])
        }
      } else {
        const res = await fetch(url, { method, headers, body, credentials: 'include' })
        const elapsed = Math.round(performance.now() - t0)
        let data
        const contentType = res.headers.get('content-type') ?? ''
        if (contentType.includes('application/json')) {
          data = await res.json()
        } else {
          data = await res.text()
        }
        setResponse({ status: res.status, ok: res.ok, time: elapsed, data })
      }
    } catch (err) {
      setResponse({ error: String(err), status: null, time: null })
    } finally {
      setLoading(false)
    }
  }

  const pathFields = endpoint.fields.filter(f => f.in === 'path')
  const queryFields = endpoint.fields.filter(f => f.in === 'query')
  const headerFields = endpoint.fields.filter(f => f.in === 'header')
  const bodyField = endpoint.fields.find(f => f.in === 'body')
  const formFields = endpoint.fields.filter(f => f.in === 'form')
  const fileFields = endpoint.fields.filter(f => f.in === 'file')

  return (
    <div className="playground-card">
      <div className="playground-card-header">
        <span className={`playground-card-method ${endpoint.method}`}>{endpoint.method}</span>
        <span className="playground-card-path">{endpoint.path}</span>
        {endpoint.label && (
          <span className="playground-card-label">{endpoint.label}</span>
        )}
      </div>
      <div className="playground-body">

        {endpoint.note && (
          <div className="info-card" style={{ padding: '10px 14px', fontSize: '12px' }}>
            ℹ️ {endpoint.note}
          </div>
        )}

        {pathFields.length > 0 && (
          <FieldSection title="Path" fields={pathFields} values={values} onChange={set} />
        )}
        {queryFields.length > 0 && (
          <FieldSection title="Query" fields={queryFields} values={values} onChange={set} />
        )}
        {headerFields.length > 0 && (
          <FieldSection title="Headers" fields={headerFields} values={values} onChange={set} />
        )}
        {formFields.length > 0 && (
          <FieldSection title="Form" fields={formFields} values={values} onChange={set} />
        )}
        {fileFields.length > 0 && (
          <div className="fields-section">
            <div className="fields-section-title">File</div>
            {fileFields.map(f => (
              <div key={f.name} className="field-row">
                <div className="field-label">
                  <span className="field-name">{f.name}</span>
                  {f.required && <span className="field-required">required</span>}
                </div>
                <FileInput name={f.name} onChange={set} />
              </div>
            ))}
          </div>
        )}
        {bodyField && (
          <div className="fields-section">
            <div className="fields-section-title">Request Body (JSON)</div>
            <textarea
              className="field-input"
              style={{ minHeight: 120 }}
              placeholder={bodyField.placeholder}
              value={values[bodyField.name] ?? ''}
              onChange={e => set(bodyField.name, e.target.value)}
            />
          </div>
        )}

        <button className="send-btn" onClick={send} disabled={loading}>
          {loading ? '⏳ Sending…' : `▶ Send ${endpoint.method}`}
        </button>

        {response && (
          <div className="response-section">
            <div className="divider" />
            <div className="response-header">
              {response.error ? (
                <span className="response-status err">Network Error</span>
              ) : (
                <span className={`response-status ${response.ok ? 'ok' : 'err'}`}>
                  {response.status}
                </span>
              )}
              {response.time != null && (
                <span className="response-time">{response.time} ms</span>
              )}
            </div>

            {response.streaming ? (
              <div className="stream-output">
                {streamLines.map((line, i) => (
                  <span key={i} className="stream-line">{line}</span>
                ))}
                {loading && <span className="stream-line" style={{ opacity: 0.5 }}>…</span>}
              </div>
            ) : response.error ? (
              <div className="response-body" style={{ color: 'var(--error)' }}>
                {response.error}
              </div>
            ) : (
              <div
                className="response-body"
                dangerouslySetInnerHTML={{
                  __html: typeof response.data === 'string'
                    ? response.data
                    : syntaxHighlight(response.data),
                }}
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function FieldSection({ title, fields, values, onChange }) {
  return (
    <div className="fields-section">
      <div className="fields-section-title">{title}</div>
      {fields.map(f => (
        <div key={f.name} className="field-row">
          <div className="field-label">
            <span className="field-name">{f.name}</span>
            <span className="field-in">{f.in}</span>
            {f.required && <span className="field-required">required</span>}
          </div>
          {f.type === 'select' ? (
            <select
              className="field-input"
              value={values[f.name] ?? f.options[0]}
              onChange={e => onChange(f.name, e.target.value)}
            >
              {f.options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          ) : (
            <input
              className="field-input"
              type={f.type === 'number' ? 'text' : 'text'}
              placeholder={f.placeholder ?? ''}
              value={values[f.name] ?? ''}
              onChange={e => onChange(f.name, e.target.value)}
            />
          )}
        </div>
      ))}
    </div>
  )
}
