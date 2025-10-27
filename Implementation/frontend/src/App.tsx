import { useEffect, useState } from "react";
import { api } from "./lib/api";

function App() {
  const [msg, setMsg] = useState("Loading...");

  useEffect(() => {
    api.get("/health")
      .then(res => setMsg(JSON.stringify(res.data)))
      .catch(err => setMsg("Error: " + err.message));
  }, []);

  return (
    <main style={{
      minHeight: "100vh",
      display: "grid",
      placeItems: "center",
      fontFamily: "sans-serif",
    }}>
      <div>
        <h1>React ↔ FastAPI</h1>
        <p>{msg}</p>
      </div>
    </main>
  );
}

export default App;
