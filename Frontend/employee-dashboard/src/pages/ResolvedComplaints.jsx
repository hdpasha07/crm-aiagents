import React, { useEffect, useState } from 'react';
import { CheckCircle, Search, Filter, Calendar, Clock, ArrowUpRight } from 'lucide-react';
import { fetchComplaints, updateComplaint, deleteComplaint } from '../api/complaints';
import ComplaintModal from '../components/ComplaintModal';

const ResolvedComplaints = () => {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedComplaint, setSelectedComplaint] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');

    const loadResolved = async () => {
        try {
            setLoading(true);
            const data = await fetchComplaints({ status: 'resolved' });
            setComplaints(data);
        } catch (err) {
            console.error("Failed to fetch resolved complaints:", err);
            setError("Failed to load history");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadResolved();
    }, []);

    const handleUpdate = async (id, updates) => {
        // If status changed to pending, remove from resolved list
        if (updates.status === 'pending') {
            setComplaints(prev => prev.filter(c => c.id !== id));
        } else {
            setComplaints(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
        }
        await updateComplaint(id, updates);
    };

    const handleDelete = async (id) => {
        await deleteComplaint(id);
        setComplaints(prev => prev.filter(c => c.id !== id));
    };

    const filteredComplaints = complaints.filter(c =>
        c.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.complaint_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.order_id.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600"></div>
        </div>
    );

    if (error) return (
        <div className="p-8 text-center text-red-500 bg-red-50 rounded-2xl border border-red-100">
            {error}
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Resolved Complaints</h1>
                    <p className="text-gray-500 mt-2 text-lg">History of successfully closed tickets.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors">
                        <Calendar className="w-4 h-4" />
                        Last 30 Days
                    </button>
                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-colors">
                        <Filter className="w-4 h-4" />
                        Filter
                    </button>
                </div>
            </header>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 bg-green-50 rounded-xl">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                        </div>
                        <span className="text-xs font-semibold text-green-600 bg-green-50 px-2.5 py-1 rounded-full border border-green-100">Total</span>
                    </div>
                    <div className="text-3xl font-bold text-gray-900">{complaints.length}</div>
                    <div className="text-sm text-gray-500 mt-1 font-medium">Resolved Tickets</div>
                </div>
            </div>

            {/* Search Bar */}
            <div className="bg-white p-2 rounded-2xl shadow-sm border border-gray-100 flex items-center focus-within:ring-4 ring-gray-100 transition-all">
                <div className="pl-4 pr-3 text-gray-400">
                    <Search className="w-5 h-5" />
                </div>
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search history..."
                    className="flex-1 bg-transparent border-none outline-none text-gray-900 placeholder-gray-400 text-base py-2.5"
                />
            </div>

            {/* Table */}
            <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50/50 border-b border-gray-100">
                            <tr>
                                <th className="px-6 py-4 font-semibold text-gray-900 w-32">Order ID</th>
                                <th className="px-6 py-4 font-semibold text-gray-900 w-64">Customer</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Issue</th>
                                <th className="px-6 py-4 font-semibold text-gray-900 w-32">Status</th>
                                <th className="px-6 py-4 font-semibold text-gray-900 text-right w-24">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {filteredComplaints.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-6 py-12 text-center text-gray-500">
                                        <div className="flex flex-col items-center justify-center text-gray-400">
                                            <div className="p-4 bg-gray-50 rounded-full mb-3">
                                                <Search className="w-8 h-8 opacity-50" />
                                            </div>
                                            <p className="font-medium">No resolved tickets found</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                filteredComplaints.map((item) => (
                                    <tr
                                        key={item.id}
                                        className="group hover:bg-gray-50/80 transition-colors cursor-pointer"
                                        onClick={() => setSelectedComplaint(item)}
                                    >
                                        <td className="px-6 py-4 font-medium text-gray-900 font-mono">
                                            #{item.order_id}
                                        </td>
                                        <td className="px-6 py-4 font-medium text-gray-700">{item.email}</td>
                                        <td className="px-6 py-4">
                                            <div className="line-clamp-2 text-gray-600 leading-relaxed">
                                                {item.complaint_text}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="px-2.5 py-1 rounded-full text-xs font-semibold text-green-700 bg-green-50 border border-green-200">
                                                Resolved
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setSelectedComplaint(item);
                                                }}
                                                className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors opacity-0 group-hover:opacity-100"
                                            >
                                                <ArrowUpRight className="w-5 h-5" />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
                {filteredComplaints.length > 0 && (
                    <div className="px-6 py-4 border-t border-gray-100 bg-gray-50/50 flex items-center justify-between text-sm text-gray-500">
                        <span>Showing {filteredComplaints.length} tickets</span>
                    </div>
                )}
            </div>
            <ComplaintModal
                complaint={selectedComplaint}
                onClose={() => setSelectedComplaint(null)}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
            />
        </div>
    );
};

export default ResolvedComplaints;
