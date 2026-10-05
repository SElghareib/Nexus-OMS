'use client';

import { useEffect, useState } from 'react';
import { ordersApi, healthApi, agentApi } from '@/lib/api';
import { formatCurrency, getStatusColor } from '@/lib/utils';
import { Order } from '@/types';

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalOrders: 0,
    stuckOrders: 0,
    agentSuccessRate: 0,
  });
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [agentHealth, setAgentHealth] = useState<string>('checking...');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch orders
        const orders = await ordersApi.list(undefined, 0, 50);
        setRecentOrders(orders.slice(0, 10));
        
        // Calculate stats
        const stuckCount = orders.filter((o: Order) => o.is_stuck).length;
        setStats({
          totalOrders: orders.length,
          stuckOrders: stuckCount,
          agentSuccessRate: 92, // Would calculate from actual execution traces
        });

        // Check agent health
        try {
          const health = await agentApi.healthCheck();
          setAgentHealth(health.agent_core);
        } catch {
          setAgentHealth('disconnected');
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">AI-Powered Order Management System</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Orders</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">{stats.totalOrders}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Stuck Orders</h3>
          <p className="text-3xl font-bold text-orange-600 mt-2">{stats.stuckOrders}</p>
          <p className="text-xs text-gray-500 mt-1">Require agent intervention</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">Agent Core Status</h3>
          <p className={`text-3xl font-bold mt-2 ${agentHealth === 'connected' ? 'text-green-600' : 'text-red-600'}`}>
            {agentHealth === 'connected' ? 'Connected' : 'Disconnected'}
          </p>
          <p className="text-xs text-gray-500 mt-1">Project 1 Integration</p>
        </div>
      </div>

      {/* Recent Stuck Orders */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Stuck Orders</h2>
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
              {recentOrders.filter(o => o.is_stuck).slice(0, 5).map((order) => (
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
                      className="text-blue-600 hover:text-blue-900 text-sm"
                    >
                      Ask Agent →
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex space-x-4">
          <a 
            href="/dashboard" 
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            View All Orders
          </a>
          <a 
            href="/agent-flow" 
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Run Agent Task
          </a>
        </div>
      </div>
    </div>
  );
}
