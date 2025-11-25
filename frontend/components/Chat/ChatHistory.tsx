import { FC } from "react";
import { Message } from "@/types";

interface ChatHistoryItem {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  history: ChatHistoryItem[];
  onSelectChat: (messages: Message[]) => void;
  currentChatId: string | null;
}

export const ChatHistory: FC<Props> = ({ isOpen, onClose, history, onSelectChat, currentChatId }) => {
  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-80 bg-white shadow-lg transform transition-transform duration-300 ease-in-out z-50 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">Chat History</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* History List */}
          <div className="flex-1 overflow-y-auto p-4">
            {history.length === 0 ? (
              <p className="text-gray-500 text-center">No chat history</p>
            ) : (
              <div className="space-y-2">
                {history.map((chat) => (
                  <button
                    key={chat.id}
                    onClick={() => onSelectChat(chat.messages)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      currentChatId === chat.id
                        ? "bg-blue-50 text-blue-600"
                        : "hover:bg-gray-50"
                    }`}
                  >
                    <div className="font-medium truncate">{chat.title}</div>
                    <div className="text-sm text-gray-500">
                      {new Date(chat.createdAt).toLocaleDateString()}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}; 