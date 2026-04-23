'use client'

import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Scatter } from 'recharts'

interface BioVisualizationProps {
  data: any
  type: 'gene_discovery' | 'mutation_analysis' | 'drug_targets' | 'pathogen_detection' | 'motif_analysis' | 'biomarker_generation'
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff0000', '#00ffff', '#ff00ff']

const BioVisualization: React.FC<BioVisualizationProps> = ({ data, type }) => {
  const [visualizationData, setVisualizationData] = useState<any[]>([])

  useEffect(() => {
    if (!data) return

    let processedData: any[] = []

    switch (type) {
      case 'gene_discovery':
        processedData = processGeneDiscoveryData(data)
        break
      case 'mutation_analysis':
        processedData = processMutationData(data)
        break
      case 'drug_targets':
        processedData = processDrugTargetData(data)
        break
      case 'pathogen_detection':
        processedData = processPathogenData(data)
        break
      case 'motif_analysis':
        processedData = processMotifData(data)
        break
      case 'biomarker_generation':
        processedData = processBiomarkerData(data)
        break
    }

    setVisualizationData(processedData)
  }, [data, type])

  const processGeneDiscoveryData = (data: any) => {
    const potentialGenes = data.potential_genes || []
    
    // Group by coding potential ranges
    const ranges = [
      { range: '0.0-0.2', count: 0 },
      { range: '0.2-0.4', count: 0 },
      { range: '0.4-0.6', count: 0 },
      { range: '0.6-0.8', count: 0 },
      { range: '0.8-1.0', count: 0 }
    ]

    potentialGenes.forEach((gene: any) => {
      const potential = gene.coding_potential || 0
      if (potential <= 0.2) ranges[0].count++
      else if (potential <= 0.4) ranges[1].count++
      else if (potential <= 0.6) ranges[2].count++
      else if (potential <= 0.8) ranges[3].count++
      else ranges[4].count++
    })

    return ranges
  }

  const processMutationData = (data: any) => {
    return [
      { type: 'SNVs', count: data.statistics?.total_snvs || 0 },
      { type: 'Insertions', count: data.insertions?.length || 0 },
      { type: 'Deletions', count: data.deletions?.length || 0 },
      { type: 'Oncogenic', count: data.statistics?.oncogenic_sites || 0 }
    ]
  }

  const processDrugTargetData = (data: any) => {
    return [
      { category: 'Enzyme Sites', count: data.enzyme_sites?.length || 0 },
      { category: 'Binding Pockets', count: data.binding_pockets?.length || 0 },
      { category: 'Conserved Domains', count: data.conserved_domains?.length || 0 },
      { category: 'Druggable Proteins', count: data.druggable_proteins?.length || 0 }
    ]
  }

  const processPathogenData = (data: any) => {
    return [
      { pathogen: 'Bacterial', signatures: data.bacterial_signatures?.length || 0 },
      { pathogen: 'Viral', signatures: data.viral_signatures?.length || 0 },
      { pathogen: 'Resistance Genes', signatures: data.resistance_genes?.length || 0 },
      { pathogen: 'Virulence Factors', signatures: data.pathogenicity_factors?.length || 0 }
    ]
  }

  const processMotifData = (data: any) => {
    return [
      { motif: 'Promoters', count: data.promoters?.length || 0 },
      { motif: 'Enhancers', count: data.enhancers?.length || 0 },
      { motif: 'TF Binding Sites', count: data.tf_binding_sites?.length || 0 },
      { motif: 'CpG Islands', count: data.cpg_islands?.length || 0 },
      { motif: 'Splice Sites', count: data.splice_sites?.length || 0 }
    ]
  }

  const processBiomarkerData = (data: any) => {
    const discriminativeKmers = data.discriminative_kmers || []
    
    // Group by fold change
    const foldChangeRanges = [
      { range: '2-5x', count: 0 },
      { range: '5-10x', count: 0 },
      { range: '10-20x', count: 0 },
      { range: '>20x', count: 0 }
    ]

    discriminativeKmers.forEach((kmer: any) => {
      const foldChange = kmer.fold_change || 0
      if (foldChange < 5) foldChangeRanges[0].count++
      else if (foldChange < 10) foldChangeRanges[1].count++
      else if (foldChange < 20) foldChangeRanges[2].count++
      else foldChangeRanges[3].count++
    })

    return foldChangeRanges
  }

  const renderChart = () => {
    switch (type) {
      case 'gene_discovery':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={visualizationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        )
      
      case 'mutation_analysis':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={visualizationData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {visualizationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        )
      
      case 'drug_targets':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={visualizationData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="category" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="count" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        )
      
      case 'pathogen_detection':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={visualizationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="pathogen" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="signatures" fill="#ff7300" />
            </BarChart>
          </ResponsiveContainer>
        )
      
      case 'motif_analysis':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={visualizationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="motif" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#00ff00" />
            </BarChart>
          </ResponsiveContainer>
        )
      
      case 'biomarker_generation':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={visualizationData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#ff00ff" />
            </BarChart>
          </ResponsiveContainer>
        )
      
      default:
        return <div className="text-center text-gray-500 py-8">No visualization available</div>
    }
  }

  if (!visualizationData.length) {
    return <div className="text-center text-gray-500 py-8">No data to display</div>
  }

  return (
    <div className="w-full">
      {renderChart()}
    </div>
  )
}

export default BioVisualization