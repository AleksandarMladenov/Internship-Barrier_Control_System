import { AuthProvider } from "./hooks/useAuth";
import AppRouter from "./router/AppRouter";

export default function App() {
  return (
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  );
}
