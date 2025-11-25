declare module 'react-markdown' {
  import { ReactNode } from 'react';

  interface CodeProps {
    node?: any;
    inline?: boolean;
    className?: string;
    children?: ReactNode;
    [key: string]: any;
  }

  interface ReactMarkdownProps {
    children: string;
    components?: {
      [key: string]: React.ComponentType<any>;
      code?: React.ComponentType<CodeProps>;
    };
  }

  const ReactMarkdown: React.FC<ReactMarkdownProps>;
  export default ReactMarkdown;
} 