import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './SearchEngine.css';

interface SearchResult {
  title: string;
  snippet: string;
  link: string;
}

interface Language {
  name: string;
  description: string;
}

const ListItem: React.FC<Language> = (props: Language) => {
  return (
    <li title={props.description}>
      {props.name}
    </li>
  )
}

const SupportedLanguages: React.FC = () => {
  const [langs, setLangs] = useState<Language[]>([]);

  useEffect(() => {
    fetch('http://localhost:5000/langs')
    .then(resp => resp.json())
    .then(data => {console.log(data); setLangs(data)})
    .catch(console.error);
  }, []);

  return (
    <>
    <h3>Supported Languages</h3>
    <ul className="row-list">
      {langs.map(e => <ListItem {...e}/>)}
    </ul>
  </>);
}

const SearchEngine: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [langs, setLangs] = useState<string[]>([
    'Python',
    'JavaScript',
    'Markdown',
    'HTML',
    'CSS',
  ]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setHasSearched(true);
      const response = await axios.post('http://localhost:5000/search', { query });
      setResults(response.data);
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  return (
    <div className="search-engine">
      <header className="header">
        <h1>Code Search Engine</h1>
      </header>
      <div className="content">
        <aside className="sidebar">
          <SupportedLanguages />
        </aside>
        <main className="main-content">
          <form onSubmit={handleSearch} className={`search-form ${hasSearched ? 'searched' : ''}`}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your search query"
              className="search-input"
            />
            <button type="submit" className="search-button">Search</button>
          </form>
          {hasSearched && (
            <div className="search-results">
              {results.map((result, index) => (
                <div key={index} className="result-item">
                  <h2><a href={result.link}>{result.title}</a></h2>
                  <p>{result.snippet}</p>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default SearchEngine;
