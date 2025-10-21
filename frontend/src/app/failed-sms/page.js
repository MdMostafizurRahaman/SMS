'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function FailedSMSPage(){
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(()=>{
    const checkAuth = async ()=>{
      const token = localStorage.getItem('token');
      if(!token) return router.push('/login');
      try{
        const res = await fetch(`${API_BASE_URL}/users/me`, { headers: { Authorization: `Bearer ${token}` } });
        if(!res.ok){ localStorage.removeItem('token'); return router.push('/login'); }
      }catch(e){ localStorage.removeItem('token'); return router.push('/login'); }
    }
    checkAuth();
  },[router]);

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const backToHome = ()=> router.push('/');

  const fetchItems = async ()=>{
    setLoading(true);
    try{
      const res = await fetch(`${API_BASE_URL}/failed-sms`,{headers:{'Authorization':`Bearer ${token}`}});
      const j = await res.json();
      setItems(j);
    }catch(e){
      setItems([]);
    }
    setLoading(false);
  }

  useEffect(()=>{ fetchItems() },[])

  const toggle = (id)=>{
    const s = new Set(selected);
    if(s.has(id)) s.delete(id); else s.add(id);
    setSelected(s);
  }

  const resendSelected = async ()=>{
    if(selected.size === 0) return alert('Select at least one');
    setLoading(true);
    const ids = Array.from(selected);
    const res = await fetch(`${API_BASE_URL}/failed-sms/resend`,{
      method:'POST',
      headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
      body: JSON.stringify({ids})
    });
    const j = await res.json();
    alert(JSON.stringify(j));
    await fetchItems();
    setSelected(new Set());
    setLoading(false);
  }

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <button className="btn btn-sm btn-outline-secondary me-2" onClick={()=>router.back()}>Back</button>
          <button className="btn btn-sm btn-outline-primary" onClick={backToHome}>Home</button>
        </div>
        <h3 className="mb-0">Failed SMS Management</h3>
      </div>
      <div className="card p-3">
        <div className="mb-3">
          <button className="btn btn-primary me-2" onClick={fetchItems} disabled={loading}>{loading? 'Loading...' : 'Refresh'}</button>
          <button className="btn btn-success" onClick={resendSelected} disabled={loading}>{loading? 'Working...' : 'Resend Selected'}</button>
        </div>

        <div style={{maxHeight:400, overflow:'auto'}}>
          <table className="table table-sm">
            <thead>
              <tr><th></th><th>Number</th><th>Message</th><th>Created At</th><th>Resolved</th></tr>
            </thead>
            <tbody>
              {items.map(it=> (
                <tr key={it.id} className={it.resolved? 'table-success': ''}>
                  <td><input type="checkbox" checked={selected.has(it.id)} onChange={()=>toggle(it.id)} /></td>
                  <td>{it.original_number || it.normalized}</td>
                  <td><small style={{whiteSpace:'pre-wrap'}}>{it.message}</small></td>
                  <td>{it.created_at}</td>
                  <td>{String(it.resolved)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
