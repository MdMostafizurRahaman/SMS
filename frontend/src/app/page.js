'use client';

import { useState } from 'react';

export default function Home() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState([]);
  const [message, setMessage] = useState([]);
  const [loading, setLoading] = useState(false);
  const [balance, setBalance] = useState(null);

  const checkBalance = async () => {
    try {
      const response = await fetch('http://localhost:8000/balance');
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
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (response.ok) {
        setData(result.data);
        setMessage('');
      } else {
        setMessage(result.detail);
      }
    } catch (error) {
      setMessage('Error uploading file');
    }
    setLoading(false);
  };

  const handleSendSMS = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/send-sms', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      setMessage(result.message);
    } catch (error) {
      setMessage('Error sending SMS');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-light">
      <div className="container-lg py-4">
        <header className="text-center mb-4">
          <div className="d-flex flex-column align-items-center">
            <img
              src="/Big Bang logo-icn.png"
              alt="SMS Sender logo"
              className="img-fluid mb-3"
              style={{ maxHeight: '120px' }}
              onError={(e) => { e.target.src = 'https://dummyimage.com/320x200/2c3e50/ffffff&text=SMS+Sender+Logo'; }}
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
          <div className="col-md-8">
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
                <h4 className="card-title mb-3">Extracted Data</h4>
                <div className="table-responsive">
                  <table className="table table-hover align-middle">
                    <thead className="table-dark">
                      <tr>
                        <th>Student Phone No</th>
                        <th>Guardian Phone No</th>
                        <th>Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map((row, index) => (
                        <tr key={index}>
                          <td>{row['Student Phone No'] || ''}</td>
                          <td>{row['Guardian Phone No'] || ''}</td>
                          <td>{row['Result']}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-center mt-4">
                  <button
                    onClick={handleSendSMS}
                    disabled={loading}
                    className="btn btn-success btn-lg"
                  >
                    {loading ? 'Sending...' : 'Confirm & Send SMS'}
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