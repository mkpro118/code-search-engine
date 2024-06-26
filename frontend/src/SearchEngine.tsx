import React, { useState, useEffect } from 'react';
import type {Dispatch, SetStateAction} from 'react';
import axios from 'axios';
import './SearchEngine.css';

interface SearchResult {
  language: string;
  text: string;
  link: string;
  filename: string;
}

interface Language {
  name: string;
  description: string;
}

interface MetaDataProps {
  user: string;
  setUser: Dispatch<SetStateAction<string>>;
  repo: string;
  setRepo: Dispatch<SetStateAction<string>>;
}

const ListItem: React.FC<Language> = (props: Language) => {
  return (
    <li title={props.description}>
      {props.name}
    </li>
  )
}

const MetaData: React.FC<MetaDataProps> = (props: MetaDataProps) => {
  const user = props.user;
  const repo = props.repo;
  const userChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    props.setUser(e.target.value);
  };

  const repoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    props.setRepo(e.target.value);
  };

  return (
    <>
      <div className="user-container">
        <legend>User:</legend>
        <input className="meta" id="user" placeholder={user} onChange={userChange}/>
      </div>
      <div className="repo-container">
        <legend>Repository:</legend>
        <input className="meta" id="repo" placeholder={repo}  onChange={repoChange}/>
      </div>
    </>
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
  const [langs, setLangs] = useState<string[]>([]);
  const [user, setUser] = useState<string>('mkpro118');
  const [repo, setRepo] = useState<string>('mkpro118-repository');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setHasSearched(true);
      const response = await axios.post('http://localhost:5000/search', { query, user, repo });
      setResults(response.data);
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  const maxlen: number = 20;

  return (
    <div className="search-engine">
      <header className="header">
        <h1>Code Search Engine</h1>
      </header>
      <div className="content">
        <aside className="sidebar">
          <MetaData user={user} setUser={setUser} repo={repo} setRepo={setRepo}/>
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
                  <h2 title={result.filename} >{result.filename.length > maxlen ? `${result.filename.substring(0, maxlen)}...`: result.filename}
                    &nbsp;<small>({result.language})</small>
                    &nbsp;<small><a href={result.link} target="blank_">[see source]</a></small>
                  </h2>
                  <p>Preview</p>
                  <pre>{result.text}</pre>
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
