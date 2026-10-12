import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <div className="bg-white shadow p-4 flex justify-between">
      <h1 className="font-bold">Dummy Shop</h1>
      {user && (
        <button onClick={logout} className="text-red-600">
          Logout
        </button>
      )}
    </div>
  );
}
