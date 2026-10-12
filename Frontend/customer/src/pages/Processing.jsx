import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle2, Loader2 } from "lucide-react";
import { useCart } from "../context/CartContext";

export default function Processing() {
    const [step, setStep] = useState("processing"); // processing, success
    const navigate = useNavigate();
    const { clearCart } = useCart();

    useEffect(() => {
        // Simulate processing time
        const timer1 = setTimeout(() => {
            setStep("success");
            clearCart();
        }, 2000);

        const timer2 = setTimeout(() => {
            // Automatically redirect to orders after success
            // or just let them stay. Let's let them stay or click.
            // Actually, user might want to see it.
        }, 4000);

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
        };
    }, [clearCart]);

    return (
        <div className="flex flex-col items-center justify-center h-[80vh] text-center">
            {step === "processing" && (
                <div className="animate-in fade-in zoom-in duration-500">
                    <Loader2 className="w-16 h-16 text-blue-600 animate-spin mb-4 mx-auto" />
                    <h2 className="text-2xl font-bold text-gray-800">Processing Order</h2>
                    <p className="text-gray-500 mt-2">Please wait while we confirm your details...</p>
                </div>
            )}

            {step === "success" && (
                <div className="animate-in fade-in zoom-in duration-500">
                    <CheckCircle2 className="w-20 h-20 text-green-500 mb-4 mx-auto" />
                    <h2 className="text-3xl font-bold text-gray-800">Order Confirmed!</h2>
                    <p className="text-gray-500 mt-2 max-w-md mx-auto">
                        Thank you for your purchase. Your order has been successfully placed and is being prepared.
                    </p>
                    <button
                        onClick={() => navigate("/orders")}
                        className="mt-8 px-6 py-3 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200"
                    >
                        View My Orders
                    </button>
                </div>
            )}
        </div>
    );
}
