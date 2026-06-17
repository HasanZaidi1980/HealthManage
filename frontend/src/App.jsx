import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute";
import Login from "./pages/Login";

import PatientLayout from "./pages/patient/PatientLayout";
import PDashboard from "./pages/patient/Dashboard";
import PMeds from "./pages/patient/Medications";
import PSummary from "./pages/patient/HealthSummary";
import PConditions from "./pages/patient/Conditions";
import PAppointments from "./pages/patient/Appointments";
import PConsents from "./pages/patient/Consents";

import DoctorLayout from "./pages/doctor/DoctorLayout";
import DDashboard from "./pages/doctor/Dashboard";
import DPatients from "./pages/doctor/Patients";
import DSchedule from "./pages/doctor/Schedule";
import DPatientDetail from "./pages/doctor/PatientDetail";

import AdminLayout from "./pages/admin/AdminLayout";
import ADashboard from "./pages/admin/Dashboard";
import ADoctors from "./pages/admin/Doctors";
import APatients from "./pages/admin/Patients";
import ABilling from "./pages/admin/Billing";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      {/* Patient Portal */}
      <Route path="/patient" element={<ProtectedRoute role="patient"><PatientLayout /></ProtectedRoute>}>
        <Route index element={<PDashboard />} />
        <Route path="medications" element={<PMeds />} />
        <Route path="summary" element={<PSummary />} />
        <Route path="conditions" element={<PConditions />} />
        <Route path="appointments" element={<PAppointments />} />
        <Route path="consents" element={<PConsents />} />
      </Route>

      {/* Doctor Portal */}
      <Route path="/doctor" element={<ProtectedRoute role="doctor"><DoctorLayout /></ProtectedRoute>}>
        <Route index element={<DDashboard />} />
        <Route path="patients" element={<DPatients />} />
        <Route path="schedule" element={<DSchedule />} />
        <Route path="patients/:id" element={<DPatientDetail />} />
      </Route>

      {/* Practice Admin Portal */}
      <Route path="/admin" element={<ProtectedRoute role="admin"><AdminLayout /></ProtectedRoute>}>
        <Route index element={<ADashboard />} />
        <Route path="doctors" element={<ADoctors />} />
        <Route path="patients" element={<APatients />} />
        <Route path="billing" element={<ABilling />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
