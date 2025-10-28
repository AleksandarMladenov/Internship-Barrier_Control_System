import { FcGoogle } from "react-icons/fc";
import { FaApple } from "react-icons/fa";
import "./SocialLoginButtons.css";

export default function SocialLoginButtons() {
  return (
    <div className="social-row">
      <button type="button" className="social-btn google">
        <FcGoogle size={20} />
        <span>Continue with Google</span>
      </button>

      <button type="button" className="social-btn apple">
        <FaApple size={20} />
        <span>Continue with Apple</span>
      </button>
    </div>
  );
}
