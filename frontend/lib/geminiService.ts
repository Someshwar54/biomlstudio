import { GoogleGenerativeAI } from '@google/generative-ai'

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.NEXT_PUBLIC_GEMINI_API_KEY || '')

export class GeminiAIService {
  private model: any

  constructor() {
    this.model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' })
  }

  async analyzeResults(question: string, analysisResults: any): Promise<string> {
    try {
      // Prepare context from analysis results
      const context = this.prepareAnalysisContext(analysisResults)
      
      const prompt = `
You are a bioinformatics expert AI assistant helping users understand their DNA analysis results. 
Provide clear, accurate, and scientific explanations based on the analysis data.

ANALYSIS CONTEXT:
${context}

USER QUESTION: ${question}

Please provide a helpful, scientific response based on the analysis data. If the analysis doesn't contain relevant information for the question, explain what the analysis did find and suggest related insights. Keep responses concise but informative (2-4 sentences).

Focus on:
- Scientific accuracy
- Practical implications
- Clinical relevance when appropriate
- Clear explanations for non-experts
`

      const result = await this.model.generateContent(prompt)
      const response = await result.response
      return response.text()

    } catch (error) {
      console.error('Gemini AI Error:', error)
      
      // Fallback to local analysis if API fails
      return this.getFallbackResponse(question, analysisResults)
    }
  }

  private prepareAnalysisContext(analysisResults: any): string {
    if (!analysisResults) {
      return "No analysis results available."
    }

    let context = ""

    // Summary information
    if (analysisResults.summary) {
      context += `DATASET SUMMARY:
- Total sequences: ${analysisResults.summary.total_sequences || 0}
- Total base pairs: ${analysisResults.summary.total_base_pairs || 0}
- Analysis timestamp: ${analysisResults.summary.analysis_timestamp || 'Not available'}
- Processing mode: ${analysisResults.summary.processing_mode || 'standard'}

`
    }

    // Gene discovery results
    if (analysisResults.gene_discovery) {
      const geneCount = analysisResults.gene_discovery.potential_genes?.length || 0
      context += `GENE DISCOVERY:
- Potential genes found: ${geneCount}
`
      if (geneCount > 0) {
        context += `- Gene details: ${JSON.stringify(analysisResults.gene_discovery.potential_genes.slice(0, 3))}
`
      }
    }

    // Drug targets
    if (analysisResults.drug_targets) {
      const drugCount = analysisResults.drug_targets.druggable_proteins?.length || 0
      context += `DRUG TARGETS:
- Druggable proteins: ${drugCount}
`
      if (drugCount > 0) {
        context += `- Target details: ${JSON.stringify(analysisResults.drug_targets.druggable_proteins.slice(0, 3))}
`
      }
    }

    // Pathogen detection
    if (analysisResults.pathogen_detection) {
      const resistanceCount = analysisResults.pathogen_detection.resistance_genes?.length || 0
      const pathogenCount = analysisResults.pathogen_detection.bacterial_signatures?.length || 0
      context += `PATHOGEN DETECTION:
- Resistance genes: ${resistanceCount}
- Bacterial signatures: ${pathogenCount}
`
    }

    // Mutation analysis
    if (analysisResults.mutation_analysis) {
      const stats = analysisResults.mutation_analysis.statistics || {}
      context += `MUTATION ANALYSIS:
- Total SNVs: ${stats.total_snvs || 0}
- Oncogenic sites: ${stats.oncogenic_sites || 0}
- Coding mutations: ${stats.coding_mutations || 0}
`
    }

    // Biomarkers
    if (analysisResults.biomarker_generation) {
      const biomarkerCount = analysisResults.biomarker_generation.diagnostic_signatures?.length || 0
      context += `BIOMARKERS:
- Diagnostic signatures: ${biomarkerCount}
`
    }

    // Motif analysis
    if (analysisResults.motif_analysis) {
      const motifCount = analysisResults.motif_analysis.regulatory_motifs?.length || 0
      context += `MOTIF ANALYSIS:
- Regulatory motifs: ${motifCount}
`
    }

    return context || "Analysis results are not available or empty."
  }

  private getFallbackResponse(question: string, analysisResults: any): string {
    const lowerQuestion = question.toLowerCase()
    
    if (!analysisResults) {
      return "No analysis results are available yet. Please run an analysis first to get insights about your DNA sequences."
    }

    // Gene-related questions
    if (lowerQuestion.includes('gene') || lowerQuestion.includes('orf')) {
      const geneCount = analysisResults.gene_discovery?.potential_genes?.length || 0
      if (geneCount > 0) {
        return `I found ${geneCount} potential genes in your analysis. These represent sequences with significant coding potential that may encode functional proteins.`
      }
      return "No significant genes were discovered in this dataset. This could be due to short sequence lengths, non-coding regions, or sequences that don't meet the minimum ORF criteria."
    }

    // Drug target questions
    if (lowerQuestion.includes('drug') || lowerQuestion.includes('target')) {
      const drugCount = analysisResults.drug_targets?.druggable_proteins?.length || 0
      if (drugCount > 0) {
        return `I identified ${drugCount} potential drug targets in your sequences. These proteins have structural features that make them suitable for therapeutic intervention.`
      }
      return "No druggable targets were identified in this analysis. Consider analyzing longer protein-coding sequences or sequences from known therapeutic target families."
    }

    // Pathogen questions
    if (lowerQuestion.includes('pathogen') || lowerQuestion.includes('bacteria') || lowerQuestion.includes('resistance')) {
      const resistanceCount = analysisResults.pathogen_detection?.resistance_genes?.length || 0
      if (resistanceCount > 0) {
        return `I detected ${resistanceCount} potential antibiotic resistance genes. This suggests the presence of genetic elements that could confer resistance to antimicrobial treatments.`
      }
      return "No pathogenic signatures or resistance genes were detected in this dataset. The sequences appear to lack known virulence or resistance markers."
    }

    // Mutation questions
    if (lowerQuestion.includes('mutation') || lowerQuestion.includes('variant') || lowerQuestion.includes('cancer')) {
      const mutationCount = analysisResults.mutation_analysis?.statistics?.total_snvs || 0
      const oncogenicCount = analysisResults.mutation_analysis?.statistics?.oncogenic_sites || 0
      if (mutationCount > 0) {
        return `I found ${mutationCount} sequence variants${oncogenicCount > 0 ? `, including ${oncogenicCount} potentially oncogenic sites` : ''}. These variations could affect protein function or regulation.`
      }
      return "No significant mutations or variants were identified in this analysis. The sequences appear to be relatively conserved."
    }

    // Summary questions
    if (lowerQuestion.includes('summary') || lowerQuestion.includes('overview')) {
      const summary = analysisResults.summary
      if (summary) {
        return `Your analysis processed ${summary.total_sequences} sequences totaling ${summary.total_base_pairs?.toLocaleString()} base pairs. The analysis completed successfully and examined multiple biological aspects including genes, drug targets, pathogens, and mutations.`
      }
    }

    // Default response
    return "I can help you understand your DNA analysis results. Ask me about specific findings like genes, drug targets, pathogens, mutations, or request a summary of the analysis."
  }
}

export const geminiService = new GeminiAIService()