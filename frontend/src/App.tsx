import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import SearchEngine from './SearchEngine';

interface Response {
  from: string;
  text: string;
}

function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  return (
    <div className="App">
      <button className="theme-toggle" onClick={toggleTheme}>
        Switch to {theme === 'light' ? 'Dark' : 'Light'} Theme
      </button>
      <div className="chat-container">
        <SearchEngine />
      </div>
    </div>
  );
}

export default App;
