import { cls } from "./utils"
import { FileText, ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"

function SourceCitation({ sources }) {
  const [expanded, setExpanded] = useState(false)
  
  if (!sources || sources.length === 0) return null
  
  return (
    <div className="mt-3 border-t border-zinc-200 dark:border-zinc-700 pt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300"
      >
        <FileText className="h-3.5 w-3.5" />
        <span>📚 {sources.length} nguồn tham khảo</span>
        {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
      </button>
      
      {expanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, index) => (
            <div
              key={index}
              className="rounded-lg bg-zinc-50 dark:bg-zinc-800/50 p-2 text-xs"
            >
              <div className="flex items-center gap-1.5 font-medium text-zinc-700 dark:text-zinc-300">
                <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30 text-[10px] text-blue-600 dark:text-blue-400">
                  {index + 1}
                </span>
                <span className="truncate">{source.source}</span>
                <span className="text-zinc-400">• Trang {source.page + 1}</span>
              </div>
              <p className="mt-1 line-clamp-2 text-zinc-500 dark:text-zinc-400">
                {source.content.substring(0, 150)}...
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Message({ role, children, sources }) {
  const isUser = role === "user"
  return (
    <div className={cls("flex gap-3", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="mt-0.5 grid h-7 w-7 flex-shrink-0 place-items-center rounded-full bg-gradient-to-br from-red-500 to-blue-600 text-[10px] font-bold text-white">
          AI
        </div>
      )}
      <div
        className={cls(
          "max-w-[80%] rounded-2xl px-3 py-2 text-sm shadow-sm",
          isUser
            ? "bg-zinc-900 text-white dark:bg-white dark:text-zinc-900"
            : "bg-white text-zinc-900 dark:bg-zinc-900 dark:text-zinc-100 border border-zinc-200 dark:border-zinc-800",
        )}
      >
        {children}
        {!isUser && sources && <SourceCitation sources={sources} />}
      </div>
      {isUser && (
        <div className="mt-0.5 grid h-7 w-7 flex-shrink-0 place-items-center rounded-full bg-zinc-900 text-[10px] font-bold text-white dark:bg-white dark:text-zinc-900">
          U
        </div>
      )}
    </div>
  )
}
