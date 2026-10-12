import React from "react";
import Sidebar from "./Sidebar";
import { Outlet } from "react-router-dom";

export default function Layout() {
    return (
        <div className="flex h-screen w-full bg-gray-50/50">
            <Sidebar />
            <main className="flex-1 overflow-auto">
                <div className="max-w-7xl mx-auto p-4 md:p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
