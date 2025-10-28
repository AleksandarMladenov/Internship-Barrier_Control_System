export default function Button({ kind="default", className="", ...props }) {
  const base = "px-3 py-2 rounded-md border text-sm";
  const styles = {
    default: "bg-white border-[#cfd8dc]",
    primary: "bg-[#166a5a] text-white border-[#166a5a]",
    danger:  "bg-[#fff0f1] text-[#b00020] border-[#ffd1d6]"
  };
  return <button className={`${base} ${styles[kind]} ${className}`} {...props} />;
}
