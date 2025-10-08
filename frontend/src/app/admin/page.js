'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';
import Image from 'next/image';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://sms-8kiu.onrender.com';

export default function Admin() {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(true);
  const [profileData, setProfileData] = useState({
    email: '',
    full_name: '',
    password: '',
    confirmPassword: ''
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const router = useRouter();

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const response = await axios.get(`${API_BASE_URL}/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const user = response.data;
      if (user.role !== 'admin') {
        router.push('/');
        return;
      }
      setCurrentUser(user);
      setProfileData({
        email: user.email,
        full_name: user.full_name,
        password: '',
        confirmPassword: ''
      });
      fetchPendingUsers();
      fetchAllUsers();
    } catch (err) {
      localStorage.removeItem('token');
      router.push('/login');
    }
    setLoading(false);
  }, [router]);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const fetchPendingUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPendingUsers(response.data);
    } catch (err) {
      setError('Failed to fetch pending users');
    }
  };

  const fetchAllUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/admin/all-users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAllUsers(response.data);
    } catch (err) {
      setError('Failed to fetch all users');
    }
  };

  const approveUser = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE_URL}/admin/approve/${userId}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccess('User approved successfully');
      fetchPendingUsers();
      fetchAllUsers();
    } catch (err) {
      setError('Failed to approve user');
    }
  };

  const deleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_BASE_URL}/admin/user/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccess('User deleted successfully');
      fetchPendingUsers();
      fetchAllUsers();
    } catch (err) {
      setError('Failed to delete user');
    }
  };

  const updateProfile = async (e) => {
    e.preventDefault();
    
    // Clear any previous messages
    setError('');
    setSuccess('');
    
    if (profileData.password && profileData.password !== profileData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setProfileLoading(true);
    try {
      const token = localStorage.getItem('token');
      const updateData = {
        email: profileData.email,
        full_name: profileData.full_name
      };
      
      if (profileData.password) {
        updateData.password = profileData.password;
      }

      await axios.put(`${API_BASE_URL}/users/me`, updateData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      setSuccess('Profile updated successfully');
      setProfileData(prev => ({ ...prev, password: '', confirmPassword: '' }));
      
      // Refresh current user data (don't show error if this fails)
      try {
        const response = await axios.get(`${API_BASE_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setCurrentUser(response.data);
        setProfileData(prev => ({
          ...prev,
          email: response.data.email,
          full_name: response.data.full_name
        }));
      } catch (refreshErr) {
        // Refresh failed, but update was successful - just update local state
        setProfileData(prev => ({
          ...prev,
          email: profileData.email,
          full_name: profileData.full_name
        }));
      }
    } catch (err) {
      setError('Failed to update profile');
    }
    setProfileLoading(false);
  };

  const logout = () => {
    localStorage.removeItem('token');
    router.push('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen d-flex align-items-center justify-content-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-light">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container">
          <Link className="navbar-brand d-flex align-items-center" href="/">
            <Image
              src="/Big Bang logo-icn.png"
              alt="SMS Sender logo"
              width={40}
              height={25}
              className="me-2"
            />
            Admin Panel
          </Link>
          <div className="navbar-nav ms-auto">
            <span className="navbar-text me-3">
              Welcome, {currentUser?.full_name}
            </span>
            <button className="btn btn-outline-light btn-sm" onClick={logout}>
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="container mt-4">
        {error && (
          <div className="alert alert-danger alert-dismissible fade show" role="alert">
            {error}
            <button type="button" className="btn-close" onClick={() => setError('')}></button>
          </div>
        )}

        {success && (
          <div className="alert alert-success alert-dismissible fade show" role="alert">
            {success}
            <button type="button" className="btn-close" onClick={() => setSuccess('')}></button>
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <ul className="nav nav-tabs card-header-tabs">
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'pending' ? 'active' : ''}`}
                  onClick={() => setActiveTab('pending')}
                >
                  Pending Approvals ({pendingUsers.length})
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'all' ? 'active' : ''}`}
                  onClick={() => setActiveTab('all')}
                >
                  All Users ({allUsers.length})
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === 'profile' ? 'active' : ''}`}
                  onClick={() => setActiveTab('profile')}
                >
                  My Profile
                </button>
              </li>
            </ul>
          </div>
          <div className="card-body">
            {activeTab === 'pending' && (
              <div>
                <h5 className="card-title">Pending User Approvals</h5>
                {pendingUsers.length === 0 ? (
                  <p className="text-muted">No pending approvals</p>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Email</th>
                          <th>Registered</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pendingUsers.map((user) => (
                          <tr key={user.id}>
                            <td>{user.full_name}</td>
                            <td>{user.email}</td>
                            <td>{new Date(user.created_at).toLocaleDateString()}</td>
                            <td>
                              <button
                                className="btn btn-success btn-sm me-2"
                                onClick={() => approveUser(user.id)}
                              >
                                Approve
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                onClick={() => deleteUser(user.id)}
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'all' && (
              <div>
                <h5 className="card-title">All Users</h5>
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Registered</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allUsers.map((user) => (
                        <tr key={user.id}>
                          <td>{user.full_name}</td>
                          <td>{user.email}</td>
                          <td>
                            <span className={`badge ${
                              user.role === 'admin' ? 'bg-primary' :
                              user.role === 'approved' ? 'bg-success' : 'bg-warning'
                            }`}>
                              {user.role}
                            </span>
                          </td>
                          <td>{new Date(user.created_at).toLocaleDateString()}</td>
                          <td>
                            {user.role !== 'admin' && (
                              <button
                                className="btn btn-danger btn-sm"
                                onClick={() => deleteUser(user.id)}
                              >
                                Delete
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'profile' && (
              <div>
                <h5 className="card-title">Update Profile</h5>
                <div className="row justify-content-center">
                  <div className="col-md-6">
                    <form onSubmit={updateProfile}>
                      <div className="mb-3">
                        <label htmlFor="full_name" className="form-label">Full Name</label>
                        <input
                          type="text"
                          className="form-control"
                          id="full_name"
                          value={profileData.full_name}
                          onChange={(e) => setProfileData(prev => ({ ...prev, full_name: e.target.value }))}
                          required
                        />
                      </div>
                      <div className="mb-3">
                        <label htmlFor="email" className="form-label">Email</label>
                        <input
                          type="email"
                          className="form-control"
                          id="email"
                          value={profileData.email}
                          onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                          required
                        />
                      </div>
                      <div className="mb-3">
                        <label htmlFor="password" className="form-label">New Password (leave blank to keep current)</label>
                        <input
                          type="password"
                          className="form-control"
                          id="password"
                          value={profileData.password}
                          onChange={(e) => setProfileData(prev => ({ ...prev, password: e.target.value }))}
                          minLength="6"
                        />
                      </div>
                      <div className="mb-3">
                        <label htmlFor="confirmPassword" className="form-label">Confirm New Password</label>
                        <input
                          type="password"
                          className="form-control"
                          id="confirmPassword"
                          value={profileData.confirmPassword}
                          onChange={(e) => setProfileData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                          minLength="6"
                        />
                      </div>
                      <button
                        type="submit"
                        className="btn btn-primary w-100"
                        disabled={profileLoading}
                      >
                        {profileLoading ? 'Updating...' : 'Update Profile'}
                      </button>
                    </form>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}