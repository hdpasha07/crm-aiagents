import React, { useState, useEffect } from 'react';
import { X, Save, Trash2, Mail, FileText, Calendar, Hash, AlertTriangle } from 'lucide-react';

const ComplaintModal = ({ complaint, onClose, onUpdate, onDelete }) => {
    const [status, setStatus] = useState(complaint?.status || 'pending');
    const [priority, setPriority] = useState(complaint?.priority || 'low');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (complaint) {
            setStatus(complaint.status);
            setPriority(complaint.priority);
        }
    }, [complaint]);

    if (!complaint) return null;

    const handleSave = async () => {
        setLoading(true);
        try {
            await onUpdate(complaint.id, { status, priority });
            onClose();
        } catch (error) {
            console.error("Failed to update complaint", error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        if (window.confirm("Are you sure you want to delete this complaint?")) {
            setLoading(true);
            try {
                await onDelete(complaint.id);
                onClose();
            } catch (error) {
                console.error("Failed to delete complaint", error);
            } finally {
                setLoading(false);
            }
        }
    };

    const getPriorityColor = (p) => {
        const priorityColors = {
            high: 'bg-red-50 text-red-700 border-red-200',
            medium: 'bg-amber-50 text-amber-700 border-amber-200',
            low: 'bg-blue-50 text-blue-700 border-blue-200'
        };
        return priorityColors[p?.toLowerCase()] || priorityColors.low;
    };

    const getStatusColor = (s) => {
        const statusColors = {
            pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
            resolved: 'bg-green-50 text-green-700 border-green-200',
            escalated: 'bg-purple-50 text-purple-700 border-purple-200'
        };
        return statusColors[s?.toLowerCase()] || 'bg-gray-50 text-gray-700 border-gray-200';
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">

                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                            Complaint Details
                            <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(complaint.status)}`}>
                                {complaint.status}
                            </span>
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">ID: {complaint.id}</p>
                    </div>
                    <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-6 overflow-y-auto flex-1">

                    {/* Customer Info */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                            <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-1">
                                <Mail className="w-4 h-4" /> Email Address
                            </div>
                            <div className="text-gray-900 font-medium truncate" title={complaint.email}>{complaint.email}</div>
                        </div>
                        <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                            <div className="flex items-center gap-2 text-sm font-medium text-gray-500 mb-1">
                                <Hash className="w-4 h-4" /> Order ID
                            </div>
                            <div className="text-gray-900 font-medium">{complaint.order_id}</div>
                        </div>
                    </div>

                    {/* Complaint Text */}
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
                            <FileText className="w-4 h-4" /> Complaint Description
                        </div>
                        <div className="p-4 bg-white border border-gray-200 rounded-xl text-gray-700 leading-relaxed min-h-[100px]">
                            {complaint.complaint_text}
                        </div>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Calendar className="w-4 h-4" />
                        Created: {new Date(complaint.created_at || Date.now()).toLocaleString()}
                    </div>

                    {/* Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-100">
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700">Status</label>
                            <select
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                                className="w-full p-2.5 bg-white border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                            >
                                <option value="pending">Pending</option>
                                <option value="escalated">Escalated</option>
                                <option value="resolved">Resolved</option>
                            </select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700">Priority</label>
                            <select
                                value={priority}
                                onChange={(e) => setPriority(e.target.value)}
                                className="w-full p-2.5 bg-white border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                            >
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
                    <button
                        onClick={handleDelete}
                        className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-xl transition-colors font-medium text-sm"
                    >
                        <Trash2 className="w-4 h-4" /> Delete
                    </button>
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-xl transition-colors font-medium text-sm"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleSave}
                            disabled={loading}
                            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg shadow-blue-200 transition-all font-medium text-sm disabled:opacity-70"
                        >
                            <Save className="w-4 h-4" />
                            {loading ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ComplaintModal;
