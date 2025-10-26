import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";

export function Header() {
  const location = useLocation();

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Don&apos;t Truck Stupid</h1>
        <div className="flex gap-2">
          <Link to="/customers">
            <Button variant={location.pathname === "/customers" ? "default" : "outline"}>
              Why DTS
            </Button>
          </Link>
          <Link to="/investors">
            <Button variant={location.pathname === "/investors" ? "default" : "outline"}>
              Investors
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );
}