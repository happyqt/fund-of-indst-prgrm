import React from 'react';
import {Routes, Route} from 'react-router-dom';
import './App.css';

import Header from './components/Header';

import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import BooksListPage from './pages/BooksListPage';
import MyBooksPage from './pages/MyBooksPage';
import MyExchangesPage from './pages/MyExchangesPage';
import AddBookPage from './pages/AddBookPage';
import AdminStatsPage from './pages/AdminStatsPage';
import AdminBooksPage from './pages/AdminBooksPage';
import AdminUsersPage from './pages/AdminUsersPage';
import NotFoundPage from './pages/NotFoundPage';

import {ProtectedRoute, AdminProtectedRoute} from './components/ProtectedRoute';

function App() {

    return (
        <>
            <Header/>
            <main className="container">
                <Routes>
                    {/* Публичные маршруты */}
                    <Route path="/" element={<HomePage/>}/>
                    <Route path="/login" element={<LoginPage/>}/>
                    <Route path="/register" element={<RegisterPage/>}/>
                    <Route path="/books" element={<BooksListPage/>}/>

                    {/* Защищенные маршруты (требуют аутентификации) */}
                    <Route path="/my-books" element={
                        <ProtectedRoute>
                            <MyBooksPage/>
                        </ProtectedRoute>
                    }/>
                     <Route path="/add-book" element={
                        <ProtectedRoute>
                            <AddBookPage/>
                        </ProtectedRoute>
                    }/>
                     <Route path="/exchanges" element={
                        <ProtectedRoute>
                            <MyExchangesPage/>
                        </ProtectedRoute>
                    }/>


                    {/* Административные маршруты (требуют прав администратора) */}
                    <Route path="/admin/stats" element={
                         <AdminProtectedRoute>
                            <AdminStatsPage/>
                        </AdminProtectedRoute>
                    }/>
                    <Route path="/admin/books" element={
                         <AdminProtectedRoute>
                            <AdminBooksPage/>
                        </AdminProtectedRoute>
                    }/>
                    <Route path="/admin/users" element={
                         <AdminProtectedRoute>
                            <AdminUsersPage/>
                        </AdminProtectedRoute>
                    }/>

                    <Route path="*" element={<NotFoundPage/>}/>
                </Routes>
            </main>
        </>
    );
}

export default App;