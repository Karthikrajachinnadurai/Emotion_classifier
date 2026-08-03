import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axiosClient from '../api/axiosClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  // On app load, check if token exists and fetch user profile
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const res = await axiosClient.get('/profile');
          setUser(res.data);
          setIsAuthenticated(true);
        } catch {
          // Token invalid or expired
          localStorage.removeItem('token');
          setUser(null);
          setIsAuthenticated(false);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, []);

  /**
   * Register a new user account.
   * @param {string} name
   * @param {string} email
   * @param {string} password
   */
  const register = useCallback(async (name, email, password) => {
    const res = await axiosClient.post('/register', { name, email, password });
    return res.data;
  }, []);

  /**
   * Login with email and password.
   * Stores the JWT in localStorage and fetches user profile.
   * @param {string} email
   * @param {string} password
   */
  const login = useCallback(async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const res = await axiosClient.post('/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { access_token } = res.data;
    localStorage.setItem('token', access_token);

    // Fetch full user profile
    const profileRes = await axiosClient.get('/profile');
    setUser(profileRes.data);
    setIsAuthenticated(true);

    return profileRes.data;
  }, []);

  /**
   * Logout — clears token and user state.
   */
  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    logout,
    register,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

/**
 * useAuth hook — must be used inside <AuthProvider>.
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
