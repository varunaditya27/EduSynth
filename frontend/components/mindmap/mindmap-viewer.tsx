'use client';

import { useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { MindMapData } from '@/lib/api';
import { motion } from 'framer-motion';

interface MindmapViewerProps {
  mindmapData: MindMapData;
  className?: string;
}

// Custom node styles matching your color scheme
const nodeStyles = {
  central: {
    background: 'linear-gradient(135deg, rgb(99 102 241) 0%, rgb(139 92 246) 100%)',
    color: 'white',
    border: '3px solid rgb(79 70 229)',
    borderRadius: '16px',
    padding: '16px 24px',
    fontSize: '18px',
    fontWeight: 'bold',
    boxShadow: '0 10px 30px rgba(99, 102, 241, 0.4)',
  },
  branch: {
    background: 'linear-gradient(135deg, rgb(139 92 246) 0%, rgb(168 85 247) 100%)',
    color: 'white',
    border: '2px solid rgb(124 58 237)',
    borderRadius: '12px',
    padding: '12px 20px',
    fontSize: '15px',
    fontWeight: '600',
    boxShadow: '0 8px 24px rgba(139, 92, 246, 0.3)',
  },
  child: {
    background: 'linear-gradient(135deg, rgb(236 72 153) 0%, rgb(219 39 119) 100%)',
    color: 'white',
    border: '1px solid rgb(219 39 119)',
    borderRadius: '10px',
    padding: '10px 16px',
    fontSize: '13px',
    fontWeight: '500',
    boxShadow: '0 6px 20px rgba(236, 72, 153, 0.3)',
  },
};

export default function MindmapViewer({ mindmapData, className }: MindmapViewerProps) {
  // Convert mindmap data to ReactFlow nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Central node (root)
    nodes.push({
      id: mindmapData.central.id,
      data: {
        label: (
          <div className="text-center">
            <div className="font-bold">{mindmapData.central.label}</div>
            {mindmapData.central.description && (
              <div className="text-xs mt-1 opacity-90">{mindmapData.central.description}</div>
            )}
          </div>
        ),
      },
      position: { x: 0, y: 0 },
      type: 'default',
      style: nodeStyles.central,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    });

    // Calculate positions for branches in a radial layout
    const branchCount = mindmapData.branches.length;
    const angleStep = (2 * Math.PI) / branchCount;
    const branchRadius = 300;
    const childRadius = 200;

    mindmapData.branches.forEach((branch, branchIndex) => {
      const branchAngle = angleStep * branchIndex - Math.PI / 2; // Start from top
      const branchX = Math.cos(branchAngle) * branchRadius;
      const branchY = Math.sin(branchAngle) * branchRadius;

      // Add branch node
      nodes.push({
        id: branch.id,
        data: {
          label: (
            <div className="text-center">
              <div className="font-semibold">{branch.label}</div>
              {branch.description && (
                <div className="text-xs mt-1 opacity-90 max-w-[200px]">{branch.description}</div>
              )}
            </div>
          ),
        },
        position: { x: branchX, y: branchY },
        type: 'default',
        style: nodeStyles.branch,
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      });

      // Add edge from central to branch
      edges.push({
        id: `${mindmapData.central.id}-${branch.id}`,
        source: mindmapData.central.id,
        target: branch.id,
        type: 'smoothstep',
        animated: false,
        style: { stroke: 'rgb(139 92 246)', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'rgb(139 92 246)',
        },
      });

      // Add children nodes
      const childCount = branch.children.length;
      branch.children.forEach((child, childIndex) => {
        // Position children around their parent branch
        const childAngleOffset = (childIndex - (childCount - 1) / 2) * 0.4; // Spread children
        const childAngle = branchAngle + childAngleOffset;
        const childX = branchX + Math.cos(childAngle) * childRadius;
        const childY = branchY + Math.sin(childAngle) * childRadius;

        // Add child node
        nodes.push({
          id: child.id,
          data: {
            label: (
              <div className="text-center">
                <div className="font-medium">{child.label}</div>
                {child.description && (
                  <div className="text-xs mt-1 opacity-90 max-w-[180px]">{child.description}</div>
                )}
              </div>
            ),
          },
          position: { x: childX, y: childY },
          type: 'default',
          style: nodeStyles.child,
          sourcePosition: Position.Right,
          targetPosition: Position.Left,
        });

        // Add edge from branch to child
        edges.push({
          id: `${branch.id}-${child.id}`,
          source: branch.id,
          target: child.id,
          type: 'smoothstep',
          animated: false,
          style: { stroke: 'rgb(236 72 153)', strokeWidth: 1.5 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: 'rgb(236 72 153)',
          },
        });
      });
    });

    // Add cross-connections
    mindmapData.connections.forEach((connection, index) => {
      edges.push({
        id: `connection-${index}`,
        source: connection.from,
        target: connection.to,
        type: 'straight',
        animated: true,
        style: {
          stroke: 'rgb(251 146 60)',
          strokeWidth: 2,
          strokeDasharray: '5,5',
        },
        label: connection.type,
        labelStyle: {
          fill: 'rgb(251 146 60)',
          fontWeight: 600,
          fontSize: 12,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: 'rgb(251 146 60)',
        },
      });
    });

    return { nodes, edges };
  }, [mindmapData]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={className}
      style={{ width: '100%', height: '100%' }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.6 }}
        className="bg-linear-to-br from-gray-950 to-gray-900"
      >
        <Background color="#4B5563" gap={20} size={1} />
        <Controls
          className="bg-gray-800/80 backdrop-blur-md border border-white/10 rounded-lg"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === 'root') return 'rgb(99 102 241)';
            if (node.style?.background?.toString().includes('139 92 246')) return 'rgb(139 92 246)';
            return 'rgb(236 72 153)';
          }}
          className="bg-gray-800/80 backdrop-blur-md border border-white/10 rounded-lg"
          maskColor="rgba(0, 0, 0, 0.6)"
        />
      </ReactFlow>
    </motion.div>
  );
}
