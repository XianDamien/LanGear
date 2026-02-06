import React from 'react';
import { LucideIcon } from 'lucide-react';

interface RetroButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: LucideIcon;
}

export const RetroButton: React.FC<RetroButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'md',
  icon: Icon,
  className = '',
  ...props 
}) => {
  const baseStyle = "font-sans uppercase tracking-wide border-2 transition-all active:translate-y-1 active:shadow-none flex items-center justify-center gap-2";
  
  const variants = {
    primary: "bg-brand-accent border-brand-accent-hover text-white font-bold shadow-mech hover:bg-brand-accent-hover",
    secondary: "bg-brand-light border-slate-200 text-slate-700 shadow-mech hover:border-slate-300",
    danger: "bg-brand-alert border-red-600 text-white shadow-mech hover:bg-red-500",
    ghost: "bg-transparent border-transparent text-slate-500 hover:text-slate-900 shadow-none border-0"
  };

  const sizes = {
    sm: "px-2 py-1 text-sm",
    md: "px-4 py-2 text-lg",
    lg: "px-6 py-3 text-xl font-bold"
  };

  return (
    <button 
      className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`} 
      {...props}
    >
      {Icon && <Icon size={size === 'sm' ? 16 : 20} />}
      {children}
    </button>
  );
};

export const RetroCard: React.FC<{ children: React.ReactNode; className?: string; title?: string }> = ({ 
  children, 
  className = '',
  title
}) => {
  return (
    <div className={`bg-brand-panel border border-slate-200 p-4 shadow-mech relative ${className}`}>
        {title && (
            <div className="absolute -top-4 left-4 bg-white px-2 text-brand-accent font-bold uppercase tracking-wider text-sm border border-slate-200 flex items-center gap-1 shadow-mech-sm">
                {title}
            </div>
        )}
      {children}
    </div>
  );
};

export const ProgressBar: React.FC<{ value: number; max: number; label?: string }> = ({ value, max, label }) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-1 uppercase text-slate-500">
        <span>{label}</span>
        <span className="font-pixel text-brand-accent">{value} / {max}</span>
      </div>
      <div className="h-4 bg-slate-100 border border-slate-200 relative">
        <div 
          className="h-full transition-all duration-300 relative overflow-hidden"
          style={{ 
            width: `${percentage}%`,
            backgroundImage: 'linear-gradient(90deg, #ff4d2d 0%, #ff7a45 100%)'
          }}
        >
            {/* Striped pattern for industrial look */}
            <div className="absolute inset-0 w-full h-full" style={{ backgroundImage: 'linear-gradient(45deg,rgba(255,255,255,.25) 25%,transparent 25%,transparent 50%,rgba(255,255,255,.25) 50%,rgba(255,255,255,.25) 75%,transparent 75%,transparent)', backgroundSize: '1rem 1rem' }}></div>
        </div>
      </div>
    </div>
  );
};

export const LanguageSelector: React.FC<{
    currentPair: string;
    onChange: (pair: string) => void;
}> = ({ currentPair, onChange }) => {
    return (
        <div className="flex items-center gap-2 bg-brand-light text-slate-800 px-2 py-1 border border-slate-200 shadow-mech-sm">
            <span className="text-xl">🇺🇸/🇨🇳</span>
            <select 
                value={currentPair}
                onChange={(e) => onChange(e.target.value)}
                className="bg-transparent font-bold outline-none font-sans text-lg uppercase cursor-pointer"
            >
                <option value="en-zh">英语 ➜ 中文</option>
                <option value="fr-zh">法语 ➜ 中文</option>
                <option value="jp-zh">日语 ➜ 中文</option>
            </select>
        </div>
    )
}
