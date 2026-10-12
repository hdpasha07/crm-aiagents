import { useOrders } from "../context/OrderContext";
import { useAuth } from "../context/AuthContext";
import ComplaintForm from "../components/ComplaintForm";
import { Package, Truck } from "lucide-react";

export default function Orders() {
  const { orders } = useOrders();
  const { user } = useAuth();

  const myOrders = orders.filter((o) => o.email === user.email);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h1 className="text-3xl font-bold text-gray-900">Order History</h1>

      {myOrders.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-3xl border border-gray-100 border-dashed">
          <Package className="w-16 h-16 text-gray-300 mb-4" />
          <h3 className="text-xl font-medium text-gray-900">No orders yet</h3>
          <p className="text-gray-500 mt-2">Your past orders will appear here.</p>
        </div>
      ) : (
        <div className="grid gap-6">
          {myOrders.map((o) => (
            <div key={o.order_id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
              <div className="bg-gray-50/50 p-6 flex flex-wrap gap-4 justify-between items-center border-b border-gray-100">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider font-bold mb-1">Order ID</p>
                  <p className="font-mono font-bold text-gray-900 text-lg">#{o.order_id}</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                  <Truck size={16} />
                  <span>Delivered</span>
                </div>
              </div>

              <div className="p-6">
                <div className="space-y-4 mb-8">
                  {o.items.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center text-xl shrink-0">
                        📦
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{item.name}</p>
                        <p className="text-sm text-gray-500">₹{item.price.toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="pt-6 border-t border-gray-100">
                  <h4 className="font-semibold text-gray-900 mb-4">Need help with this order?</h4>
                  <ComplaintForm orderId={o.order_id} email={user.email} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
