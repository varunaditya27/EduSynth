<div align="center">

# 🎨 EduSynth Frontend

### Next.js 16 Modern Educational Platform Interface

[![Next.js](https://img.shields.io/badge/Next.js-16.0.1-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2.0-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-4.0-38bdf8.svg)](https://tailwindcss.com/)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black.svg)](https://vercel.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A cutting-edge, performant, and accessible frontend for AI-powered educational content generation with stunning animations and interactive visualizations.**

</div>

---

## 📚 Table of Contents

* [🌟 Features](#-features)
* [🏷️ Architecture](#-architecture)
* [🚀 Getting Started](#-getting-started)
* [💻 Development](#-development)
* [📁 Project Structure](#-project-structure)
* [🎨 Styling Guide](#-styling-guide)
* [🧩 Component Library](#-component-library)
* [🚀 Deployment](#-deployment)

---

## 🌟 Features

### ⚡ Performance & Modern Stack

* **Next.js 16 App Router**: Server-side rendering and streaming
* **React 19**: Latest concurrent features and optimizations
* **TypeScript**: Full type safety across the application
* **Tailwind CSS 4**: Utility-first styling with custom design system
* **Edge Runtime Ready**: Optimized for Vercel Edge deployment

### 🎨 Rich User Experience

* **Smooth Animations**

  * GSAP for complex timeline animations
  * Framer Motion for React component animations
  * CSS-based micro-interactions

* **Interactive Visualizations**

  * React Flow / XYFlow for mind maps and flowcharts
  * Real-time content updates
  * Drag-and-drop interfaces

* **Responsive Design**

  * Mobile-first approach
  * Tablet and desktop optimizations
  * Adaptive layouts for all screen sizes

### 🔍 Advanced Features

* **Real-time Content Generation**: Live progress tracking with TanStack Query
* **Code Highlighting**: Syntax highlighting with Highlight.js
* **Markdown Rendering**: Rich markdown support with remark-gfm
* **Dark Mode**: System-aware theme switching
* **Accessibility**: WCAG 2.1 AA compliant
* **Progressive Web App**: Offline-capable with service workers

### 🔒 State Management

* **Zustand**: Lightweight global state management
* **TanStack Query**: Server state and caching
* **React Context**: Feature-specific local state
* **URL State**: Shareable app states via query parameters

---

## 🏗️ Architecture

### Component Architecture

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': { 'primaryColor': '#3b82f6', 'edgeLabelBackground':'#1f2937'}}}%%
graph TB
    subgraph "App Router"
        A[Layout]
        B[Pages]
        C[Loading States]
        D[Error Boundaries]
    end
    
    subgraph "Component Layer"
        E[UI Components]
        F[Feature Components]
        G[Layout Components]
    end
    
    subgraph "State Management"
        H[Zustand Store]
        I[TanStack Query]
        J[React Context]
    end
    
    subgraph "Data Layer"
        K[API Client]
        L[WebSocket Client]
        M[Local Storage]
    end
    
    A --> B
    B --> C
    B --> D
    B --> F
    F --> E
    F --> G
    
    E --> H
    F --> H
    F --> I
    F --> J
    
    I --> K
    L --> I
    H --> M

    style A fill:#111827,stroke:#2563eb,color:#ffffff
    style H fill:#7c3aed,stroke:#5b21b6,color:#ffffff
    style I fill:#dc2626,stroke:#991b1b,color:#ffffff
```

### Data Flow

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'primaryColor': '#22d3ee', 'edgeLabelBackground': '#0f172a'}}}%%
sequenceDiagram
    participant U as User
    participant C as Component
    participant Z as Zustand Store
    participant Q as TanStack Query
    participant A as API Client
    participant B as Backend
    
    U->>C: Interaction
    C->>Z: Update Local State
    C->>Q: Fetch Data
    Q->>A: HTTP Request
    A->>B: API Call
    B-->>A: Response
    A-->>Q: Data
    Q->>Q: Cache & Normalize
    Q-->>C: Render Data
    C-->>U: UI Update
    
    Note over Q: Automatic Revalidation Cycle
    Q->>A: Background Refresh
    A->>B: Revalidate
    B-->>A: Fresh Data
    A-->>Q: Update
    Q-->>C: Re-render
```

---

## 🚀 Getting Started

(Installation, Development, and Deployment steps remain same as provided)

---

## 📧 Support

* 🐛 [GitHub Issues](https://github.com/varunaditya27/EduSynth/issues)
* 📧 Email: [varun.paparajugari@gmail.com](mailto:varun.paparajugari@gmail.com)
* 💬 [Discussions](https://github.com/varunaditya27/EduSynth/discussions)

---

<div align="center">

**Built with Next.js ⚡ | Styled with Tailwind 🎨 | Powered by React ⚛️**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/varunaditya27/EduSynth)

</div>
