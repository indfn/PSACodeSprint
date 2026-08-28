// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore

import { Suspense, ComponentType, FC } from 'react';

function Spinner() {
  return (
    <div className="flex h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
    </div>
  );
}

// ===========================|| LOADABLE - LAZY LOADING ||=========================== //

const Loadable =
  <P extends object>(Component: ComponentType<P>): FC<P> =>
  (props: P) =>
    (
      <Suspense fallback={<Spinner />}>
        <Component {...props} />
      </Suspense>
    );

export default Loadable;
