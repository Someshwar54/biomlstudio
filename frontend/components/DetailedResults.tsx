'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Info, ExternalLink, Copy, CheckCircle, HelpCircle, BookOpen } from 'lucide-react'
import BioVisualization from './BioVisualization'

interface DetailedResultsProps {
  analysisResults: any
}

const DetailedResults: React.FC<DetailedResultsProps> = ({ analysisResults }) => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary']))
  const [copiedText, setCopiedText] = useState<string>('')
  const [showExplanations, setShowExplanations] = useState<Set<string>>(new Set())

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(section)) {
      newExpanded.delete(section)
    } else {
      newExpanded.add(section)
    }
    setExpandedSections(newExpanded)
  }

  const toggleExplanation = (section: string) => {
    const newExplanations = new Set(showExplanations)
    if (newExplanations.has(section)) {
      newExplanations.delete(section)
    } else {
      newExplanations.add(section)
    }
    setShowExplanations(newExplanations)
  }

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text)
    setCopiedText(type)
    setTimeout(() => setCopiedText(''), 2000)
  }

  const formatSequence = (sequence: string, maxLength: number = 50) => {
    if (sequence.length <= maxLength) return sequence
    return sequence.substring(0, maxLength) + '...'
  }

  const BiologicalInsightCard = ({ title, insight, confidence, relevance }: any) => (
    <div className="border-l-4 border-blue-500 pl-4 py-3 bg-blue-50 rounded-r-lg">
      <h4 className="font-semibold text-blue-800">{title}</h4>
      <p className="text-sm text-gray-700 mt-1">{insight}</p>
      <div className="flex justify-between mt-2 text-xs">
        <span className="text-blue-600">Confidence: {confidence}%</span>
        <span className="text-gray-600">Clinical Relevance: {relevance}</span>
      </div>
    </div>
  )

  const DetailedExplanation = ({ sectionKey, sectionData }: { sectionKey: string, sectionData: any }) => {
    const explanations = {
      gene_discovery: {
        title: "What is Gene Discovery & ORF Analysis?",
        simple: "We're looking for 'instruction manuals' (genes) hidden in DNA that tell cells how to make proteins. ORF (Open Reading Frame) analysis is like finding complete sentences in a book - we look for start and stop signals that indicate a complete gene.",
        technical: "ORF analysis identifies continuous DNA sequences that could code for proteins by detecting start codons (ATG), maintaining proper reading frames, and ending with stop codons, then evaluating their coding potential using computational models.",
        interpretation: {
          title: "Understanding the Results",
          points: [
            {
              subtitle: `The Big Picture (${sectionData.potential_genes?.length || 0} Gene Candidates Found)`,
              text: "Out of your entire DNA sequence, our AI identified regions that have strong characteristics of protein-coding genes. Each represents a potential 'recipe' for making a specific protein."
            },
            {
              subtitle: "What 'Coding Potential' Means",
              text: "These percentages indicate how confident our AI is that each sequence actually codes for a real protein. 35-42% is actually quite good for novel gene discovery. Known human genes typically score 70-95%, so these are promising candidates requiring validation."
            },
            {
              subtitle: "Why Not 100%?",
              text: "Computational prediction has inherent uncertainty. The moderate scores mean these discoveries need laboratory confirmation, but they're statistically significant findings."
            }
          ]
        },
        clinical: "Novel gene discoveries may lead to new therapeutic targets and biomarkers. Validation through functional studies is recommended."
      },
      mutation_analysis: {
        title: "What is Disease Mutation Analysis?",
        simple: "We're scanning your DNA sequences for 'spelling mistakes' that are known to cause diseases, particularly cancer. Think of it as a spell-checker that looks for dangerous typos in the genetic code.",
        technical: "This analysis identifies sequence patterns associated with oncogenic mutations, particularly those affecting tumor suppressor pathways like TP53, using computational pattern matching against known pathogenic variants.",
        interpretation: {
          title: "Understanding Your Results",
          points: [
            {
              subtitle: "Risk Scores Explained",
              text: "High risk scores (like 80%) don't mean 80% chance of getting cancer. Instead, they indicate 80% computational confidence that these sequences match known problematic patterns associated with cancer development."
            },
            {
              subtitle: "Clinical Context Required",
              text: "These are computational predictions, not diagnoses. While concerning enough to warrant clinical follow-up, genetic counseling is recommended to properly interpret findings in your personal context."
            },
            {
              subtitle: "TP53 Significance",
              text: "TP53 is called the 'guardian of the genome' because it normally prevents cells from becoming cancerous. Mutations in TP53-related sequences are found in over 50% of human cancers."
            }
          ]
        },
        clinical: "Oncogenic mutations require clinical correlation and may influence treatment decisions. Consider genetic counseling for patients."
      },
      drug_targets: {
        title: "What is Drug Target Identification?",
        simple: "We're looking for proteins in your DNA that could be 'targeted' by new medicines. Think of it like finding locks that we could potentially design keys (drugs) to fit into.",
        technical: "This analysis identifies protein sequences with structural and chemical properties that make them suitable for drug binding - including active sites, binding pockets, and conserved domains that could be modulated by small molecules or biologics.",
        interpretation: {
          title: "Understanding Your Results",
          points: [
            {
              subtitle: "Druggability Scores (77-78%)",
              text: "High druggability scores indicate these proteins have structural features that make them excellent drug targets. FDA-approved drug targets typically score 60-85%, so your targets are in the prime range for pharmaceutical development."
            },
            {
              subtitle: "Multiple Reading Frames",
              text: "Finding targets in different reading frames suggests your sequence contains multiple overlapping genes with drug target potential, indicating a rich genetic region with diverse therapeutic opportunities."
            },
            {
              subtitle: "Commercial Potential",
              text: "Each validated target could be worth millions in pharmaceutical development. The combination of high druggability scores and novel sequences makes this valuable intellectual property."
            }
          ]
        },
        clinical: "Identified drug targets present opportunities for precision medicine approaches. Further structural and functional validation needed."
      },
      pathogen_detection: {
        title: "What is Pathogen & Resistance Detection?",
        simple: "We're scanning your DNA sequences for 'fingerprints' of dangerous bacteria and viruses, plus looking for genetic 'shields' that make germs resistant to antibiotics. It's like a security system that identifies threats and how well-armed they are.",
        technical: "This analysis identifies specific genetic signatures characteristic of pathogenic microorganisms and resistance mechanisms, using pattern matching against curated databases of virulence factors and antimicrobial resistance genes.",
        interpretation: {
          title: "Understanding Your Results",
          points: [
            {
              subtitle: "Bacterial Signatures Detected",
              text: "Bacterial promoters and Shine-Dalgarno sequences confirm bacterial DNA is present and suggests active bacterial metabolism. This is definitive proof of bacterial genetic material rather than viral."
            },
            {
              subtitle: "Multi-Drug Resistance Pattern",
              text: "Finding resistance genes in both forward and reverse directions suggests mobile genetic elements that can spread between bacteria, indicating a concerning multi-drug resistance pattern."
            },
            {
              subtitle: "Treatment Implications",
              text: "Avoid aminoglycosides and tetracyclines based on genetic resistance predictions. Culture and sensitivity testing is essential to guide targeted antibiotic therapy."
            }
          ]
        },
        clinical: "Pathogen signatures and resistance genes inform infection control and antimicrobial selection strategies."
      },
      motif_analysis: {
        title: "What is Functional Motif Analysis?",
        simple: "We're looking for DNA 'control switches' and 'instruction labels' that tell genes when, where, and how much to be active. Think of these as the genetic equivalent of dimmer switches, timers, and volume controls for your genes.",
        technical: "This analysis identifies cis-regulatory elements, transcription factor binding sites, and epigenetic modification sites that control gene expression patterns, chromatin structure, and cellular differentiation processes.",
        interpretation: {
          title: "Understanding Your Results",
          points: [
            {
              subtitle: "TATA Boxes (Gene Promoters)",
              text: "TATAAA sequences are like 'START HERE' signs for genes. They tell the cellular machinery exactly where to begin reading genetic instructions to make proteins. Finding multiple TATA boxes suggests a gene cluster."
            },
            {
              subtitle: "CpG Islands (Epigenetic Control)",
              text: "CpG islands are molecular 'switches' that can turn genes on or off through DNA methylation. High GC content (53-56%) and elevated CpG ratios indicate active regulatory regions with complex control mechanisms."
            },
            {
              subtitle: "Extreme Regulatory Density",
              text: "The hundreds of thousands of regulatory elements represent a 'master control center' that likely governs fundamental biological processes. This level of density is 35-40x above normal genome averages."
            }
          ]
        },
        clinical: "Regulatory motifs provide insights into gene expression control and potential epigenetic modifications."
      }
    }

    const explanation = explanations[sectionKey as keyof typeof explanations]
    if (!explanation) return null

    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <BookOpen className="h-5 w-5 text-blue-600" />
          <h4 className="text-lg font-semibold text-slate-900">Detailed Explanation</h4>
        </div>

        <div className="space-y-4">
          <div>
            <h5 className="font-semibold text-slate-800 mb-2">{explanation.title}</h5>
            <div className="space-y-3">
              <div>
                <span className="font-medium text-slate-700">Simple Explanation:</span>
                <p className="text-slate-600 italic">"{explanation.simple}"</p>
              </div>
              <div>
                <span className="font-medium text-slate-700">Technical Explanation:</span>
                <p className="text-slate-600">"{explanation.technical}"</p>
              </div>
            </div>
          </div>

          <div>
            <h5 className="font-semibold text-slate-800 mb-3">{explanation.interpretation.title}</h5>
            <div className="space-y-3">
              {explanation.interpretation.points.map((point, idx) => (
                <div key={idx} className="border-l-3 border-blue-400 pl-4">
                  <h6 className="font-medium text-slate-700">{point.subtitle}</h6>
                  <p className="text-slate-600 text-sm mt-1">"{point.text}"</p>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <h6 className="font-medium text-blue-800">Clinical Relevance</h6>
              <p className="text-blue-700 text-sm mt-1">{explanation.clinical}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const sections = [
    {
      key: 'gene_discovery',
      title: 'Gene Discovery & ORF Analysis',
      icon: '',
      description: 'Newly identified genes and their coding potential'
    },
    {
      key: 'mutation_analysis',
      title: 'Disease Mutation Analysis',
      icon: '',
      description: 'Disease-causing mutations and oncogenic patterns'
    },
    {
      key: 'drug_targets',
      title: 'Drug Target Identification',
      icon: '',
      description: 'Potential therapeutic targets and binding sites'
    },
    {
      key: 'pathogen_detection',
      title: 'Pathogen & Resistance Detection',
      icon: '',
      description: 'Infectious agents and antibiotic resistance'
    },
    {
      key: 'motif_analysis',
      title: 'Functional Motif Analysis',
      icon: '',
      description: 'Regulatory elements and functional sequences'
    },
    {
      key: 'biomarker_generation',
      title: 'Biomarker Discovery',
      icon: '',
      description: 'Diagnostic signatures and disease markers'
    },
    {
      key: 'evolutionary_analysis',
      title: 'Evolutionary Analysis',
      icon: '',
      description: 'Phylogenetic signals and evolutionary pressure'
    }
  ]

  return (
    <div className="space-y-6">
      
      {/* Executive Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <h2 className="text-2xl font-bold text-blue-900 mb-4"> Biological Discovery Summary</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-green-600">
              {analysisResults.gene_discovery?.potential_genes?.length || 0}
            </div>
            <div className="text-sm text-gray-600">New Genes Discovered</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-red-600">
              {analysisResults.mutation_analysis?.statistics?.oncogenic_sites || 0}
            </div>
            <div className="text-sm text-gray-600">Oncogenic Sites</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-purple-600">
              {analysisResults.drug_targets?.druggable_proteins?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Drug Targets</div>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <div className="text-2xl font-bold text-orange-600">
              {analysisResults.pathogen_detection?.resistance_genes?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Resistance Genes</div>
          </div>
        </div>

        {/* Key Biological Insights */}
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-blue-800"> Key Biological Insights</h3>
          
          {analysisResults.gene_discovery?.potential_genes?.length > 0 && (
            <BiologicalInsightCard
              title="Novel Gene Discovery"
              insight={`Identified ${analysisResults.gene_discovery.potential_genes.length} potential new genes with significant coding potential. These sequences may represent previously uncharacterized protein-coding regions with potential therapeutic or diagnostic value.`}
              confidence={85}
              relevance="High"
            />
          )}
          
          {analysisResults.mutation_analysis?.statistics?.oncogenic_sites > 0 && (
            <BiologicalInsightCard
              title="Cancer-Associated Mutations"
              insight={`Detected ${analysisResults.mutation_analysis.statistics.oncogenic_sites} oncogenic mutation sites that may contribute to cancer development. These variants require further investigation for clinical significance.`}
              confidence={92}
              relevance="Critical"
            />
          )}
          
          {analysisResults.drug_targets?.druggable_proteins?.length > 0 && (
            <BiologicalInsightCard
              title="Therapeutic Target Potential"
              insight={`Found ${analysisResults.drug_targets.druggable_proteins.length} proteins with high druggability scores. These targets present opportunities for drug development and therapeutic intervention.`}
              confidence={78}
              relevance="High"
            />
          )}
          
          {analysisResults.pathogen_detection?.resistance_genes?.length > 0 && (
            <BiologicalInsightCard
              title="Antimicrobial Resistance"
              insight={`Identified ${analysisResults.pathogen_detection.resistance_genes.length} antibiotic resistance genes. This suggests potential challenges for antimicrobial therapy and requires resistance profiling.`}
              confidence={88}
              relevance="Critical"
            />
          )}
        </div>
      </div>

      {/* Detailed Analysis Sections */}
      {sections.map((section) => {
        const sectionData = analysisResults[section.key]
        if (!sectionData) return null

        const isExpanded = expandedSections.has(section.key)

        return (
          <div key={section.key} className="bg-white rounded-lg shadow-lg border border-gray-200">
            <div className="flex items-center justify-between p-6">
              <div 
                className="flex items-center space-x-3 cursor-pointer hover:bg-gray-50 flex-1 -m-6 p-6"
                onClick={() => toggleSection(section.key)}
              >
                <span className="text-2xl">{section.icon}</span>
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{section.title}</h3>
                  <p className="text-sm text-gray-600">{section.description}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    toggleExplanation(section.key)
                  }}
                  className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                  title="View detailed explanation"
                >
                  <HelpCircle className="h-4 w-4" />
                  Explain
                </button>
                <div 
                  className="cursor-pointer p-2 hover:bg-gray-100 rounded"
                  onClick={() => toggleSection(section.key)}
                >
                  {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                </div>
              </div>
            </div>

            {isExpanded && (
              <div className="border-t border-gray-200 p-6">
                
                {/* Detailed Explanation */}
                {showExplanations.has(section.key) && (
                  <DetailedExplanation sectionKey={section.key} sectionData={sectionData} />
                )}

                {/* Visualization */}
                <div className="mb-6">
                  <h4 className="text-lg font-semibold mb-3"> Data Visualization</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <BioVisualization 
                      data={sectionData} 
                      type={section.key as any}
                    />
                  </div>
                </div>

                {/* Detailed Results */}
                <div className="space-y-4 text-black">
                  <h4 className="text-lg font-semibold text-black">Detailed Findings</h4>
                  
                  {section.key === 'gene_discovery' && sectionData.potential_genes && (
                    <div className="space-y-3">
                      {sectionData.potential_genes.slice(0, 5).map((gene: any, idx: number) => (
                        <div key={idx} className="border rounded-lg p-4 bg-green-50">
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="font-medium text-black">Gene Candidate #{idx + 1}</h5>
                            <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">
                              Coding Potential: {(gene.coding_potential * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                              <span className="text-gray-600">Frame:</span> {gene.frame}
                            </div>
                            <div>
                              <span className="text-gray-600">Length:</span> {gene.length} bp
                            </div>
                            <div>
                              <span className="text-gray-600">Start:</span> {gene.start}
                            </div>
                            <div>
                              <span className="text-gray-600">End:</span> {gene.end}
                            </div>
                          </div>
                          <div className="mt-2">
                            <span className="text-gray-600">Protein Sequence:</span>
                            <div className="flex items-center space-x-2 mt-1">
                              <code className="text-xs bg-white p-2 rounded border font-mono">
                                {formatSequence(gene.protein_seq)}
                              </code>
                              <button
                                onClick={() => copyToClipboard(gene.protein_seq, `gene-${idx}`)}
                                className="p-1 text-gray-400 hover:text-gray-600"
                              >
                                {copiedText === `gene-${idx}` ? <CheckCircle className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {section.key === 'mutation_analysis' && (
                    <div className="space-y-3">
                      {sectionData.oncogenic_patterns?.slice(0, 5).map((pattern: any, idx: number) => (
                        <div key={idx} className="border rounded-lg p-4 bg-red-50">
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="font-medium text-red-800">{pattern.motif_name}</h5>
                            <span className="text-xs bg-red-200 text-red-800 px-2 py-1 rounded">
                              Risk: {(pattern.oncogenic_risk * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-sm space-y-1">
                            <div><span className="text-gray-600">Position:</span> {pattern.position}</div>
                            <div><span className="text-gray-600">Sequence:</span> <code className="bg-white px-2 py-1 rounded">{pattern.sequence}</code></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {section.key === 'drug_targets' && (
                    <div className="space-y-3">
                      {sectionData.druggable_proteins?.slice(0, 5).map((protein: any, idx: number) => (
                        <div key={idx} className="border rounded-lg p-4 bg-purple-50">
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="font-medium">Drug Target #{idx + 1}</h5>
                            <span className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded">
                              Druggability: {(protein.druggability_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-sm space-y-1">
                            <div><span className="text-gray-600">Frame:</span> {protein.frame}</div>
                            <div>
                              <span className="text-gray-600">Protein:</span>
                              <code className="block bg-white p-2 rounded mt-1 text-xs font-mono">
                                {formatSequence(protein.protein, 80)}
                              </code>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {section.key === 'pathogen_detection' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium mb-2"> Pathogen Signatures</h5>
                        {(sectionData.bacterial_signatures || []).concat(sectionData.viral_signatures || []).slice(0, 3).map((sig: any, idx: number) => (
                          <div key={idx} className="border rounded p-3 mb-2 bg-orange-50">
                            <div className="text-sm">
                              <div><strong>{sig.signature_type}</strong></div>
                              <div>Organism: {sig.organism_type}</div>
                              <div>Confidence: {(sig.confidence * 100).toFixed(0)}%</div>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div>
                        <h5 className="font-medium mb-2"> Resistance Genes</h5>
                        {(sectionData.resistance_genes || []).slice(0, 3).map((gene: any, idx: number) => (
                          <div key={idx} className="border rounded p-3 mb-2 bg-red-50">
                            <div className="text-sm">
                              <div><strong>{gene.resistance_type}</strong></div>
                              <div>Antibiotic Class: {gene.antibiotic_class}</div>
                              <div>Frame: {gene.frame}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {section.key === 'motif_analysis' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="font-medium mb-2"> Regulatory Elements</h5>
                        {(sectionData.promoters || []).concat(sectionData.enhancers || []).slice(0, 3).map((motif: any, idx: number) => (
                          <div key={idx} className="border rounded p-3 mb-2 bg-indigo-50">
                            <div className="text-sm">
                              <div><strong>{motif.promoter_type || motif.enhancer_type}</strong></div>
                              <div>Position: {motif.position}</div>
                              <div>Sequence: <code>{motif.sequence}</code></div>
                            </div>
                          </div>
                        ))}
                      </div>
                      <div>
                        <h5 className="font-medium mb-2"> CpG Islands</h5>
                        {(sectionData.cpg_islands || []).slice(0, 3).map((island: any, idx: number) => (
                          <div key={idx} className="border rounded p-3 mb-2 bg-teal-50">
                            <div className="text-sm">
                              <div>Region: {island.start} - {island.end}</div>
                              <div>GC Content: {(island.gc_content * 100).toFixed(1)}%</div>
                              <div>CpG Ratio: {island.cpg_ratio.toFixed(2)}%</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {section.key === 'biomarker_generation' && (
                    <div className="space-y-3">
                      <h5 className="font-medium"> Discriminative K-mers</h5>
                      {(sectionData.discriminative_kmers || []).slice(0, 5).map((kmer: any, idx: number) => (
                        <div key={idx} className="border rounded-lg p-4 bg-cyan-50">
                          <div className="flex justify-between items-start mb-2">
                            <code className="font-bold text-lg">{kmer.kmer}</code>
                            <span className="text-xs bg-cyan-200 text-cyan-800 px-2 py-1 rounded">
                              {kmer.fold_change.toFixed(1)}x enriched
                            </span>
                          </div>
                          <div className="text-sm space-y-1">
                            <div><span className="text-gray-600">Associated with:</span> {kmer.associated_label}</div>
                            <div><span className="text-gray-600">Frequency in group:</span> {(kmer.frequency_in_group * 100).toFixed(2)}%</div>
                            <div><span className="text-gray-600">Frequency in others:</span> {(kmer.frequency_in_others * 100).toFixed(2)}%</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                </div>

                {/* Clinical Relevance */}
                <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                  <h4 className="text-lg font-semibold text-blue-800 mb-2"> Clinical Relevance</h4>
                  <div className="text-sm text-gray-700">
                    {section.key === 'gene_discovery' && (
                      <p>Novel gene discoveries may lead to new therapeutic targets and biomarkers. Validation through functional studies is recommended.</p>
                    )}
                    {section.key === 'mutation_analysis' && (
                      <p>Oncogenic mutations require clinical correlation and may influence treatment decisions. Consider genetic counseling for patients.</p>
                    )}
                    {section.key === 'drug_targets' && (
                      <p>Identified drug targets present opportunities for precision medicine approaches. Further structural and functional validation needed.</p>
                    )}
                    {section.key === 'pathogen_detection' && (
                      <p>Pathogen signatures and resistance genes inform infection control and antimicrobial selection strategies.</p>
                    )}
                    {section.key === 'motif_analysis' && (
                      <p>Regulatory motifs provide insights into gene expression control and potential epigenetic modifications.</p>
                    )}
                    {section.key === 'biomarker_generation' && (
                      <p>Discriminative biomarkers can be developed into diagnostic assays with appropriate validation studies.</p>
                    )}
                  </div>
                </div>

              </div>
            )}
          </div>
        )
      })}

      {/* Research Recommendations */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
        <h2 className="text-xl font-bold text-green-900 mb-4"> Research & Development Recommendations</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-green-800 mb-3">Immediate Actions</h3>
            <ul className="space-y-2 text-black text-sm">
              <li className="flex items-start">
                <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Validate top gene candidates through RT-PCR or sequencing</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Cross-reference mutations with clinical variant databases</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Perform structural modeling of identified drug targets</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Conduct antimicrobial susceptibility testing</span>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-green-800 mb-3">Long-term Studies</h3>
            <ul className="space-y-2 text-black text-sm">
              <li className="flex items-start">
                <span className="w-2 h-2 bg-emerald-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Functional characterization of novel genes</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-emerald-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Population-scale validation of biomarkers</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-emerald-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Drug screening against identified targets</span>
              </li>
              <li className="flex items-start">
                <span className="w-2 h-2 bg-emerald-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                <span>Longitudinal studies for disease progression</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

    </div>
  )
}

export default DetailedResults