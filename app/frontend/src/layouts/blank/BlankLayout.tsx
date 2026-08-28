import { Outlet } from "react-router";
import { useEffect } from "react";
import { useLocation } from "react-router";

function ScrollToTop({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return <>{children}</>;
}

const BlankLayout = () => (
  <>
    <ScrollToTop>
      <Outlet />
    </ScrollToTop>
  </>
);

export default BlankLayout;
