import { GoogleGenAI, Type } from "@google/genai";

const getAIClient = () => {
  if (!process.env.API_KEY) {
    console.warn("API_KEY not set.");
    return null;
  }
  return new GoogleGenAI({ apiKey: process.env.API_KEY });
};

export const explainText = async (text: string, context: string): Promise<string> => {
  const ai = getAIClient();
  if (!ai) return "AI Service Unavailable (Missing Key)";

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: `Explain the phrase or word "${text}" in the context of the sentence: "${context}". Keep it concise and helpful for a language learner.`,
      config: {
        systemInstruction: "You are a helpful language tutor.",
      }
    });
    return response.text || "No explanation available.";
  } catch (error) {
    console.error("Gemini Explain Error:", error);
    return "Error fetching explanation.";
  }
};

export const analyzePronunciation = async (originalText: string, userTranscript: string): Promise<string> => {
  const ai = getAIClient();
  if (!ai) return "AI Service Unavailable";

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: `Original Text: "${originalText}"\nUser Said (Transcript): "${userTranscript}"\n\nCompare the two. Point out any missing words or likely pronunciation errors based on the transcript difference. Be encouraging but precise.`,
    });
    return response.text || "Analysis complete.";
  } catch (error) {
    console.error("Gemini Analysis Error:", error);
    return "Could not analyze pronunciation.";
  }
};

export const segmentText = async (rawText: string): Promise<{segments: string[]}> => {
  const ai = getAIClient();
  if (!ai) return { segments: rawText.split('\n') };

  try {
      const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: `Split the following text into logical sentences or phrases suitable for language learning flashcards. Return a JSON array of strings.\n\nText: ${rawText}`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
            type: Type.OBJECT,
            properties: {
                segments: {
                    type: Type.ARRAY,
                    items: { type: Type.STRING }
                }
            }
        }
      }
    });
    
    if (response.text) {
        return JSON.parse(response.text);
    }
    return { segments: [] };
  } catch (error) {
      console.error("Segmentation error", error);
      return { segments: rawText.split('. ') };
  }
}