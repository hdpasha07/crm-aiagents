import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import PendingComplaints from './pages/PendingComplaints';
import ResolvedComplaints from './pages/ResolvedComplaints';
import Analytics from './pages/Analytics';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/pending" replace />} />
          <Route path="pending" element={<PendingComplaints />} />
          <Route path="resolved" element={<ResolvedComplaints />} />
          <Route path="analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

