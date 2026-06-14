import ManageUsers from "../../components/ManageUsers";
export default function Patients() {
  return <ManageUsers role="patient" createPath="/admin/patients" title="Manage Patients" />;
}
