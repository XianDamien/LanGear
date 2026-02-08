import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { RetroCard, RetroButton, ProgressBar } from '../components/Common';
import { Play, TrendingUp, Calendar, Award } from 'lucide-react';
import { Deck } from '../types';

interface DashboardProps {
    recentDecks: Deck[];
    onPlayDeck: (deckId: string) => void;
}

const data = [
  { name: '周一', sentences: 12 },
  { name: '周二', sentences: 18 },
  { name: '周三', sentences: 5 },
  { name: '周四', sentences: 25 },
  { name: '周五', sentences: 30 },
  { name: '周六', sentences: 45 },
  { name: '周日', sentences: 10 },
];

export const Dashboard: React.FC<DashboardProps> = ({ recentDecks, onPlayDeck }) => {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Top Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <RetroCard title="积分">
            <div className="flex items-center gap-3">
                <Award className="text-yellow-400" size={32} />
                <div>
                    <div className="text-3xl font-bold font-pixel text-brand-accent">1,240</div>
                    <div className="text-xs text-slate-500 uppercase">已获得积分</div>
                </div>
            </div>
        </RetroCard>
        
        <RetroCard title="待复习">
            <div className="flex flex-col gap-2">
                <div className="text-3xl font-bold text-brand-accent">
                  <span className="font-pixel">14</span> <span>张卡</span>
                </div>
                <RetroButton size="sm" variant="primary">全部复习</RetroButton>
            </div>
        </RetroCard>

        <RetroCard title="连续学习">
            <div className="flex items-center gap-3">
                <div className="text-4xl font-bold text-brand-accent font-pixel">5</div>
                <div className="flex flex-col">
                    <span className="font-bold">天</span>
                    <span className="text-xs text-green-500">目标达成 ✓</span>
                </div>
            </div>
        </RetroCard>

        <RetroCard title="今日目标">
             <p className="text-sm text-slate-500 mb-2">熟能生巧</p>
             <ProgressBar value={15} max={30} label="句子" />
        </RetroCard>
      </div>

      {/* Activity Chart */}
      <div className="bg-brand-panel border border-slate-200 p-4 shadow-mech">
          <h3 className="text-slate-500 uppercase mb-4 text-sm font-bold flex items-center gap-2">
            <TrendingUp size={16}/> 学习趋势
          </h3>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="colorSplit" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ff4d2d" stopOpacity={0.35}/>
                            <stop offset="95%" stopColor="#ff4d2d" stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey="name" tick={{fill: '#64748b', fontFamily: 'Source Sans 3'}} axisLine={false} tickLine={false} />
                    <YAxis hide />
                    <Tooltip 
                        contentStyle={{backgroundColor: '#ffffff', border: '1px solid #ff4d2d', fontFamily: 'Source Sans 3', color: '#0f172a'}}
                        itemStyle={{color: '#ff4d2d'}}
                    />
                    <Area type="monotone" dataKey="sentences" stroke="#ff4d2d" strokeWidth={3} fillOpacity={1} fill="url(#colorSplit)" />
                </AreaChart>
            </ResponsiveContainer>
          </div>
      </div>

      {/* Recent / Favorites */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
            <h2 className="text-2xl font-bold mb-4 uppercase text-brand-accent">学习中</h2>
            <div className="space-y-3">
                {recentDecks.map(deck => (
                    <div key={deck.id} className="bg-white p-4 border border-slate-200 hover:border-brand-accent cursor-pointer transition-colors flex justify-between items-center group" onClick={() => onPlayDeck(deck.id)}>
                        <div>
                            <div className="font-bold text-lg group-hover:text-brand-accent">{deck.name}</div>
                            <div className="text-sm text-slate-500">
                              <span className="font-pixel text-brand-accent">{deck.newCards}</span> 新卡 •{' '}
                              <span className="font-pixel text-brand-accent">{deck.reviewCards}</span> 复习
                            </div>
                        </div>
                        <Play className="text-slate-400 group-hover:text-brand-accent" fill="currentColor" />
                    </div>
                ))}
            </div>
        </div>
        
        <div>
            <h2 className="text-2xl font-bold mb-4 uppercase text-brand-accent">排行榜</h2>
            <div className="bg-white p-4 border border-slate-200 shadow-mech-sm">
                <div className="flex justify-between border-b border-slate-200 pb-2 mb-2">
                    <span><span className="font-pixel text-brand-accent">1</span>. Polyglot_99</span>
                    <span className="text-brand-accent"><span className="font-pixel">9950</span> 积分</span>
                </div>
                <div className="flex justify-between border-b border-slate-200 pb-2 mb-2 bg-red-50 px-2 -mx-2">
                    <span><span className="font-pixel text-brand-accent">2</span>. 你</span>
                    <span className="text-slate-900 font-bold"><span className="font-pixel text-brand-accent">1240</span> 积分</span>
                </div>
                <div className="flex justify-between text-slate-500">
                    <span><span className="font-pixel text-brand-accent">3</span>. Learner_X</span>
                    <span><span className="font-pixel text-brand-accent">800</span> 积分</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};
