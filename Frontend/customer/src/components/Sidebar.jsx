import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
    Store,
    ShoppingCart,
    Clock,
    Package,
    LogOut,
    Menu,
    X
} from "lucide-react";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs) {
    return twMerge(clsx(inputs));
}

export default function Sidebar() {
    const [isOpen, setIsOpen] = useState(false);
    const location = useLocation();
    const { logout } = useAuth();

    const links = [
        { name: "Products", path: "/", icon: Store },
        { name: "Cart", path: "/cart", icon: ShoppingCart },
        { name: "Past Orders", path: "/orders", icon: Package },
    ];

    const handleSignOut = () => {
        logout();
    };

    return (
        <>
            {/* Mobile Toggle */}
            <button
                className="md:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-md shadow-md"
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>

            {/* Sidebar Container */}
            <div
                className={cn(
                    "fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-gray-100 transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:inset-auto md:w-64 md:flex md:flex-col shadow-xl",
                    isOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                {/* Logo / Header */}
                <div className="h-20 flex items-center px-8 border-b border-gray-100">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                        Store
                    </h1>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-8 space-y-2">
                    {links.map((link) => {
                        const Icon = link.icon;
                        const isActive = location.pathname === link.path;

                        return (
                            <NavLink
                                key={link.path}
                                to={link.path}
                                onClick={() => setIsOpen(false)}
                                className={({ isActive }) =>
                                    cn(
                                        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group",
                                        isActive
                                            ? "bg-blue-50 text-blue-600 shadow-sm"
                                            : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                                    )
                                }
                            >
                                <Icon
                                    size={20}
                                    className={cn(
                                        "transition-colors",
                                        isActive ? "text-blue-600" : "text-gray-400 group-hover:text-gray-600"
                                    )}
                                />
                                <span className="font-medium">{link.name}</span>
                            </NavLink>
                        );
                    })}
                </nav>

                {/* Footer / User */}
                <div className="p-4 border-t border-gray-100">
                    <button
                        onClick={handleSignOut}
                        className="flex items-center gap-3 w-full px-4 py-3 text-red-500 hover:bg-red-50 rounded-xl transition-colors"
                    >
                        <LogOut size={20} />
                        <span className="font-medium">Log Out</span>
                    </button>
                </div>
            </div>

            {/* Overlay for mobile */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/20 z-30 md:hidden backdrop-blur-sm"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </>
    );
}
