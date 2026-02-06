import React, { useState } from 'react';
import { HashRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { BookOpen, Home, Upload, Settings, Menu, X, Plus } from 'lucide-react';
import { RetroButton, LanguageSelector, RetroCard } from './components/Common';
import { Dashboard } from './features/Dashboard';
import { StudySession } from './features/StudySession';
import { Deck, Card } from './types';
import { segmentText } from './services/geminiService';

// Mock Data
const MOCK_DECKS: Deck[] = [
    { id: '1', name: '新概念英语 2', description: '经典教材', totalCards: 96, newCards: 5, reviewCards: 12, type: 'folder' },
    { id: '2', name: '雅思听力 第1章', description: '剑桥雅思', totalCards: 40, newCards: 10, reviewCards: 0, type: 'deck' },
];

const MOCK_CARDS: Card[] = [
    { 
        id: 'c1', 
        backText: "The quick brown fox jumps over the lazy dog.", 
        backTranslation: "这只敏捷的棕色狐狸跳过了懒惰的狗。",
        difficulty: 1,
        grammarInfo: { nouns: ['fox', 'dog'], verbs: ['jumps'] } 
    },
    { 
        id: 'c2', 
        backText: "Learning a language requires patience and practice.", 
        backTranslation: "学习语言需要耐心和练习。",
        difficulty: 2,
        grammarInfo: { nouns: ['language', 'patience', 'practice'], verbs: ['requires', 'learning'] } 
    }
];

// --- Internal Components for Library & Import to save file count ---

const Library: React.FC<{ onSelectDeck: (id: string) => void }> = ({ onSelectDeck }) => {
    return (
        <div className="animate-fadeIn">
            <h2 className="text-3xl font-bold mb-6 text-brand-accent uppercase">题库</h2>
            <div className="grid grid-cols-1 gap-4">
                {MOCK_DECKS.map(deck => (
                    <RetroCard key={deck.id} className="cursor-pointer hover:border-brand-accent" title={deck.type === 'folder' ? '文件夹' : '卡组'}>
                        <div onClick={() => onSelectDeck(deck.id)} className="flex justify-between items-center">
                            <div>
                                <h3 className="text-xl font-bold">{deck.name}</h3>
                                <p className="text-slate-500 text-sm">{deck.description}</p>
                            </div>
                            <RetroButton size="sm" variant="secondary">打开</RetroButton>
                        </div>
                    </RetroCard>
                ))}
            </div>
        </div>
    );
};

const ImportPage: React.FC = () => {
    const [text, setText] = useState("");
    const [segments, setSegments] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleAnalyze = async () => {
        setIsLoading(true);
        const result = await segmentText(text);
        setSegments(result.segments);
        setIsLoading(false);
    };

    return (
        <div className="animate-fadeIn max-w-2xl mx-auto">
            <h2 className="text-3xl font-bold mb-6 text-brand-accent uppercase">导入卡组</h2>
            <RetroCard title="素材来源">
                <textarea 
                    className="w-full bg-white border border-slate-200 p-4 text-slate-900 font-sans h-40 focus:border-brand-accent outline-none resize-none"
                    placeholder="在这里粘贴文本（如新闻、字幕文件等）..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />
                <div className="mt-4 flex justify-between items-center">
                    <label className="flex items-center gap-2 cursor-pointer bg-white px-3 py-2 border border-slate-200 hover:border-brand-accent">
                        <Upload size={16} />
                        <span className="text-sm">上传音频（可选）</span>
                        <input type="file" className="hidden" accept="audio/*" />
                    </label>
                    <RetroButton onClick={handleAnalyze} disabled={isLoading}>
                        {isLoading ? "AI 处理中..." : "AI 分句"}
                    </RetroButton>
                </div>
            </RetroCard>

            {segments.length > 0 && (
                <div className="mt-8 space-y-4">
                    <h3 className="text-xl uppercase border-b border-slate-200 pb-2">卡片预览</h3>
                    {segments.map((seg, idx) => (
                        <div key={idx} className="bg-white p-3 border border-slate-200 flex gap-2">
                             <div className="text-brand-accent w-6 font-pixel">{idx + 1}.</div>
                             <input className="bg-transparent w-full outline-none text-slate-900" defaultValue={seg} />
                        </div>
                    ))}
                    <RetroButton variant="primary" className="w-full mt-4">生成卡组</RetroButton>
                </div>
            )}
        </div>
    );
};

// --- Main App Layout & Logic ---

const App: React.FC = () => {
  const [langPair, setLangPair] = useState("en-zh");
  const [activeDeck, setActiveDeck] = useState<string | null>(null);

  // In a real app, useLocation would be inside Router context, so we wrap content
  return (
    <HashRouter>
        <MainLayout 
            langPair={langPair} 
            setLangPair={setLangPair} 
            activeDeck={activeDeck} 
            setActiveDeck={setActiveDeck} 
        />
    </HashRouter>
  );
};

const MainLayout: React.FC<any> = ({ langPair, setLangPair, activeDeck, setActiveDeck }) => {
    const location = useLocation();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // If studying, show study interface full screen
    if (activeDeck) {
        return (
            <div className="min-h-screen bg-brand-dark text-slate-900">
                <StudySession 
                    deckName={MOCK_DECKS.find(d => d.id === activeDeck)?.name || "卡组"} 
                    cards={MOCK_CARDS} 
                    onComplete={() => setActiveDeck(null)}
                    onExit={() => setActiveDeck(null)}
                />
            </div>
        );
    }

    const NavItem = ({ to, icon: Icon, label }: any) => {
        const isActive = location.pathname === to;
        const iconClass = isActive ? 'text-brand-accent' : 'text-slate-400 group-hover:text-brand-accent';
        const labelClass = isActive ? 'text-slate-900' : 'text-slate-600 group-hover:text-slate-900';
        return (
            <Link to={to} onClick={() => setMobileMenuOpen(false)}>
                <div className={`group flex items-center gap-3 px-4 py-3 mb-2 transition-all cursor-pointer border-l-4 ${isActive ? 'bg-red-50 border-brand-accent' : 'border-transparent hover:bg-slate-50'}`}>
                    <Icon size={24} className={iconClass} />
                    <span className={`uppercase tracking-widest text-lg ${labelClass}`}>{label}</span>
                </div>
            </Link>
        );
    };

    return (
        <div className="min-h-screen bg-brand-dark text-slate-900 flex">
            {/* Sidebar (Desktop) */}
            <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-brand-panel border-r border-slate-200 transform transition-transform duration-300 md:relative md:translate-x-0 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`}>
                <div className="p-6 border-b border-slate-200 bg-white">
                    <h1 className="text-3xl font-bold text-brand-accent tracking-tighter flex items-center gap-2">
                        <div className="relative w-8 h-8 flex items-center justify-center">
                            <Settings className="animate-spin-slow w-8 h-8 text-brand-accent" strokeWidth={2.5} />
                        </div>
                        <span>Lan<span className="text-slate-900">Gear</span></span>
                    </h1>
                </div>
                
                <nav className="mt-8">
                    <NavItem to="/" icon={Home} label="总览" />
                    <NavItem to="/library" icon={BookOpen} label="题库" />
                    <NavItem to="/import" icon={Upload} label="导入" />
                    <NavItem to="/settings" icon={Settings} label="设置" />
                </nav>

                <div className="absolute bottom-8 left-0 w-full px-6">
                    <RetroButton variant="primary" className="w-full" size="sm">
                        开通专业版
                    </RetroButton>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="h-20 border-b border-slate-200 bg-brand-panel flex items-center justify-between px-6 sticky top-0 z-40 shadow-mech-sm">
                    <button className="md:hidden text-slate-900" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                        {mobileMenuOpen ? <X /> : <Menu />}
                    </button>
                    
                    <div className="hidden md:block text-slate-500 uppercase text-sm">
                        流利学习引擎
                    </div>

                    <div className="flex items-center gap-4">
                        <LanguageSelector currentPair={langPair} onChange={setLangPair} />
                        <RetroButton variant="secondary" size="sm" icon={Plus} />
                    </div>
                </header>

                {/* Content Area */}
                <div className="flex-1 p-6 overflow-y-auto">
                    <Routes>
                        <Route path="/" element={<Dashboard recentDecks={MOCK_DECKS} onPlayDeck={setActiveDeck} />} />
                        <Route path="/library" element={<Library onSelectDeck={setActiveDeck} />} />
                        <Route path="/import" element={<ImportPage />} />
                        <Route path="/settings" element={<div className="p-10 text-center text-slate-500">设置功能占位</div>} />
                    </Routes>
                </div>
            </main>

            {/* Overlay for mobile sidebar */}
            {mobileMenuOpen && (
                <div className="fixed inset-0 bg-black bg-opacity-70 z-40 md:hidden" onClick={() => setMobileMenuOpen(false)}></div>
            )}
        </div>
    );
};

export default App;
