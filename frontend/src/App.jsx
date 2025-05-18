import React from 'react';
import {Routes, Route} from 'react-router-dom';
import './App.css';

import Header from './components/Header';

import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import BooksListPage from './pages/BooksListPage';
import NotFoundPage from './pages/NotFoundPage';


function App() {

    return (
        <>
            <Header/>
            <main className="container">
                <Routes>
                    <Route path="/" element={<HomePage/>}/>
                    <Route path="/login" element={<LoginPage/>}/>
                    <Route path="/register" element={<RegisterPage/>}/>
                    <Route path="/books" element={<BooksListPage/>}/>
                    <Route path="*" element={<NotFoundPage/>}/>
                </Routes>
            </main>
        </>
    );
}

export default App;