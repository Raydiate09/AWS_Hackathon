import './App.css'
import { Button } from "@/components/modern-ui/button";

function ButtonDemo() {
  return <Button>Click me</Button>;
}

function App() {
  return (
    <div className="landing-page">
      <h1>Welcome to Our Landing Page</h1>
      <ButtonDemo />
    </div>
  )
}

export default App
