import React, { useEffect, useState, useCallback } from 'react';
import { AlertCircle, Search, Filter, MoreVertical, CheckCircle, Clock, ArrowUpRight, RefreshCw } from 'lucide-react';
import { fetchComplaints, updateComplaint, deleteComplaint } from '../api/complaints';
import ComplaintModal from '../components/ComplaintModal';

const PendingComplaints = () => {
    const [complaints, setComplaints] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedComplaint, setSelectedComplaint] = useState(null);
    const [filterPriority, setFilterPriority] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [isRefreshing, setIsRefreshing] = useState(false);

    const loadComplaints = useCallback(async (showLoading = true) => {
        try {
            if (showLoading) setLoading(true);
            // Fetch all complaints to support pending AND escalated
            // Filtering strictly by 'pending' would hide escalated items
            const data = await fetchComplaints({});
            console.log("Fetched all complaints:", data);

            // Filter client-side to exclude resolved
            const activeComplaints = (data || []).filter(c => c.status !== 'resolved');

            setComplaints(activeComplaints);
            setError(null);
        } catch (err) {
            console.error("Failed to fetch complaints:", err);
            setError("Failed to load complaints. Check console for details.");
        } finally {
            if (showLoading) setLoading(false);
            setIsRefreshing(false);
        }
    }, []);

    useEffect(() => {
        loadComplaints();
    }, [loadComplaints]);

    const handleManualRefresh = () => {
        setIsRefreshing(true);
        loadComplaints(false);
    };

    const handleUpdate = async (id, updates) => {
        // Optimistic update
        if (updates.status === 'resolved') {
            setComplaints(prev => prev.filter(c => c.id !== id));
        } else {
            // Update local state
            setComplaints(prev => prev.map(c => c.id === id ? { ...c, ...updates } : c));
        }
        await updateComplaint(id, updates);
        // Reload to ensure sync
        loadComplaints(false);
    };

    const handleDelete = async (id) => {
        await deleteComplaint(id);
        setComplaints(prev => prev.filter(c => c.id !== id));
    };

    const filteredComplaints = complaints.filter(c => {
        const mail = c.email || '';
        const text = c.complaint_text || '';
        const oid = c.order_id || '';

        const matchesSearch =
            mail.toLowerCase().includes(searchQuery.toLowerCase()) ||
            text.toLowerCase().includes(searchQuery.toLowerCase()) ||
            oid.toLowerCase().includes(searchQuery.toLowerCase());

        const matchesPriority = filterPriority === 'all' || c.priority === filterPriority;

        return matchesSearch && matchesPriority;
    });

    const getPriorityColor = (priority) => {
        const p = priority?.toLowerCase() || 'low';
        if (p === 'high') return 'text-red-700 bg-red-50 border-red-200 ring-red-100';
        if (p === 'medium') return 'text-amber-700 bg-amber-50 border-amber-200 ring-amber-100';
        return 'text-blue-700 bg-blue-50 border-blue-200 ring-blue-100';
    };

    if (loading && !complaints.length) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
    );

    if (error) return (
        <div className="p-8 text-center text-red-500 bg-red-50 rounded-2xl border border-red-100">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            {error}
            <button
                onClick={() => loadComplaints(true)}
                className="block mx-auto mt-4 px-4 py-2 bg-white border border-red-200 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50"
            >
                Try Again
            </button>
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Pending Complaints</h1>
                    <p className="text-gray-500 mt-2 text-lg">Manage and track ongoing customer issues.</p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={handleManualRefresh}
                        className={`p-2.5 bg-white border border-gray-200 rounded-xl text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors ${isRefreshing ? 'animate-spin text-blue-600' : ''}`}
                        title="Refresh Data"
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>
                    <div className="relative group">
                        <select
                            value={filterPriority}
                            onChange={(e) => setFilterPriority(e.target.value)}
                            className="appearance-none pl-10 pr-8 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 shadow-sm transition-all outline-none focus:ring-2 focus:ring-blue-500/20"
                        >
                            <option value="all">All Priorities</option>
                            <option value="high">High Priority</option>
                            <option value="medium">Medium Priority</option>
                            <option value="low">Low Priority</option>
                        </select>
                        <Filter className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2 group-hover:text-gray-600 transition-colors" />
                    </div>
                </div>
            </header>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 bg-blue-50 rounded-xl">
                            <AlertCircle className="w-6 h-6 text-blue-600" />
                        </div>
                        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-100">Active</span>
                    </div>
                    <div className="text-3xl font-bold text-gray-900">{complaints.length}</div>
                    <div className="text-sm text-gray-500 mt-1 font-medium">Pending Tickets</div>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-3 bg-red-50 rounded-xl">
                            <Clock className="w-6 h-6 text-red-600" />
                        </div>
                        <span className="text-xs font-semibold text-red-600 bg-red-50 px-2.5 py-1 rounded-full border border-red-100">High Priority</span>
                    </div>
                    <div className="text-3xl font-bold text-gray-900">
                        {complaints.filter(c => c.priority === 'high').length}
                    </div>
                    <div className="text-sm text-gray-500 mt-1 font-medium">Urgent Issues</div>
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
                    placeholder="Search by email, order ID, or content..."
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
                                <th className="px-6 py-4 font-semibold text-gray-900 w-32">Status</th>
                                <th className="px-6 py-4 font-semibold text-gray-900">Complaint</th>
                                <th className="px-6 py-4 font-semibold text-gray-900 w-32">Priority</th>
                                <th className="px-6 py-4 font-semibold text-gray-900 text-right w-24">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {filteredComplaints.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center">
                                        <div className="flex flex-col items-center justify-center text-gray-400">
                                            <div className="p-4 bg-gray-50 rounded-full mb-3">
                                                <Search className="w-8 h-8 opacity-50" />
                                            </div>
                                            <p className="font-medium">No complaints found</p>
                                            <p className="text-sm mt-1">Try adjusting your filters or search query</p>
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
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-gray-900">{item.email}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            {item.status === 'escalated' ? (
                                                <span className="px-2.5 py-1 rounded-full text-xs font-semibold text-purple-700 bg-purple-50 border border-purple-200">
                                                    Escalated
                                                </span>
                                            ) : (
                                                <span className="px-2.5 py-1 rounded-full text-xs font-semibold text-yellow-700 bg-yellow-50 border border-yellow-200">
                                                    Pending
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="line-clamp-2 text-gray-600 leading-relaxed">
                                                {item.complaint_text}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getPriorityColor(item.priority)} ring-1`}>
                                                {item.priority?.toUpperCase() || 'LOW'}
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
                        <span>Showing {filteredComplaints.length} complaints</span>
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

export default PendingComplaints;

