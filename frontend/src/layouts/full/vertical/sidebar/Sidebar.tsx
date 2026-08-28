import React from 'react';
import NavCollapse from './nav-collapse';
import SimpleBar from 'simplebar-react';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarHeader,
} from 'src/components/ui/sidebar';
import sidebaritems from './sidebaritems';

const SidebarLayout = ({ ...props }: React.ComponentProps<typeof Sidebar>) => {
  return (
     <Sidebar
            variant="inset"
            collapsible="icon"
            {...props}
            className="sidebar-box **:data-[slot=sidebar-inner]:bg-background **:data-[slot=sidebar-inner]:border **:data-[slot=sidebar-inner]:border-border group-data-[state=collapsed]:hover:shadow-xl"
            side="left"
        >
            <SidebarHeader className="p-3 group-data-[state=collapsed]:px-2.5 flex flex-row items-center border-b border-border">
                <span className="text-lg font-bold tracking-tight group-data-[state=collapsed]:hidden">
                  PSA <span className="text-primary">NEXUS</span>
                </span>
            </SidebarHeader>

            <SidebarContent>
                <SimpleBar style={{ height: "100%" }} >
                    <SidebarGroup className="flex items-center justify-center group-data-[state=collapsed]:px-2 px-3 py-4">
                        <div className="px-0 group-data-[state=collapsed]:px-0 w-full flex flex-col gap-4">
                            <NavCollapse menu={sidebaritems} className="text-sm" />
                        </div>
                    </SidebarGroup>
                </SimpleBar>
            </SidebarContent>
        </Sidebar>
  );
};

export default SidebarLayout;
