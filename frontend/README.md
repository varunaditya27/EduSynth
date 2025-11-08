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

- [🌟 Features](#-features)
- [🏗️ Architecture](#-architecture)
- [🚀 Getting Started](#-getting-started)
- [💻 Development](#-development)
- [📁 Project Structure](#-project-structure)
- [🎨 Styling Guide](#-styling-guide)
- [🧩 Component Library](#-component-library)
- [🚀 Deployment](#-deployment)

---

## 🌟 Features

### ⚡ Performance & Modern Stack

- **Next.js 16 App Router**: Server-side rendering and streaming
- **React 19**: Latest concurrent features and optimizations
- **TypeScript**: Full type safety across the application
- **Tailwind CSS 4**: Utility-first styling with custom design system
- **Edge Runtime Ready**: Optimized for Vercel Edge deployment

### 🎨 Rich User Experience

- **Smooth Animations**
  - GSAP for complex timeline animations
  - Framer Motion for React component animations
  - CSS-based micro-interactions
  
- **Interactive Visualizations**
  - React Flow / XYFlow for mind maps and flowcharts
  - Real-time content updates
  - Drag-and-drop interfaces

- **Responsive Design**
  - Mobile-first approach
  - Tablet and desktop optimizations
  - Adaptive layouts for all screen sizes

### 🔍 Advanced Features

- **Real-time Content Generation**: Live progress tracking with TanStack Query
- **Code Highlighting**: Syntax highlighting with Highlight.js
- **Markdown Rendering**: Rich markdown support with remark-gfm
- **Dark Mode**: System-aware theme switching
- **Accessibility**: WCAG 2.1 AA compliant
- **Progressive Web App**: Offline-capable with service workers

### 🔒 State Management

- **Zustand**: Lightweight global state management
- **TanStack Query**: Server state and caching
- **React Context**: Feature-specific local state
- **URL State**: Shareable app states via query parameters

---

## 🏗️ Architecture

### Component Architecture

```mermaid
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
    
    style A fill:#000000,stroke:#ffffff,color:#ffffff
    style H fill:#764abc,stroke:#5a2d8c,color:#ffffff
    style I fill:#ff4154,stroke:#cc1a2b,color:#ffffff
</mermaid>

### Data Flow

```mermaid
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
    
    Note over Q: Automatic revalidation
    Q->>A: Background Refresh
    A->>B: Revalidate
    B-->>A: Fresh Data
    A-->>Q: Update
    Q-->>C: Re-render
```

---

## 🚀 Getting Started

### Prerequisites

```bash
Node.js 20.x or higher
npm, yarn, or pnpm
Git
```

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Set up environment variables**
   
   Create `.env.local` file:
   ```env
   # API Configuration
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   
   # Feature Flags
   NEXT_PUBLIC_ENABLE_ANALYTICS=true
   NEXT_PUBLIC_ENABLE_ANIMATIONS=true
   
   # Optional: External Services
   NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
   ```

4. **Run development server**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

5. **Open your browser**
   
   Navigate to [http://localhost:3000](http://localhost:3000)

---

## 💻 Development

### Available Scripts

```bash
# Development server with hot reload
npm run dev

# Production build
npm run build

# Start production server
npm run start

# Lint code
npm run lint

# Type check
npx tsc --noEmit

# Format code (if prettier is configured)
npm run format
```

### Development Workflow

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Follow the project structure
   - Write TypeScript with proper types
   - Use existing components when possible
   - Add new components to appropriate directories

3. **Test locally**
   ```bash
   npm run dev
   # Test all features
   npm run build  # Ensure production build works
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

---

## 📁 Project Structure

```
frontend/
├── app/                          # Next.js App Router
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Home page
│   ├── globals.css              # Global styles
│   │
│   ├── (dashboard)/            # Dashboard route group
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── generate/
│   │
│   ├── (auth)/                 # Auth route group
│   │   ├── login/
│   │   └── signup/
│   │
│   └── api/                    # API routes
│       └── ...
│
├── components/                  # React components
│   ├── ui/                     # Reusable UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   └── ...
│   │
│   ├── features/              # Feature-specific components
│   │   ├── content-generator/
│   │   ├── animation-viewer/
│   │   ├── mindmap-visualizer/
│   │   └── export-manager/
│   │
│   └── layout/                # Layout components
│       ├── header.tsx
│       ├── footer.tsx
│       ├── sidebar.tsx
│       └── navigation.tsx
│
├── contexts/                    # React contexts
│   ├── theme-context.tsx
│   ├── auth-context.tsx
│   └── content-context.tsx
│
├── lib/                         # Utility functions
│   ├── utils.ts               # General utilities
│   ├── api-client.ts          # API client
│   ├── hooks/                 # Custom React hooks
│   │   ├── useContent.ts
│   │   ├── useAnimation.ts
│   │   └── useMindMap.ts
│   │
│   ├── stores/                # Zustand stores
│   │   ├── contentStore.ts
│   │   ├── uiStore.ts
│   │   └── authStore.ts
│   │
│   └── types/                 # TypeScript types
│       ├── content.ts
│       ├── animation.ts
│       └── user.ts
│
├── public/                      # Static files
│   ├── fonts/
│   ├── images/
│   └── icons/
│
├── .eslintrc.json              # ESLint config
├── next.config.ts              # Next.js config
├── tailwind.config.ts          # Tailwind config
├── tsconfig.json               # TypeScript config
├── package.json
└── README.md
```

---

## 🎨 Styling Guide

### Tailwind CSS Configuration

The project uses a custom design system built on Tailwind CSS:

```typescript
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        // Brand colors
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
        // ... more colors
      },
      fontFamily: {
        sans: ['Space Grotesk', 'system-ui'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
    },
  },
}
```

### Component Styling Patterns

#### Using Class Variance Authority (CVA)

```tsx
import { cva } from 'class-variance-authority'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary text-white hover:bg-primary/90',
        outline: 'border border-input hover:bg-accent',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3 rounded-md',
        lg: 'h-11 px-8 rounded-md',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)
```

#### Using Tailwind Merge

```tsx
import { cn } from '@/lib/utils'

function Component({ className }: { className?: string }) {
  return (
    <div className={cn('p-4 bg-white rounded-lg', className)}>
      Content
    </div>
  )
}
```

### Typography

```css
/* globals.css */
@layer base {
  h1 {
    @apply text-4xl font-bold tracking-tight;
  }
  h2 {
    @apply text-3xl font-semibold tracking-tight;
  }
  p {
    @apply text-base leading-7;
  }
}
```

---

## 🧩 Component Library

### UI Components

All UI components follow a consistent API:

```tsx
// Button Component
import { Button } from '@/components/ui/button'

<Button variant="default" size="lg">
  Click Me
</Button>

// Card Component
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>

// Dialog Component
import { Dialog, DialogTrigger, DialogContent } from '@/components/ui/dialog'

<Dialog>
  <DialogTrigger>Open</DialogTrigger>
  <DialogContent>
    Dialog content
  </DialogContent>
</Dialog>
```

### Animation Components

```tsx
import { motion } from 'framer-motion'

function AnimatedComponent() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      Content
    </motion.div>
  )
}
```

### Custom Hooks

```tsx
// useContent Hook
import { useContent } from '@/lib/hooks/useContent'

function Component() {
  const { data, isLoading, error } = useContent(contentId)
  
  if (isLoading) return <Loading />
  if (error) return <Error error={error} />
  
  return <Content data={data} />
}
```

---

## 🚀 Deployment

### Vercel Deployment (Recommended)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Import in Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel auto-detects Next.js configuration

3. **Configure Environment Variables**
   - Add all `NEXT_PUBLIC_*` variables
   - Set production API URLs

4. **Deploy**
   - Click "Deploy"
   - Automatic deployments on every push

### Docker Deployment

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

```bash
# Build and run
docker build -t edusynth-frontend .
docker run -p 3000:3000 edusynth-frontend
```

### Performance Optimization

- ✅ Image optimization with `next/image`
- ✅ Font optimization with `next/font`
- ✅ Code splitting with dynamic imports
- ✅ React Server Components for reduced bundle size
- ✅ Streaming SSR for faster initial loads
- ✅ Edge Runtime for low-latency responses

---

## 📊 Performance Metrics

### Target Metrics

- **First Contentful Paint (FCP)**: < 1.0s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Time to Interactive (TTI)**: < 3.0s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Lighthouse Score**: > 90

### Monitoring

```tsx
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
```

---

## 🤝 Contributing

### Code Standards

1. **TypeScript**
   - Strict mode enabled
   - No `any` types
   - Proper interface definitions

2. **React Best Practices**
   - Functional components only
   - Custom hooks for logic reuse
   - Proper memoization with `useMemo` / `useCallback`

3. **Accessibility**
   - Semantic HTML
   - ARIA labels where needed
   - Keyboard navigation support
   - Screen reader compatibility

### Pull Request Process

1. Create a feature branch
2. Write/update tests
3. Update documentation
4. Run linting and type checks
5. Submit PR with clear description
6. Address review feedback

---

## 📝 License

MIT License - see [LICENSE](../LICENSE) for details.

---

## 📧 Support

- 🐛 [GitHub Issues](https://github.com/varunaditya27/EduSynth/issues)
- 📧 Email: varun.paparajugari@gmail.com
- 💬 [Discussions](https://github.com/varunaditya27/EduSynth/discussions)

---

<div align="center">

**Built with Next.js ⚡ | Styled with Tailwind 🎨 | Powered by React ⚛️**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/varunaditya27/EduSynth)

</div>
