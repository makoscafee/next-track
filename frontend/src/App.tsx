import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Recommendations from './pages/Recommendations';
import AdminLogin from './pages/admin/Login';
import AdminDashboard from './pages/admin/Dashboard';
import AdminExperiments from './pages/admin/Experiments';
import AdminMetrics from './pages/admin/Metrics';
import ProtectedRoute from './components/common/ProtectedRoute';

function App() {
  return (
    <Router>
      <Routes>
        {/* User Routes */}
        <Route path="/" element={<Home />} />
        <Route path="/recommendations" element={<Recommendations />} />

        {/* Admin Routes */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/experiments"
          element={
            <ProtectedRoute>
              <AdminExperiments />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/metrics"
          element={
            <ProtectedRoute>
              <AdminMetrics />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
