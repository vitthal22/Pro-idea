"use client";

import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useUiStore } from "@/stores/ui-store";

/**
 * Desktop-only collapse control. Lives in the sidebar footer as a normal row
 * so it reads as a utility action rather than a floating icon, and stays
 * permanently in the tab order.
 */
export function SidebarToggle() {
  const collapsed = useUiStore((state) => state.collapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const label = collapsed ? "Expand sidebar" : "Collapse sidebar";

  return (
    <Button
      variant="ghost"
      onClick={toggleSidebar}
      aria-expanded={!collapsed}
      aria-controls="app-sidebar"
      title={label}
      className="hidden h-9 w-full justify-start gap-3 px-3 text-muted-foreground md:inline-flex group-data-[collapsed=true]/sidebar:justify-center group-data-[collapsed=true]/sidebar:px-0"
    >
      {collapsed ? (
        <PanelLeftOpen className="size-4 shrink-0" />
      ) : (
        <PanelLeftClose className="size-4 shrink-0" />
      )}
      <span className="group-data-[collapsed=true]/sidebar:sr-only">
        {label}
      </span>
    </Button>
  );
}
