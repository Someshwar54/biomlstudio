'use client'

import { useState, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { geminiService } from '@/lib/geminiService'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
}

interface AIAssistantProps {
  analysisResults: any
  isAnalyzing: boolean
}

const AIAssistant: React.FC<AIAssistantProps> = ({ analysisResults, isAnalyzing }) => {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)

  // Reset chat when new analysis starts
  useEffect(() => {
    if (isAnalyzing) {
      setMessages([])
      setInputMessage('')
    }
  }, [isAnalyzing])

  const generateAIResponse = (question: string): string => {
    if (!analysisResults) {
      return "No analysis results available yet. Please run an analysis first."
    }

    const lowerQuestion = question.toLowerCase()
    
    // Gene discovery questions
    if (lowerQuestion.includes('gene') || lowerQuestion.includes('orf')) {
      const geneCount = analysisResults.gene_discovery?.potential_genes?.length || 0
      if (geneCount > 0) {
        return `Found ${geneCount} potential genes in your analysis. These sequences show coding potential and may represent protein-coding regions.`
      }
      return "No significant genes were discovered in this dataset. This could be due to short sequence lengths or non-coding regions."
    }

    // Drug target questions
    if (lowerQuestion.includes('drug') || lowerQuestion.includes('target')) {
      const drugCount = analysisResults.drug_targets?.druggable_proteins?.length || 0
      if (drugCount > 0) {
        return `Identified ${drugCount} potential drug targets. These proteins may be suitable for therapeutic intervention.`
      }
      return "No druggable targets were identified in this analysis. Consider analyzing longer protein-coding sequences."
    }

    // Pathogen questions
    if (lowerQuestion.includes('pathogen') || lowerQuestion.includes('bacteria') || lowerQuestion.includes('resistance')) {
      const resistanceCount = analysisResults.pathogen_detection?.resistance_genes?.length || 0
      if (resistanceCount > 0) {
        return `Found ${resistanceCount} potential resistance genes. This suggests possible antibiotic resistance patterns.`
      }
      return "No pathogenic signatures or resistance genes were detected in this dataset."
    }

    // Mutation questions
    if (lowerQuestion.includes('mutation') || lowerQuestion.includes('variant')) {
      const mutationCount = analysisResults.mutation_analysis?.statistics?.total_snvs || 0
      if (mutationCount > 0) {
        return `Detected ${mutationCount} sequence variants. These may include single nucleotide variations that could affect function.`
      }
      return "No significant mutations or variants were identified in this analysis."
    }

    // Summary questions
    if (lowerQuestion.includes('summary') || lowerQuestion.includes('overview') || lowerQuestion.includes('total')) {
      const summary = analysisResults.summary
      if (summary) {
        return `Analysis Summary: Processed ${summary.total_sequences} sequences (${summary.total_base_pairs?.toLocaleString()} base pairs). Analysis completed at ${new Date(summary.analysis_timestamp).toLocaleString()}.`
      }
    }

    // Default response
    return "I can help you understand your DNA analysis results. Ask me about genes, drug targets, pathogens, mutations, or request a summary of your analysis."
  }

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    }

    const question = inputMessage.trim()
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)

    try {
      // Use real Gemini AI service
      const aiResponseText = await geminiService.analyzeResults(question, analysisResults)
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: aiResponseText,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiResponse])
    } catch (error) {
      console.error('AI Response Error:', error)
      
      // Fallback to local response on error
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: generateAIResponse(question),
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aiResponse])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="bg-zinc-800 border border-zinc-600 rounded-lg p-4 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-zinc-700">
        <Bot className="w-5 h-5 text-blue-400" />
        <h3 className="text-white font-semibold">AI Assistant</h3>

      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {messages.length === 0 && !isAnalyzing && (
          <div className="text-zinc-400 text-sm text-center py-8">
            Ask me anything about your analysis results!
          </div>
        )}
        
        {messages.map((message) => (
          <div key={message.id} className={`flex gap-2 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-2 max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                message.type === 'user' ? 'bg-blue-600' : 'bg-zinc-600'
              }`}>
                {message.type === 'user' ? <User className="w-3 h-3 text-white" /> : <Bot className="w-3 h-3 text-white" />}
              </div>
              <div className={`rounded-lg p-3 ${
                message.type === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-zinc-700 text-zinc-100'
              }`}>
                <p className="text-sm">{message.content}</p>
              </div>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-zinc-600 flex items-center justify-center shrink-0">
              <Bot className="w-3 h-3 text-white" />
            </div>
            <div className="bg-zinc-700 rounded-lg p-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-75"></div>
                <div className="w-2 h-2 bg-zinc-400 rounded-full animate-bounce delay-150"></div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      {!isAnalyzing && (
        <div className="flex gap-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about your analysis results..."
            className="flex-1 bg-zinc-700 text-white placeholder-zinc-400 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-zinc-600 disabled:cursor-not-allowed text-white rounded-lg px-3 py-2 transition-colors"
            title="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {isAnalyzing && (
        <div className="text-zinc-400 text-sm text-center py-2">
          Analysis in progress...
        </div>
      )}
    </div>
  )
}

export default AIAssistant