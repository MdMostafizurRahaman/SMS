'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function SingleSMSPage() {
  const [numbers, setNumbers] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (!token) return router.push('/login');
      try {
        const res = await fetch(`${API_BASE_URL}/users/me`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) {
          localStorage.removeItem('token');
          return router.push('/login');
        }
      } catch (e) {
        localStorage.removeItem('token');
        return router.push('/login');
      }
    };
    checkAuth();
  }, [router]);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const backToHome = ()=> router.push('/');

  const send = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/send-manual`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ numbers, message }),
      });
      const json = await res.json();
      // Present a friendly summary instead of raw JSON
      if (res.ok) {
        const sent = json.sent_count || 0;
        const failed = json.failed_count || 0;
        const successList = json.successful_recipients || [];
        const failedList = json.failed_recipients || [];
        setResult({ sent, failed, successList, failedList, raw: json });
      } else {
        setResult({ error: json.detail || JSON.stringify(json) });
      }
    } catch (e) {
      setResult({ error: 'Network error' });
    }
    setLoading(false);
  };

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <button className="btn btn-sm btn-outline-secondary me-2" onClick={()=>router.back()}>Back</button>
          <button className="btn btn-sm btn-outline-primary" onClick={backToHome}>Home</button>
        </div>
        <h3 className="mb-0">Single / Multiple SMS</h3>
      </div>
      <div className="card p-3">
        <div className="mb-3">
          <label className="form-label">Numbers (comma or newline separated)</label>
          <textarea className="form-control" rows={4} value={numbers} onChange={(e)=>setNumbers(e.target.value)} />
        </div>
        <div className="mb-3">
          <label className="form-label">Message</label>
          <textarea className="form-control" rows={4} value={message} onChange={(e)=>setMessage(e.target.value)} />
        </div>
        <div className="d-flex gap-2">
          <button className="btn btn-primary" onClick={send} disabled={loading}>{loading ? 'Sending...' : 'Send SMS'}</button>
        </div>
        {result && (
          <div className="mt-3">
            {result.error ? (
              <div className="alert alert-danger">{result.error}</div>
            ) : (
              <>
                <div className={`alert ${result.failed === 0 ? 'alert-success' : 'alert-warning'}`}>
                  <strong>{result.failed === 0 ? 'Send successful' : 'Partially sent'}</strong>
                  <div>Sent: {result.sent} &nbsp;|&nbsp; Failed: {result.failed}</div>
                </div>

                {result.successList && result.successList.length > 0 && (
                  <div className="card mb-2 p-2">
                    <h6 className="mb-2">Successful recipients</h6>
                    <ul className="list-unstyled mb-0">
                      {result.successList.map((s, i) => (
                        <li key={i} className="py-1">
                          <strong>{s.number || s.normalized}</strong>
                          <div className="small text-muted">Message: {message}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.failedList && result.failedList.length > 0 && (
                  <div className="card p-2">
                    <h6 className="mb-2">Failed recipients</h6>
                    <ul className="list-unstyled mb-0">
                      {result.failedList.map((f, i) => (
                        <li key={i} className="py-1 text-danger">
                          <strong>{f.original_number || f.number || f.normalized}</strong>
                          <div className="small text-muted">Reason: {f.info || JSON.stringify(f)}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
