import DataTable from "../components/DataTable";

const users = [
  { name: "Priya Shah", role: "Owner", status: "Active", plan: "Yearly" },
  { name: "Anuj Kapoor", role: "Trader", status: "Invite Sent", plan: "Trial" }
];

const columns = [
  { key: "name", label: "User" },
  { key: "role", label: "Role" },
  { key: "status", label: "Status" },
  { key: "plan", label: "Plan" }
];

function AdminPanel() {
  return (
    <section className="page">
      <h1>Admin Panel</h1>
      <p>Operational center for user management, payments, and compliance.</p>
      <DataTable columns={columns} data={users} emptyMessage="No users onboarded yet." />
    </section>
  );
}

export default AdminPanel;
