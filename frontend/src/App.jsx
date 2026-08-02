import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Register from './pages/Register'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import AllNotes from './pages/AllNotes'
import SearchPage from './pages/SearchPage'
import TagsPage from './pages/TagsPage'
import CollectionsPage from './pages/CollectionsPage'
import SettingsPage from './pages/SettingsPage'
import NoteEditor from './pages/NoteEditor'
import { getToken } from './api'
import BrainDump from './pages/BrainDump'
import ModelRoutingDashboard from './pages/ModelRoutingDashboard'
import AISuggestions from './pages/AISuggestions'
import KnowledgeGraph from './pages/KnowledgeGraph'
import SplashHome from './pages/SplashHome'

function ProtectedRoute({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

function protectedPage(page) {
  return <ProtectedRoute>{page}</ProtectedRoute>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SplashHome />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={protectedPage(<Dashboard />)} />
        <Route path="/notes" element={protectedPage(<AllNotes />)} />
        <Route path="/notes/:id" element={protectedPage(<NoteEditor />)} />
        <Route path="/search" element={protectedPage(<SearchPage />)} />
        <Route path="/tags" element={protectedPage(<TagsPage />)} />
        <Route path="/collections" element={protectedPage(<CollectionsPage />)} />
        <Route path="/settings" element={protectedPage(<SettingsPage />)} />
        <Route path="/model-routing" element={protectedPage(<ModelRoutingDashboard />)} />
        <Route path="/ai-suggestions" element={protectedPage(<AISuggestions />)} />
        <Route path="/knowledge-graph" element={protectedPage(<KnowledgeGraph />)} />
        <Route path="/brain-dump" element={protectedPage(<BrainDump />)} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
