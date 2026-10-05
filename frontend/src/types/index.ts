// Type definitions for Nexus OMS Frontend

export interface Order {
  id: number;
  customer_id: number;
  status: OrderStatus;
  total_amount: number;
  discount_percent: number;
  items: OrderItem[];
  shipping_address: Address;
  notes?: string;
  is_stuck: boolean;
  stuck_reason?: string;
  created_at: string;
  updated_at?: string;
}

export type OrderStatus = 
  | 'pending'
  | 'processing'
  | 'shipped'
  | 'delivered'
  | 'cancelled'
  | 'stuck'
  | 'refunded';

export interface OrderItem {
  product_id: number;
  product_name?: string;
  quantity: number;
  price: number;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
}

export interface Customer {
  id: number;
  email: string;
  name: string;
  tier: 'standard' | 'premium' | 'vip';
  created_at: string;
  updated_at?: string;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description?: string;
  price: number;
  stock_level: number;
  created_at: string;
  updated_at?: string;
}

// Agent Types
export interface AgentTaskRequest {
  task_description: string;
  order_id?: number;
  customer_id?: number;
  require_approval?: boolean;
}

export interface AgentTaskResponse {
  task_id: string;
  success: boolean;
  result: any;
  execution_trace: ExecutionTrace;
  message: string;
  requires_approval: boolean;
  pending_actions: PendingAction[];
}

export interface ExecutionTrace {
  nodes: FlowNode[];
  edges: FlowEdge[];
}

export interface FlowNode {
  id: string;
  type: 'plan' | 'tool' | 'result';
  label: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'waiting_approval';
  data: Record<string, any>;
  position: { x: number; y: number };
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
  style?: Record<string, any>;
}

export interface FlowData {
  nodes: FlowNode[];
  edges: FlowEdge[];
  task_id: string;
  status: string;
}

export interface PendingAction {
  step_id: string;
  approval_node_id: string;
  tool_name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface ToolInfo {
  name: string;
  description: string;
  permission_level: 'read' | 'low_risk_write' | 'high_risk_write';
  requires_approval: boolean;
  parameters: Record<string, ParameterInfo>;
}

export interface ParameterInfo {
  type: string;
  description: string;
}
