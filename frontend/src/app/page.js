'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [file, setFile] = useState(null);
  const [data, setData] = useState([]);
  const [selectedIndices, setSelectedIndices] = useState([]);
  const [smsMessage, setSmsMessage] = useState(''); // Separate state for SMS results
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [smsResult, setSmsResult] = useState(null);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      // Don't redirect immediately, show login options instead
      setCurrentUser(null);
      return;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCurrentUser(response.data);
    } catch (err) {
      localStorage.removeItem('token');
      setCurrentUser(null);
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    // Reset selections when new file is uploaded
    setSelectedIndices([]);
    // Clear previous SMS results when new file is selected
    setSmsResult(null);
    setSmsMessage('');
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
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
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_BASE_URL}/send-sms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          data: data,
          selectedIndices: selectedIndices
        }),
      });
      const result = await response.json();
      setSmsMessage(result.message); // Set SMS result message
      setSmsResult(result); // Store the full result including failed_recipients
      setMessage(''); // Clear any previous error messages
    } catch (error) {
      setMessage('Error sending SMS');
      setSmsResult(null);
      setSmsMessage(''); // Clear SMS message on error
    }
    setLoading(false);
  };

  const handleExportExcel = async () => {
    if (data.length === 0) {
      setMessage('No data to export');
      return;
    }

    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_BASE_URL}/export-excel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          data: data
        }),
      });

      if (response.ok) {
        // Create blob from response
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'SMS_Export.xlsx';
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename=(.+)/);
          if (filenameMatch) {
            filename = filenameMatch[1].replace(/"/g, '');
          }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setMessage('Excel file downloaded successfully!');
      } else {
        const result = await response.json();
        setMessage(result.detail || 'Error exporting Excel file');
      }
    } catch (error) {
      setMessage('Error exporting Excel file');
    }
    setLoading(false);
  };

  const handleDownloadSuccess = async () => {
    if (!smsResult || !smsResult.successful_recipients || smsResult.successful_recipients.length === 0) {
      setMessage('No successful recipients to download');
      return;
    }

    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_BASE_URL}/download-success`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          successful_recipients: smsResult.successful_recipients
        }),
      });

      if (response.ok) {
        // Create blob from response
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'Successful_Recipients.xlsx';
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename=(.+)/);
          if (filenameMatch) {
            filename = filenameMatch[1].replace(/"/g, '');
          }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setMessage('Successful recipients Excel downloaded successfully!');
      } else {
        const result = await response.json();
        setMessage(result.detail || 'Error downloading successful recipients Excel');
      }
    } catch (error) {
      setMessage('Error downloading successful recipients Excel');
    }
    setLoading(false);
  };

  const handleDownloadFailed = async () => {
    if (!smsResult || !smsResult.failed_recipients || smsResult.failed_recipients.length === 0) {
      setMessage('No failed recipients to download');
      return;
    }

    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const response = await fetch(`${API_BASE_URL}/download-failed`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          failed_recipients: smsResult.failed_recipients
        }),
      });

      if (response.ok) {
        // Create blob from response
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = 'Failed_Recipients.xlsx';
        if (contentDisposition) {
          const filenameMatch = contentDisposition.match(/filename=(.+)/);
          if (filenameMatch) {
            filename = filenameMatch[1].replace(/"/g, '');
          }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setMessage('Failed recipients Excel downloaded successfully!');
      } else {
        const result = await response.json();
        setMessage(result.detail || 'Error downloading failed recipients Excel');
      }
    } catch (error) {
      setMessage('Error downloading failed recipients Excel');
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
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div></div>
            <div className="d-flex align-items-center">
              {currentUser ? (
                <>
                  <span className="me-3">Welcome, {currentUser?.full_name}</span>
                  {currentUser?.role === 'admin' && (
                    <a href="/admin" className="btn btn-outline-primary btn-sm me-2">
                      Admin Panel
                    </a>
                  )}
                  <button className="btn btn-outline-secondary btn-sm" onClick={logout}>
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <a href="/login" className="btn btn-primary btn-sm me-2">
                    Login
                  </a>
                  <a href="/register" className="btn btn-outline-primary btn-sm">
                    Register
                  </a>
                </>
              )}
            </div>
          </div>
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

        {!currentUser ? (
          <div className="row justify-content-center">
            <div className="col-md-8">
              <div className="card shadow p-4 text-center">
                <h4 className="card-title mb-3">Welcome to SMS Sender</h4>
                <p className="text-muted mb-4">
                  Please login or register to access the SMS sending functionality.
                  Upload Excel files with student and guardian phone numbers to send SMS messages.
                </p>
                <div className="d-flex justify-content-center gap-3">
                  <a href="/login" className="btn btn-primary btn-lg">
                    Login
                  </a>
                  <a href="/register" className="btn btn-outline-primary btn-lg">
                    Register
                  </a>
                </div>
              </div>
            </div>
          </div>
        ) : (
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
                </div>
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
                    <div className="d-flex justify-content-center gap-3">
                      <button
                        onClick={handleSendSMS}
                        disabled={loading || selectedIndices.length === 0}
                        className="btn btn-success btn-lg"
                      >
                        {loading ? 'Sending...' : `Send SMS to ${selectedIndices.length} Selected Recipients`}
                      </button>
                    </div>
                    <div className="mt-2">
                      <small className="text-muted">
                        Export will create a ZIP file with two separate Excel files: Success.xlsx and Failed.xlsx
                      </small>
                    </div>

                    {smsMessage && (
                      <div className="alert alert-success mt-3" role="alert">
                        <strong>SMS Sent Successfully!</strong> {smsMessage}
                      </div>
                    )}

                    {smsResult && (smsResult.sent_count > 0 || smsResult.failed_count > 0) && (
                      <div className="mt-3">
                        <div className="alert alert-info">
                          <h6>SMS Sending Results:</h6>
                          <p className="mb-2">
                            <strong>Sent:</strong> {smsResult.sent_count || 0} | 
                            <strong> Failed:</strong> {smsResult.failed_count || 0}
                          </p>
                          <div className="d-flex gap-2 flex-wrap">
                            {smsResult.successful_recipients && smsResult.successful_recipients.length > 0 && (
                              <button
                                onClick={handleDownloadSuccess}
                                disabled={loading}
                                className="btn btn-success btn-sm"
                              >
                                {loading ? 'Downloading...' : 'Download Successful Recipients Excel'}
                              </button>
                            )}
                            {smsResult.failed_recipients && smsResult.failed_recipients.length > 0 && (
                              <button
                                onClick={handleDownloadFailed}
                                disabled={loading}
                                className="btn btn-warning btn-sm"
                              >
                                {loading ? 'Downloading...' : 'Download Failed Recipients Excel'}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}