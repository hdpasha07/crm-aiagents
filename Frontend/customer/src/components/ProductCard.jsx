import { useCart } from "../context/CartContext";
import { Plus, ShoppingBag } from "lucide-react";

export default function ProductCard({ product }) {
  const { addToCart } = useCart();

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm hover:shadow-xl hover:shadow-blue-500/5 transition-all duration-300 border border-gray-100 flex flex-col h-full group">
      <div className="relative h-48 bg-gradient-to-br from-indigo-50 to-blue-50 rounded-xl mb-4 flex items-center justify-center overflow-hidden group-hover:bg-blue-50 transition-colors">
        <div className="transform group-hover:scale-110 transition-transform duration-300 drop-shadow-lg text-blue-200 group-hover:text-blue-300">
          <ShoppingBag size={64} />
        </div>
        <div className="absolute top-3 right-3 bg-white/80 backdrop-blur-sm px-2 py-1 rounded-full text-xs font-semibold text-gray-600">
          In Stock
        </div>
      </div>
      <div>
        <h2 className="font-bold text-lg text-gray-900 mb-1 leading-tight">{product.name}</h2>
        <p className="text-gray-500 text-sm line-clamp-2 mb-4 h-10 leading-relaxed">
          {product.description}
        </p>
      </div>

      <div className="mt-auto flex items-center justify-between pt-4 border-t border-gray-50">
        <div className="flex flex-col">
          <span className="text-xs text-gray-400 font-medium">Price</span>
          <span className="text-xl font-bold text-gray-900">₹{product.price.toLocaleString()}</span>
        </div>
        <button
          onClick={() => addToCart(product)}
          className="bg-black hover:bg-gray-800 text-white px-4 py-2.5 rounded-xl transition-all duration-200 flex items-center gap-2 active:scale-95 shadow-lg shadow-gray-200 group/btn"
        >
          <Plus size={18} className="group-hover/btn:rotate-90 transition-transform duration-200" />
          <span className="text-sm font-medium">Add</span>
        </button>
      </div>
    </div>
  );
}
