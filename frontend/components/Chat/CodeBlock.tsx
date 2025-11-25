import { FC, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";

// Supported languages for syntax highlighting
const SUPPORTED_LANGUAGES = [
  'javascript', 'typescript', 'python', 'java', 'c', 'cpp', 'csharp', 
  'go', 'rust', 'swift', 'kotlin', 'php', 'ruby', 'html', 'css', 'json', 
  'yaml', 'markdown', 'bash', 'shell', 'sql', 'plaintext'
];

interface Props {
  language: string;
  value: string;
}

export const CodeBlock: FC<Props> = ({ language, value }) => {
  const [copied, setCopied] = useState(false);
  
  // Normalize language to supported format
  const normalizedLanguage = language?.toLowerCase().trim() || 'plaintext';
  
  // Check if language is supported, fallback to plaintext if not
  const supportedLanguage = SUPPORTED_LANGUAGES.includes(normalizedLanguage) 
    ? normalizedLanguage 
    : 'plaintext';

  const handleCopy = () => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="relative w-full my-2 bg-black rounded-md overflow-hidden">
      <div className="flex justify-between items-center px-4 py-1 bg-gray-800 text-gray-200 text-xs">
        <span>{supportedLanguage !== 'plaintext' ? supportedLanguage : 'code'}</span>
        <button 
          onClick={handleCopy}
          className="text-xs px-2 py-1 rounded hover:bg-gray-700 transition-colors"
        >
          {copied ? 'Đã sao chép!' : 'Sao chép'}
        </button>
      </div>
      
      <SyntaxHighlighter
        language={supportedLanguage}
        style={vscDarkPlus}
        PreTag="div"
        customStyle={{
          margin: 0,
          padding: "1rem",
          borderRadius: "0 0 0.375rem 0.375rem",
          fontSize: "0.9rem",
          overflow: "auto",
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
}; 