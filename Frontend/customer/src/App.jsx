import { AuthProvider, useAuth } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { OrderProvider } from "./context/OrderContext";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Layout from "./components/Layout";
import Login from "./pages/Login";
import Products from "./pages/Products";
import Cart from "./pages/Cart";
import Orders from "./pages/Orders";
import Processing from "./pages/Processing";

function AppRoutes() {
  const { user } = useAuth();

  if (!user) {
    return <Login />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Products />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/orders" element={<Orders />} />
          <Route path="/processing" element={<Processing />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <OrderProvider>
          <AppRoutes />
        </OrderProvider>
      </CartProvider>
    </AuthProvider>
  );
}
