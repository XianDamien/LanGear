import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mic, Play, Volume2, Square } from 'lucide-react';
import { RetroButton, RetroCard } from '../components/Common';
import { Card, FSRSGrade } from '../types';
import { explainText, analyzePronunciation } from '../services/geminiService';

interface StudySessionProps {
  deckName: string;
  cards: Card[];
  onComplete: () => void;
  onExit: () => void;
}

// Helper to simulate text analysis highlighting
const renderHighlightedText = (text: string, nouns: string[] = [], verbs: string[] = []) => {
  const parts = text.split(' ');
  return parts.map((word, i) => {
    const cleanWord = word.replace(/[.,!?]/g, '');
    let className = "";
    if (nouns.includes(cleanWord.toLowerCase())) className = "noun-highlight";
    else if (verbs.includes(cleanWord.toLowerCase())) className = "verb-highlight";

    return (
      <span key={i} className={`${className} mr-2 inline-block cursor-help hover:scale-105 transition-transform`} title="点击查看 AI 解析">
        {word}
      </span>
    );
  });
};

type StudyStore = {
  notesByCard: Record<string, string>;
  feedbackByCard: Record<string, string>;
  translationByCard: Record<string, string>;
  summaryByDeck?: string | null;
};

const getStorageKey = (deckName: string) => `langear.study.${deckName}`;

const createEmptyStore = (): StudyStore => ({
  notesByCard: {},
  feedbackByCard: {},
  translationByCard: {},
  summaryByDeck: null,
});

const normalizeStore = (raw: Partial<StudyStore> | null): StudyStore => {
  if (!raw) return createEmptyStore();
  return {
    notesByCard: raw.notesByCard || {},
    feedbackByCard: raw.feedbackByCard || {},
    translationByCard: raw.translationByCard || {},
    summaryByDeck: raw.summaryByDeck ?? null,
  };
};

const loadStore = (deckName: string): StudyStore => {
  if (typeof window === 'undefined') return createEmptyStore();
  const key = getStorageKey(deckName);
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return createEmptyStore();
    return normalizeStore(JSON.parse(raw));
  } catch {
    return createEmptyStore();
  }
};

const saveStore = (deckName: string, updater: (prev: StudyStore) => StudyStore): StudyStore => {
  if (typeof window === 'undefined') return createEmptyStore();
  const key = getStorageKey(deckName);
  const next = updater(loadStore(deckName));
  localStorage.setItem(key, JSON.stringify(next));
  return next;
};

export const StudySession: React.FC<StudySessionProps> = ({ deckName, cards, onComplete, onExit }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [userTranscript, setUserTranscript] = useState("");
  const [liveTranscript, setLiveTranscript] = useState("");
  const [aiFeedback, setAiFeedback] = useState<string | null>(null);
  const [isFeedbackLoading, setIsFeedbackLoading] = useState(false);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<string>("");
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const [userAudioUrl, setUserAudioUrl] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [translationText, setTranslationText] = useState<string | null>(null);
  const [showTranslation, setShowTranslation] = useState(false);
  const [isTranslationLoading, setIsTranslationLoading] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [summaryText, setSummaryText] = useState<string | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  const currentCard = cards[currentIndex];
  
  // Refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const asrIntervalRef = useRef<number | null>(null);
  const liveTranscriptRef = useRef("");

  useEffect(() => {
    liveTranscriptRef.current = liveTranscript;
  }, [liveTranscript]);

  const stopAsrStream = useCallback(() => {
    if (asrIntervalRef.current) {
      window.clearInterval(asrIntervalRef.current);
      asrIntervalRef.current = null;
    }
  }, []);

  const startAsrStream = useCallback(() => {
    stopAsrStream();
    setLiveTranscript("");
    const words = currentCard.backText.split(' ');
    let idx = 0;
    asrIntervalRef.current = window.setInterval(() => {
      idx = Math.min(words.length, idx + 1);
      setLiveTranscript(words.slice(0, idx).join(' '));
      if (idx >= words.length) stopAsrStream();
    }, 400);
  }, [currentCard.backText, stopAsrStream]);

  // Simulate Audio Playback
  const playAudio = useCallback(() => {
    setAudioPlaying(true);
    // In a real app, this would play `currentCard.frontAudio`
    // Using SpeechSynthesis for demo
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(currentCard.backText); // Playing target language
    utterance.lang = "en-US"; // Assuming English learning for demo
    utterance.rate = 0.9;
    
    utterance.onend = () => {
      setAudioPlaying(false);
    };
    window.speechSynthesis.speak(utterance);
  }, [currentCard.backText]);

  useEffect(() => {
    // Auto play on new card
    playAudio();
    setIsFlipped(false);
    setUserTranscript("");
    setLiveTranscript("");
    setAiFeedback(null);
    setIsFeedbackLoading(false);
    setRecordingBlob(null);
    setIsRecording(false);
    setTranslationText(null);
    setShowTranslation(false);
    setIsTranslationLoading(false);
    setUserAudioUrl(prev => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
    stopAsrStream();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentIndex, playAudio, stopAsrStream]);

  useEffect(() => {
    if (!currentCard) return;
    const store = loadStore(deckName);
    setNotes(store.notesByCard[currentCard.id] ?? "");
    const storedFeedback = store.feedbackByCard[currentCard.id] ?? null;
    setAiFeedback(storedFeedback);
    const storedTranslation = store.translationByCard[currentCard.id] ?? null;
    setTranslationText(storedTranslation);
    setShowTranslation(!!storedTranslation);
    setSummaryText(store.summaryByDeck ?? null);
  }, [deckName, currentCard.id]);

  useEffect(() => {
    return () => {
      stopAsrStream();
      mediaStreamRef.current?.getTracks().forEach(track => track.stop());
    };
  }, [stopAsrStream]);

  const toggleRecording = async () => {
    if (isRecording) {
      // Stop
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      stopAsrStream();
    } else {
      // Start
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStreamRef.current = stream;
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        chunksRef.current = [];

        mediaRecorder.ondataavailable = (e) => {
          chunksRef.current.push(e.data);
        };

        mediaRecorder.onstop = () => {
          const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
          setRecordingBlob(blob);
          const url = URL.createObjectURL(blob);
          setUserAudioUrl(prev => {
            if (prev) URL.revokeObjectURL(prev);
            return url;
          });
          const transcript = liveTranscriptRef.current.trim();
          setUserTranscript(transcript || "（未识别到内容）");
          mediaStreamRef.current?.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        setIsRecording(true);
        setUserTranscript("");
        startAsrStream();
      } catch (err) {
        alert("麦克风权限被拒绝");
      }
    }
  };

  const handleFlip = async () => {
    setIsFlipped(true);
    if (!recordingBlob) {
      if (!aiFeedback) setAiFeedback("暂无录音，无法生成反馈。");
      return;
    }
    setIsFeedbackLoading(true);
    setAiFeedback(null);
    const feedback = await analyzePronunciation(currentCard.backText, userTranscript);
    setAiFeedback(feedback);
    setIsFeedbackLoading(false);
    saveStore(deckName, prev => ({
      ...prev,
      feedbackByCard: { ...prev.feedbackByCard, [currentCard.id]: feedback }
    }));
  };

  const handleGrade = (grade: FSRSGrade) => {
    // Logic to save grade would go here
    if (currentIndex < cards.length - 1) {
      setCurrentIndex(prev => prev + 1);
    } else {
      setIsSummaryOpen(true);
    }
  };

  const handleWordClick = async (word: string) => {
    setSelectedWord(word);
    setExplanation("正在加载 AI 解析...");
    const exp = await explainText(word, currentCard.backText);
    setExplanation(exp);
  };

  const handleNotesChange = (value: string) => {
    setNotes(value);
    saveStore(deckName, prev => ({
      ...prev,
      notesByCard: { ...prev.notesByCard, [currentCard.id]: value }
    }));
  };

  const handleShowTranslation = () => {
    setShowTranslation(true);
    if (translationText) return;
    setIsTranslationLoading(true);
    window.setTimeout(() => {
      const text = currentCard.backTranslation || "（AI 翻译示例）";
      setTranslationText(text);
      setIsTranslationLoading(false);
      saveStore(deckName, prev => ({
        ...prev,
        translationByCard: { ...prev.translationByCard, [currentCard.id]: text }
      }));
    }, 1000);
  };

  const handleSummary = () => {
    setIsSummaryLoading(true);
    setSummaryText(null);
    window.setTimeout(() => {
      const text = "本课已完成。建议重点关注发音连读与动词时态变化，并回听不顺畅的句子。";
      setSummaryText(text);
      setIsSummaryLoading(false);
      saveStore(deckName, prev => ({
        ...prev,
        summaryByDeck: text
      }));
    }, 1200);
  };

  const exitSummary = () => {
    setIsSummaryOpen(false);
    onComplete();
  };

  return (
    <div className="max-w-4xl mx-auto p-4 flex flex-col h-[85vh]">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <RetroButton variant="ghost" onClick={onExit} size="sm">退出</RetroButton>
        <div className="text-xl text-brand-accent font-bold uppercase">
          {deckName}{' '}
          <span className="font-pixel">{currentIndex + 1}</span>
          /
          <span className="font-pixel">{cards.length}</span>
        </div>
        <div className="w-10"></div>
      </div>

      {/* Main Card Area */}
      <div className="flex-1 relative perspective-1000">
        <RetroCard className="h-full flex flex-col justify-center items-center text-center p-8 transition-all duration-500">
          
          {/* Front Content (Audio/Hidden) */}
          <div className="mb-8">
            <div className={`p-4 rounded-full border-4 ${audioPlaying ? 'border-brand-accent animate-pulse' : 'border-slate-300'} inline-flex items-center justify-center w-24 h-24 mb-4 cursor-pointer hover:bg-slate-50`} onClick={playAudio}>
              {audioPlaying ? <Volume2 size={40} className="text-brand-accent" /> : <Play size={40} />}
            </div>
            <p className="text-slate-500 text-sm uppercase tracking-widest">听读跟读</p>
          </div>

          {/* User Interaction Area */}
          {!isFlipped ? (
            <div className="w-full max-w-md space-y-6">
                
               {/* Simulated Stream Transcript */}
               <div className="min-h-[60px] text-brand-accent font-sans text-lg border-b border-slate-200 pb-2">
                 {isRecording ? (liveTranscript || "...") : (userTranscript || "...")}
               </div>
               <div className="flex items-center justify-between text-xs uppercase text-slate-500">
                 <span>ASR 实时反馈</span>
               </div>

               <div className="flex justify-center gap-4">
                  <RetroButton 
                    variant={isRecording ? "danger" : "secondary"} 
                    onClick={toggleRecording}
                    className="w-full"
                  >
                    {isRecording ? <Square className="mr-2 animate-pulse"/> : <Mic className="mr-2"/>}
                    {isRecording ? "停止" : "录音"}
                  </RetroButton>
               </div>

               <RetroButton variant="primary" className="w-full mt-4" onClick={handleFlip} disabled={isRecording}>
                 翻面复盘
               </RetroButton>
            </div>
          ) : (
            // Back Content (Review)
            <div className="w-full text-left space-y-6 animate-fadeIn">
              
              {/* Target Text with NLP Highlighting */}
              <div className="bg-slate-50 p-6 border-l-4 border-brand-accent">
                <h2 className="text-3xl mb-2 tracking-wide" onClick={(e: any) => handleWordClick(e.target.innerText)}>
                    {renderHighlightedText(currentCard.backText, currentCard.grammarInfo?.nouns, currentCard.grammarInfo?.verbs)}
                </h2>
                <div className="mt-3">
                  {!showTranslation ? (
                    <RetroButton variant="secondary" size="sm" onClick={handleShowTranslation}>
                      显示中文翻译
                    </RetroButton>
                  ) : (
                    <p className="text-slate-500 italic text-lg">
                      {isTranslationLoading ? "AI 翻译生成中..." : (translationText || "暂无翻译")}
                    </p>
                  )}
                </div>
              </div>

              {/* Feedback Section */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-3 rounded text-sm border border-slate-200">
                      <h3 className="text-slate-500 uppercase text-xs mb-2">音频对比</h3>
                      <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                              <RetroButton variant="secondary" size="sm" onClick={playAudio}>
                                原音频
                              </RetroButton>
                              {userAudioUrl ? (
                                <audio controls src={userAudioUrl} className="h-8 w-full" />
                              ) : (
                                <span className="text-slate-500 text-xs">暂无录音</span>
                              )}
                          </div>
                          <div className="text-brand-accent font-sans">{userTranscript || "暂无转写"}</div>
                      </div>
                  </div>
                  <div className="bg-white p-3 rounded text-sm relative border border-slate-200">
                      <h3 className="text-slate-500 uppercase text-xs mb-1">AI 反馈</h3>
                      {isFeedbackLoading ? (
                          <span className="animate-pulse text-slate-500">分析中...</span>
                      ) : aiFeedback ? (
                          <p className="text-slate-900">{aiFeedback}</p>
                      ) : (
                          <span className="text-slate-500">暂无反馈</span>
                      )}
                  </div>
              </div>

              <div className="bg-white p-3 rounded text-sm border border-slate-200">
                  <h3 className="text-slate-500 uppercase text-xs mb-2">笔记</h3>
                  <textarea
                      className="w-full border border-slate-200 p-2 text-slate-900 font-sans text-sm resize-none"
                      placeholder="记录易错点或理解要点..."
                      value={notes}
                      onChange={(e) => handleNotesChange(e.target.value)}
                      rows={3}
                  />
              </div>

              {/* FSRS Grading */}
              <div className="grid grid-cols-4 gap-2 mt-8">
                <RetroButton variant="danger" size="sm" onClick={() => handleGrade(FSRSGrade.Again)}>
                    <div className="flex flex-col"><span>再来</span><span className="text-xs opacity-70 font-pixel text-brand-accent">1m</span></div>
                </RetroButton>
                <RetroButton variant="secondary" size="sm" onClick={() => handleGrade(FSRSGrade.Hard)}>
                    <div className="flex flex-col"><span>困难</span><span className="text-xs opacity-70 font-pixel text-brand-accent">6m</span></div>
                </RetroButton>
                <RetroButton variant="primary" size="sm" onClick={() => handleGrade(FSRSGrade.Good)}>
                    <div className="flex flex-col"><span>良好</span><span className="text-xs opacity-70 font-pixel text-brand-accent">10m</span></div>
                </RetroButton>
                <RetroButton variant="ghost" className="bg-blue-600 text-white hover:bg-blue-500" size="sm" onClick={() => handleGrade(FSRSGrade.Easy)}>
                    <div className="flex flex-col"><span>轻松</span><span className="text-xs opacity-70 font-pixel text-brand-accent">4d</span></div>
                </RetroButton>
              </div>
            </div>
          )}

        </RetroCard>

        {/* Floating Explanation Modal */}
        {selectedWord && (
            <div className="absolute bottom-4 right-4 z-50 w-64">
                <RetroCard className="bg-white border-brand-accent" title="AI 解析">
                    <div className="flex justify-between items-start mb-2">
                        <span className="font-bold text-brand-accent text-xl">{selectedWord}</span>
                        <button onClick={() => setSelectedWord(null)} className="text-slate-400 hover:text-slate-900">x</button>
                    </div>
                    <p className="text-sm leading-relaxed">{explanation}</p>
                </RetroCard>
            </div>
        )}

        {isSummaryOpen && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 z-50">
                <RetroCard className="bg-white border-brand-accent w-full max-w-lg">
                    <h3 className="text-xl font-bold text-brand-accent mb-2">本课完成</h3>
                    <p className="text-slate-600 text-sm mb-4">是否生成本课的复述总结报告？</p>
                    {isSummaryLoading && <p className="text-slate-500 text-sm animate-pulse">AI 总结生成中...</p>}
                    {summaryText && <p className="text-slate-900 text-sm mb-4">{summaryText}</p>}
                    <div className="flex gap-2 justify-end">
                        {!summaryText && (
                          <RetroButton variant="primary" size="sm" onClick={handleSummary} disabled={isSummaryLoading}>
                              生成总结
                          </RetroButton>
                        )}
                        <RetroButton variant="secondary" size="sm" onClick={exitSummary}>
                            返回
                        </RetroButton>
                    </div>
                </RetroCard>
            </div>
        )}
      </div>
    </div>
  );
};
