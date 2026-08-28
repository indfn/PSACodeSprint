// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { lazy } from 'react';
import { Navigate, createBrowserRouter } from 'react-router';
import Loadable from '../layouts/full/shared/loadable/Loadable';

/* ***Layouts**** */
const FullLayout = Loadable(lazy(() => import('../layouts/full/FullLayout')));

// dashboards
const NexusDashboard = Loadable(lazy(() => import('../views/dashboards/modern')));
const AgentTrace = Loadable(lazy(() => import('../views/agent-trace')));
const History = Loadable(lazy(() => import('../views/history')));

const Router = [
  {
    path: '/',
    element: <FullLayout />,
    children: [
      { path: '/', element: <NexusDashboard /> },
      { path: '/trace', element: <AgentTrace /> },
      { path: '/history', element: <History /> },
      { path: '*', element: <Navigate to="/" /> },
    ],
  },
];

const router = createBrowserRouter(Router);

export default router;
