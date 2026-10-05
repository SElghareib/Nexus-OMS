'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { agentApi } from '@/lib/api';
import { FlowData } from '@/types';

export default function AgentFlowPage() {
  const searchParams = useSearchParams();
  const taskId = searchParams.get('task');
  
  const [flowData, setFlowData] = useState<FlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadFlowData() {
      if (!taskId) {
        setError('No task ID provided');
        setLoading(false);
        return;
      }

      try {
        const data = await agentApi.getFlowData(taskId);
        setFlowData(data);
      } catch (err) {
        console.error('Failed to load flow data:', err);
        setError('Failed to load execution trace. The task may not exist yet.');
      } finally {
        setLoading(false);
      }
    }

    loadFlowData();
  }, [taskId]);

  // Transform backend nodes to React Flow format
  const nodes = flowData?.nodes.map((node) => ({
    id: node.id,
    type: node.type,
    position: node.position,
    data: { 
      label: node.label,
      status: node.status,
      ...node.data,
    },
    className: `react-flow__node-${node.type} ${node.status}`,
  })) || [];

  const edges = flowData?.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    animated: edge.animated,
    style: edge.style,
  })) || [];

  if (loading) {
    return <div className="text-center py-12">Loading execution trace...</div>;
  }

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Agent Execution Flow</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-800">{error}</p>
          <a href="/dashboard" className="text-blue-600 hover:underline mt-2 inline-block">
            ← Back to Dashboard
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 h-[calc(100vh-12rem)]">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agent Execution Flow</h1>
          <p className="text-gray-600 mt-1">Task ID: {taskId}</p>
          <p className="text-sm text-gray-500 mt-1">
            Status: <span className={`font-medium ${flowData?.status === 'success' ? 'text-green-600' : flowData?.status === 'failed' ? 'text-red-600' : 'text-yellow-600'}`}>
              {flowData?.status}
            </span>
          </p>
        </div>
        <a 
          href="/dashboard" 
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
        >
          ← Back to Dashboard
        </a>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg shadow h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          attributionPosition="bottom-left"
        >
          <Background />
          <Controls />
          <MiniMap 
            nodeColor={(node) => {
              if (node.className?.includes('success')) return '#22c55e';
              if (node.className?.includes('failed')) return '#ef4444';
              if (node.className?.includes('waiting_approval')) return '#f97316';
              if (node.className?.includes('plan')) return '#3b82f6';
              return '#6b7280';
            }}
          />
        </ReactFlow>
      </div>

      {/* Legend */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Legend</h3>
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-100 border-2 border-blue-500"></div>
            <span>Plan Node</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-yellow-100 border-2 border-yellow-500"></div>
            <span>Tool Execution</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-100 border-2 border-green-500"></div>
            <span>Success</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-100 border-2 border-red-500"></div>
            <span>Failed</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-orange-100 border-2 border-orange-500"></div>
            <span>Awaiting Approval</span>
          </div>
        </div>
      </div>
    </div>
  );
}
