import { useCart } from "../context/CartContext";
import { useOrders } from "../context/OrderContext";
import { useAuth } from "../context/AuthContext";
import { Trash2, ShoppingCart, ArrowRight } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

export default function Cart() {
  const { cart, removeFromCart } = useCart();
  const { addOrder } = useOrders();
  const { user } = useAuth();
  const navigate = useNavigate();

  // Group items by ID to show quantities
  const groupedItems = cart.reduce((acc, item) => {
    if (!acc[item.id]) {
      acc[item.id] = { ...item, quantity: 0 };
    }
    acc[item.id].quantity += 1;
    return acc;
  }, {});

  const items = Object.values(groupedItems);
  const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const tax = total * 0.18;

  const handleCheckout = () => {
    addOrder(cart, user.email);
    navigate("/processing");
  };

  if (cart.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center animate-in fade-in zoom-in duration-500">
        <div className="bg-gray-100 p-8 rounded-full mb-6">
          <ShoppingCart className="w-16 h-16 text-gray-400" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900">Your cart is empty</h2>
        <p className="text-gray-500 mt-3 mb-8 text-lg">Looks like you haven't added anything yet.</p>
        <Link to="/" className="px-8 py-4 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-colors shadow-lg shadow-gray-200">
          Start Shopping
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h1 className="text-3xl font-bold text-gray-900">Shopping Cart</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => (
            <div key={item.id} className="bg-white p-6 rounded-2xl border border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center gap-6">
                <div className="w-20 h-20 bg-gray-50 rounded-xl flex items-center justify-center text-3xl shrink-0">
                  📦
                </div>
                <div>
                  <h3 className="font-bold text-lg text-gray-900">{item.name}</h3>
                  <p className="text-sm text-gray-500 mb-2">{item.description}</p>
                  <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700">
                    Qty: {item.quantity}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto mt-4 sm:mt-0 pt-4 sm:pt-0 border-t sm:border-0 border-gray-100">
                <div className="text-right">
                  <div className="text-xs text-gray-400">Total</div>
                  <div className="font-bold text-xl text-gray-900">₹{(item.price * item.quantity).toLocaleString()}</div>
                </div>
                <button
                  onClick={() => removeFromCart(item.id)}
                  className="p-3 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
                  title="Remove from cart"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-xl shadow-gray-100/50 sticky top-8">
            <h3 className="font-bold text-xl text-gray-900 mb-6">Order Summary</h3>

            <div className="space-y-4 mb-8">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span className="font-medium">₹{total.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax (18%)</span>
                <span className="font-medium">₹{tax.toLocaleString()}</span>
              </div>
              <div className="h-px bg-gray-100 my-4" />
              <div className="flex justify-between items-end">
                <span className="font-bold text-gray-900 text-lg">Total</span>
                <span className="font-bold text-3xl text-gray-900">₹{(total + tax).toLocaleString()}</span>
              </div>
            </div>

            <button
              onClick={handleCheckout}
              className="w-full py-4 bg-black text-white rounded-xl font-bold text-lg hover:bg-gray-800 transition-all flex items-center justify-center gap-2 shadow-lg shadow-gray-300 hover:shadow-xl hover:translate-y-[-2px] active:translate-y-[0px]"
            >
              <span>Checkout</span>
              <ArrowRight size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}