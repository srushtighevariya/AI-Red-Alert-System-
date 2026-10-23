import { useState } from "react";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import "./index.css";

function App() {
  const savedUser = localStorage.getItem("user");
  const [user, setUser] = useState(savedUser ? JSON.parse(savedUser) : null);

  function handleLogout() {
    localStorage.clear();
    setUser(null);
  }

  if (!user) {
    return <LoginPage onLogin={setUser} />;
  }

  return <DashboardPage user={user} onLogout={handleLogout} />;
}

export default App;