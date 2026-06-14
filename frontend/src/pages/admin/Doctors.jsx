import ManageUsers from "../../components/ManageUsers";
export default function Doctors() {
  return <ManageUsers role="doctor" createPath="/admin/doctors" title="Manage Doctors" />;
}
