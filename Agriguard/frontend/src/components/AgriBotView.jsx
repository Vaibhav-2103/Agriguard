import React, { useState, useEffect, useRef } from "react";
import { Send, Bot, User, Sparkles, Sprout, CornerDownLeft, RefreshCw, AlertCircle, Trash2, ArrowLeft } from "lucide-react";
import { api } from "../api";
import { translations } from "../translations";

export default function AgriBotView({ activeReport, onBack, lang }) {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [chips, setChips] = useState([]);

  const messagesEndRef = useRef(null);
  const t = translations[lang] || translations.en;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, [activeReport]);

  const loadConversations = async () => {
    try {
      const convList = await api.getConversations();
      setConversations(convList);

      // If activeReport is passed, find or initiate conversation for this report
      if (activeReport) {
        const matchingConv = convList.find(c => c.report_id === activeReport.id);
        if (matchingConv) {
          selectConversation(matchingConv.id);
        } else {
          // Initialize fresh conversation for this report
          setConversationId(null);
          setMessages([
            {
              role: "assistant",
              content: `Namaste! I am AgriBot. I see you are inquiring about **${activeReport.insight?.disease_name || activeReport.predicted_class}** on **${activeReport.crop || 'your crop'}** (${activeReport.severity || 'Medium'} Severity).\n\nHow can I help you protect your crop today?`
            }
          ]);
          setChips(t.quickChips);
        }
      } else if (convList.length > 0) {
        // Load most recent conversation
        selectConversation(convList[0].id);
      } else {
        // General chat greeting
        setMessages([
          {
            role: "assistant",
            content: "Hello! I am AgriBot, your local farm health assistant. Ask me anything about crop diseases, organic treatments, chemical precautions, or scan a leaf photo for a complete cure plan!"
          }
        ]);
        setChips(t.quickChips);
      }
    } catch (err) {
      console.error("Error loading chat conversations:", err);
    }
  };

  const selectConversation = async (convId) => {
    setLoading(true);
    setConversationId(convId);
    try {
      const msgList = await api.getMessages(convId);
      setMessages(msgList);
      setChips(t.quickChips);
    } catch (err) {
      console.error("Failed to load messages:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputText).trim();
    if (!text || isTyping) return;

    // Optimistically append user message
    const tempUserMsg = { role: "user", content: text };
    setMessages(prev => [...prev, tempUserMsg]);
    setInputText("");
    setIsTyping(true);

    try {
      const resp = await api.sendChatMessage(
        text,
        activeReport ? activeReport.id : null,
        conversationId
      );

      setConversationId(resp.conversation_id);
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: resp.reply }
      ]);
      if (resp.quick_chips && resp.quick_chips.length > 0) {
        setChips(resp.quick_chips);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        { role: "assistant", content: "⚠️ Sorry, could not process your message. Please check the local server connection." }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat history?")) return;
    try {
      await api.deleteConversation(convId);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (conversationId === convId) {
        setConversationId(null);
        setMessages([]);
      }
    } catch (err) {
      alert("Failed to delete conversation");
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="bg-white rounded-3xl shadow-lg border border-slate-200 overflow-hidden flex flex-col md:flex-row h-[80vh]">
        {/* Left Sidebar: Conversations History */}
        <div className="hidden md:flex flex-col w-72 bg-slate-50 border-r border-slate-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Chat History
            </h3>
            <button
              onClick={() => {
                setConversationId(null);
                setMessages([
                  {
                    role: "assistant",
                    content: "Hello! I am AgriBot. How can I help you today?"
                  }
                ]);
              }}
              className="text-xs text-emerald-700 hover:text-emerald-800 font-bold"
            >
              + New Chat
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {conversations.map(c => (
              <div
                key={c.id}
                onClick={() => selectConversation(c.id)}
                className={`p-3 rounded-2xl text-xs cursor-pointer transition flex items-center justify-between group ${
                  conversationId === c.id
                    ? "bg-emerald-100 text-emerald-950 font-bold border border-emerald-300"
                    : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200/70"
                }`}
              >
                <div className="truncate pr-2">
                  <p className="truncate">{c.title || "AgriBot Advisory"}</p>
                  <p className="text-[10px] text-slate-400 font-normal mt-0.5">
                    {new Date(c.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => handleDeleteConversation(c.id, e)}
                  className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 transition p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Right Main Chat Area */}
        <div className="flex-1 flex flex-col h-full bg-[#efeae2]/40 relative">
          {/* Header */}
          <div className="bg-white px-6 py-4 border-b border-slate-200 flex items-center justify-between shadow-sm z-10">
            <div className="flex items-center gap-3">
              {onBack && (
                <button
                  onClick={onBack}
                  className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition mr-1"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
              )}
              <div className="w-10 h-10 bg-emerald-700 text-white rounded-2xl flex items-center justify-center shadow-sm">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <span>AgriBot Assistant</span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </h2>
                <p className="text-[11px] text-slate-500">
                  {activeReport ? `Grounded on ${activeReport.crop || 'Crop'} diagnosis` : "Local Rule & Retrieval Engine"}
                </p>
              </div>
            </div>

            {/* Language badge */}
            <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-full uppercase">
              Multilingual (EN / HI / PA)
            </span>
          </div>

          {/* Pinned Diagnosis Context Banner */}
          {activeReport && (
            <div className="bg-emerald-800 text-white px-5 py-2.5 flex items-center justify-between text-xs shadow-inner">
              <div className="flex items-center gap-2">
                <Sprout className="w-4 h-4 text-emerald-300 flex-shrink-0" />
                <span className="truncate">
                  Context: <strong>{activeReport.crop}</strong> — {activeReport.insight?.disease_name || activeReport.predicted_class}
                </span>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                activeReport.severity === "High" ? "bg-red-500" :
                activeReport.severity === "Medium" ? "bg-amber-500" :
                "bg-emerald-500"
              }`}>
                {activeReport.severity || "Healthy"}
              </span>
            </div>
          )}

          {/* Message List */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.map((m, idx) => {
              const isUser = m.role === "user";
              return (
                <div
                  key={idx}
                  className={`flex items-end gap-2 ${isUser ? "justify-end" : "justify-start"}`}
                >
                  {!isUser && (
                    <div className="w-7 h-7 rounded-xl bg-emerald-700 text-white flex items-center justify-center text-xs flex-shrink-0 mb-1 shadow-sm">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] sm:max-w-[75%] px-4 py-3 text-xs leading-relaxed shadow-sm whitespace-pre-wrap ${
                      isUser
                        ? "bg-emerald-700 text-white rounded-2xl rounded-br-none"
                        : "bg-white text-slate-800 border border-slate-200/90 rounded-2xl rounded-bl-none"
                    }`}
                  >
                    {m.content}
                  </div>

                  {isUser && (
                    <div className="w-7 h-7 rounded-xl bg-slate-700 text-white flex items-center justify-center text-xs flex-shrink-0 mb-1 shadow-sm">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex items-end gap-2 justify-start">
                <div className="w-7 h-7 rounded-xl bg-emerald-700 text-white flex items-center justify-center text-xs flex-shrink-0 mb-1 shadow-sm">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 rounded-full bg-emerald-600 animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick-Question Chips */}
          <div className="px-4 py-2 bg-white/95 border-t border-slate-200/60 overflow-x-auto flex items-center gap-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex-shrink-0">
              Ask Quick:
            </span>
            {chips.map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSendMessage(chip)}
                className="whitespace-nowrap px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-[11px] font-semibold rounded-full border border-emerald-200 transition active:scale-95 flex-shrink-0"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Chat Input Bar */}
          <form
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
            className="p-3 bg-white border-t border-slate-200 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={t.chatPlaceholder}
              className="flex-1 py-3 px-4 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium text-slate-800"
            />
            <button
              type="submit"
              disabled={!inputText.trim() || isTyping}
              className={`p-3 rounded-2xl font-bold shadow transition flex items-center justify-center ${
                !inputText.trim() || isTyping
                  ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                  : "bg-emerald-700 hover:bg-emerald-800 text-white active:scale-95"
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
