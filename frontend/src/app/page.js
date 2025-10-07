'use client';

import { useState } from 'react';
import Image from 'next/image';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState([]);
  const [selectedIndices, setSelectedIndices] = useState([]);
  const [message, setMessage] = useState([]);
  const [loading, setLoading] = useState(false);
  const [balance, setBalance] = useState(null);

  const checkBalance = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/balance`);
      const result = await response.json();
      if (response.ok) {
        setBalance(result.balance);
      } else {
        setMessage(result.detail);
      }
    } catch (error) {
      setMessage('Error checking balance');
    }
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    // Reset selections when new file is uploaded
    setSelectedIndices([]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (response.ok) {
        setData(result.data);
        // Auto-select all rows by default
        setSelectedIndices(result.data.map((_, index) => index));
        setMessage('');
      } else {
        setMessage(result.detail);
      }
    } catch (error) {
      setMessage('Error uploading file');
    }
    setLoading(false);
  };

  const handleRowSelect = (index) => {
    setSelectedIndices(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else {
        return [...prev, index];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedIndices.length === data.length) {
      setSelectedIndices([]);
    } else {
      setSelectedIndices(data.map((_, index) => index));
    }
  };

  const handleSendSMS = async () => {
    if (selectedIndices.length === 0) {
      setMessage('Please select at least one row to send SMS');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/send-sms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          data: data,
          selectedIndices: selectedIndices
        }),
      });
      const result = await response.json();
      setMessage(result.message);
    } catch (error) {
      setMessage('Error sending SMS');
    }
    setLoading(false);
  };

  const getPhoneDisplay = (row) => {
    const studentPhone = row['Student Phone No'];
    const guardianPhone = row['Guardian Phone No'];

    if (studentPhone && guardianPhone) {
      return `${studentPhone} / ${guardianPhone}`;
    } else if (studentPhone) {
      return studentPhone;
    } else if (guardianPhone) {
      return guardianPhone;
    }
    return '';
  };

  return (
    <div className="min-h-screen bg-light">
      <div className="container-lg py-4">
        <header className="text-center mb-4">
          <div className="d-flex flex-column align-items-center">
            <Image
              src="/Big Bang logo-icn.png"
              alt="SMS Sender logo"
              className="img-fluid mb-3"
              width={320}
              height={200}
              style={{ maxHeight: '120px', width: 'auto', height: 'auto' }}
            />
            <h2 className="text-primary fw-bold mb-1" style={{ fontSize: '2rem' }}>
              SMS Sender
            </h2>
            <div className="text-muted fs-5">
              Excel Upload & SMS Dispatch
            </div>
          </div>
        </header>

        <div className="row justify-content-center">
          <div className="col-md-10">
            <div className="card shadow p-4">
              <h4 className="card-title text-center mb-4">Upload Excel File</h4>
              <div className="mb-3">
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  onChange={handleFileChange}
                  className="form-control"
                />
              </div>
              <div className="text-center">
                <button
                  onClick={handleUpload}
                  disabled={!file || loading}
                  className="btn btn-primary btn-lg"
                >
                  {loading ? 'Uploading...' : 'Upload and Parse'}
                </button>
                <button
                  onClick={checkBalance}
                  className="btn btn-info btn-lg ms-2"
                >
                  Check Balance
                </button>
              </div>
              {balance !== null && (
                <div className="alert alert-info mt-3">
                  Current Balance: {balance} SMS
                </div>
              )}
              {message && (
                <div className="alert alert-danger mt-3" role="alert">
                  {message}
                </div>
              )}
            </div>

            {data.length > 0 && (
              <div className="card shadow p-4 mt-4">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h4 className="card-title mb-0">Extracted Data ({data.length} rows)</h4>
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="selectAll"
                      checked={selectedIndices.length === data.length && data.length > 0}
                      onChange={handleSelectAll}
                    />
                    <label className="form-check-label" htmlFor="selectAll">
                      Select All ({selectedIndices.length} selected)
                    </label>
                  </div>
                </div>
                <div className="table-responsive">
                  <table className="table table-hover align-middle">
                    <thead className="table-dark">
                      <tr>
                        <th style={{width: '50px'}}>Select</th>
                        <th>Phone Numbers</th>
                        <th>Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map((row, index) => (
                        <tr key={index} className={selectedIndices.includes(index) ? 'table-active' : ''}>
                          <td>
                            <input
                              type="checkbox"
                              className="form-check-input"
                              checked={selectedIndices.includes(index)}
                              onChange={() => handleRowSelect(index)}
                            />
                          </td>
                          <td>
                            <div>
                              <small className="text-muted">Student: {row['Student Phone No'] || 'N/A'}</small><br/>
                              <small className="text-muted">Guardian: {row['Guardian Phone No'] || 'N/A'}</small>
                            </div>
                          </td>
                          <td style={{maxWidth: '400px'}}>
                            <small>{row['Result']}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-center mt-4">
                  <button
                    onClick={handleSendSMS}
                    disabled={loading || selectedIndices.length === 0}
                    className="btn btn-success btn-lg"
                  >
                    {loading ? 'Sending...' : `Send SMS to ${selectedIndices.length} Selected Recipients`}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}