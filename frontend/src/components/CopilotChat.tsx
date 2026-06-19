import React, { useState } from 'react';
import { MessageSquare, Send, X, Bot, User } from 'lucide-react';
import axios from 'axios';

interface Message {
  sender: 'user' | 'copilot';
  text: string;
}

export default function CopilotChat({ cityId = 'bengaluru' }: { cityId?: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'copilot', text: 'Hi! I am RouteGuard AI Copilot. Ask me about critical bottlenecks, structural failures, or safe evacuation routes.' }
  ]);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userQuery = query;
    setQuery('');
    setMessages(prev => [...prev, { sender: 'user', text: userQuery }]);
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/simulations/feed/copilot', {
        query: userQuery,
        cityId
      });
      setMessages(prev => [...prev, { sender: 'copilot', text: response.data.reply }]);
    } catch (err) {
      setMessages(prev => [...prev, { sender: 'copilot', text: 'Sorry, I am having trouble connecting to the graph engine.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-[1000] flex flex-col items-end">
      {isOpen ? (
        <div className="w-80 h-96 glass-panel rounded-2xl flex flex-col justify-between overflow-hidden shadow-2xl border border-slate-800 animate-fade-in">
          {/* Header */}
          <div className="bg-card px-4 py-3 flex items-center justify-between border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              <div>
                <h4 className="text-xs font-bold tracking-wider">AI MOBILITY COPILOT</h4>
                <span className="text-[9px] text-success font-semibold">ONLINE</span>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex gap-2 max-w-[85%] ${m.sender === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
                <div className={`w-6 h-6 rounded-full shrink-0 flex items-center justify-center text-[10px] ${
                  m.sender === 'user' ? 'bg-primary text-white' : 'bg-slate-800 text-slate-300'
                }`}>
                  {m.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                </div>
                <div className={`rounded-xl px-3 py-2 text-xs leading-normal ${
                  m.sender === 'user' ? 'bg-primary text-white rounded-tr-none' : 'bg-slate-900 border border-slate-800 text-slate-300 rounded-tl-none'
                }`}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-2 self-start max-w-[85%] animate-pulse">
                <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center"><Bot className="w-3.5 h-3.5 text-slate-400" /></div>
                <div className="bg-slate-900 border border-slate-800 rounded-xl rounded-tl-none px-3 py-2 text-xs text-slate-400">Typing analysis...</div>
              </div>
            )}
          </div>

          {/* Footer input */}
          <form onSubmit={handleSend} className="p-3 border-t border-slate-800/80 bg-slate-950/40 flex gap-2">
            <input
              type="text"
              placeholder="Ask RouteGuard AI..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-slate-700"
            />
            <button type="submit" className="bg-primary hover:bg-primary/95 text-white p-2 rounded-lg transition-all shrink-0">
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="w-12 h-12 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/30 text-white hover:scale-105 transition-all"
        >
          <MessageSquare className="w-5 h-5" />
        </button>
      )}
    </div>
  );
}
