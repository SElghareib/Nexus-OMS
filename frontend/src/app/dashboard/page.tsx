'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ordersApi, agentApi } from '@/lib/api';
import { formatCurrency, getStatusColor } from '@/lib/utils';
import { Order, AgentTaskResponse } from '@/types';

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const selectedOrderId = searchParams.get('order');
  
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningTask, setRunningTask] = useState(false);
  const [taskResult, setTaskResult] = useState<AgentTaskResponse | null>(null);
  const [taskInput, setTaskInput] = useState('');

  useEffect(() => {
    async function loadOrders() {
      try {
        const data = await ordersApi.list(undefined, 0, 100);
        setOrders(data);
        
        // Pre-fill task input if order is selected
        if (selectedOrderId) {
          const order = data.find((o: Order) => o.id === parseInt(selectedOrderId));
          if (order && order.is_stuck) {
            setTaskInput(`Fix stuck order #${order.id}. It's stuck because: ${order.stuck_reason}. Check the order details and determine the best action to resolve this.`);
          }
        }
      } catch (error) {
        console.error('Failed to load orders:', error);
      } finally {
        setLoading(false);
      }
    }
    loadOrders();
  }, [selectedOrderId]);

  const handleRunAgent = async () => {
    if (!taskInput.trim()) return;
    
    setRunningTask(true);
    try {
      const result = await agentApi.runTask(taskInput, selectedOrderId ? parseInt(selectedOrderId) : undefined);
      setTaskResult(result);
      
      // Redirect to flow visualization
      if (result.task_id) {
        window.location.href = `/agent-flow?task=${result.task_id}`;
      }
    } catch (error) {
      console.error('Failed to run agent task:', error);
      alert('Failed to run agent task. Make sure Agent Core (Project 1) is running.');
    } finally {
      setRunningTask(false);
    }
  };

  const stuckOrders = orders.filter(o => o.is_stuck);
  const normalOrders = orders.filter(o => !o.is_stuck);

  if (loading) {
    return <div className="text-center py-12">Loading orders...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Order Management</h1>
        <p className="text-gray-600 mt-2">View and manage all orders. Use AI Agent to fix stuck orders.</p>
      </div>

      {/* Agent Task Input */}
      {selectedOrderId && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Ask Agent to Fix Order #{selectedOrderId}
          </h2>
          <textarea
            value={taskInput}
            onChange={(e) => setTaskInput(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
            placeholder="Describe what you want the agent to do..."
          />
          <button
            onClick={handleRunAgent}
            disabled={runningTask || !taskInput.trim()}
            className="mt-4 px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {runningTask ? 'Running Agent...' : 'Run Agent Task'}
          </button>
        </div>
      )}

      {/* Stuck Orders */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 bg-orange-50">
          <h2 className="text-lg font-semibold text-orange-800">
            🚨 Stuck Orders ({stuckOrders.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stuck Reason</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stuckOrders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{order.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Customer #{order.customer_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatCurrency(order.total_amount)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{order.stuck_reason}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <a 
                      href={`/dashboard?order=${order.id}`}
                      className="text-blue-600 hover:text-blue-900 text-sm font-medium"
                    >
                      Fix with Agent →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* All Orders */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">All Orders ({normalOrders.length})</h2>
        </div>
        <div className="overflow-x-auto max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {normalOrders.slice(0, 20).map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{order.id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Customer #{order.customer_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatCurrency(order.total_amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
