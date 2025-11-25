import { FC } from "react";
import { useDarkMode } from "../Contexts/DarkModeContext";

export const Footer: FC = () => {
  const { darkMode } = useDarkMode();
  
  return (
    <footer className="py-4">
      <div className={`max-w-[800px] mx-auto px-4 text-center ${darkMode ? 'text-gray-300' : 'text-white'} text-sm ${darkMode ? '' : 'drop-shadow-[1px_1px_0px_black]'}`}>
        <p>SoICT Innovation Club - 1 sản phẩm phục vụ Innovation Day 2025</p>
      </div>
    </footer>
  );
}; 