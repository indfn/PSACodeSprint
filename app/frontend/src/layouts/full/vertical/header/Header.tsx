import { useSidebar } from "src/components/ui/sidebar";
import { Button } from "src/components/ui/button";
import { PanelLeft } from 'lucide-react';
import { cn } from "src/lib/utils";
import LightDark from "./Light-Dark";

const Header = () => {
  const { toggleSidebar } = useSidebar();

  return (
    <header className={cn("sticky top-0 z-2 bg-background border-b border-border")}>
      <nav>
        <div className="mx-auto flex flex-wrap items-center justify-between p-2">
          <div className="flex gap-2 items-center">
            <Button
              variant="ghost"
              size="icon"
              className="p-2 hover:bg-primary/5 rounded-full transition cursor-pointer"
              onClick={toggleSidebar}
            >
              <PanelLeft size={21} />
            </Button>
          </div>

          <div className="flex sm:gap-1 gap-0 items-center">
            <LightDark />
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;
