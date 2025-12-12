import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Loader2, Sparkles, Terminal } from "lucide-react";
import { ScrollArea } from "./ui/scroll-area";
import { Button } from "./ui/button";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AIConsole = ({ selectedEmitter }) => {
  const [messages, setMessages] = useState([
    {
      role: "system",
      content: "AEGIS MIND AI Assistant online. Ready to provide tactical EW analysis and recommendations.",
      timestamp: new Date().toISOString()
    }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  // Sample queries
  const sampleQueries = [
    "What's the best counter for S-400 in tracking mode?",
    "Analyze all Chinese naval radars",
    "Recommend ECM for current threat environment",
    "What's the kill chain status?"
  ];

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // If emitter is selected, add context message
    if (selectedEmitter) {
      const contextMessage = {
        role: "system",
        content: `Context loaded: ${selectedEmitter.name} (${selectedEmitter.emitter_type}) - ${selectedEmitter.origin}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, contextMessage]);
    }
  }, [selectedEmitter]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/ai/chat`, {
        message: input,
        session_id: "aegis-console"
      });

      const aiMessage = {
        role: "assistant",
        content: response.data.response,
        context: response.data.context,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error("AI chat error:", error);
      const errorMessage = {
        role: "error",
        content: "Communication error with AI system. Please try again.",
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      toast.error("Failed to communicate with AI");
    }

    setIsLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSampleQuery = (query) => {
    setInput(query);
    inputRef.current?.focus();
  };

  return (
    <div className="h-full flex flex-col" data-testid="ai-console">
      {/* Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-2">
          <div className="p-1.5 bg-sky-500/20 rounded-sm">
            <Bot className="w-4 h-4 text-sky-400" />
          </div>
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            AI Console
          </h2>
          <div className="flex-1"></div>
          <div className="flex items-center gap-1.5 text-xs text-green-400">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
            ONLINE
          </div>
        </div>
        <p className="text-xs text-slate-500">
          Gemini 2.5 Flash - Natural language tactical analysis
        </p>
      </div>

      {/* Sample Queries */}
      <div className="p-2 border-b border-slate-800 bg-slate-900/50">
        <div className="flex gap-1 overflow-x-auto pb-1">
          {sampleQueries.map((query, index) => (
            <button
              key={index}
              onClick={() => handleSampleQuery(query)}
              className="px-2 py-1 text-xs bg-slate-800 text-slate-400 hover:text-sky-400 hover:bg-slate-700 rounded-sm whitespace-nowrap transition-colors"
              data-testid={`sample-query-${index}`}
            >
              {query.slice(0, 30)}...
            </button>
          ))}
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-4 space-y-4">
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                <MessageBubble message={message} />
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-2 text-slate-500 text-sm"
            >
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="font-mono">Processing query...</span>
            </motion.div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Terminal className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter tactical query..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 text-slate-100 text-sm font-mono placeholder-slate-500 focus:outline-none focus:border-sky-500 rounded-sm"
              disabled={isLoading}
              data-testid="ai-input"
            />
          </div>
          <Button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="px-4 bg-sky-500/20 border border-sky-500/50 text-sky-400 hover:bg-sky-500 hover:text-slate-900 disabled:opacity-50 disabled:cursor-not-allowed rounded-sm"
            data-testid="ai-send-btn"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

// Message Bubble Component
const MessageBubble = ({ message }) => {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isError = message.role === "error";

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  if (isSystem) {
    return (
      <div className="flex items-start gap-2 text-xs" data-testid="system-message">
        <Sparkles className="w-3.5 h-3.5 text-sky-400 mt-0.5" />
        <div className="flex-1">
          <span className="text-sky-400">[SYSTEM]</span>
          <span className="text-slate-400 ml-2">{message.content}</span>
        </div>
        <span className="text-slate-600 font-mono text-[10px]">{formatTime(message.timestamp)}</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-start gap-2 text-xs text-red-400" data-testid="error-message">
        <span>[ERROR]</span>
        <span>{message.content}</span>
      </div>
    );
  }

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`} data-testid={isUser ? "user-message" : "ai-message"}>
      <div className={`w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-slate-700' : 'bg-sky-500/20'
      }`}>
        {isUser ? (
          <User className="w-4 h-4 text-slate-300" />
        ) : (
          <Bot className="w-4 h-4 text-sky-400" />
        )}
      </div>
      
      <div className={`flex-1 max-w-[85%] ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block p-3 rounded-sm text-sm ${
          isUser 
            ? 'bg-slate-700 text-slate-100' 
            : 'bg-slate-800 text-slate-200 border border-slate-700'
        }`}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        
        {message.context && (
          <div className="mt-2 text-xs text-slate-500 font-mono">
            <span className="text-slate-600">Active emitters: </span>
            {message.context.active_emitters} | 
            <span className="text-red-400 ml-1">Hostile: {message.context.hostile_count}</span>
          </div>
        )}
        
        <div className={`text-[10px] text-slate-600 mt-1 font-mono ${isUser ? 'text-right' : ''}`}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
};

export default AIConsole;
