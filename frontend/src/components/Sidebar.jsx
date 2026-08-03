import React from 'react';
import { NavLink } from 'react-router-dom';
import { Home, History, PieChart, User, Settings as SettingsIcon, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = () => {
  const { logout } = useAuth();
  
  const navItems = [
    { name: 'Dashboard', path: '/', icon: <Home size={20} /> },
    { name: 'History', path: '/history', icon: <History size={20} /> },
    { name: 'Analytics', path: '/analytics', icon: <PieChart size={20} /> },
    { name: 'Profile', path: '/profile', icon: <User size={20} /> },
    { name: 'Settings', path: '/settings', icon: <SettingsIcon size={20} /> },
  ];

  return (
    <div className="sidebar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
        <span style={{ fontSize: '32px' }}>🧠</span>
        <h2 style={{ fontSize: '1.2rem', margin: 0, fontWeight: 700 }} className="gradient-text">Mental Health AI</h2>
      </div>
      
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
          >
            {item.icon}
            {item.name}
          </NavLink>
        ))}
      </nav>
      
      <button 
        onClick={logout}
        className="sidebar-logout"
      >
        <LogOut size={20} />
        Log Out
      </button>
    </div>
  );
};

export default Sidebar;
