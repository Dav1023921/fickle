import { createContext, useContext, useState } from 'react'

// a case can be staged or complete
export type CaseStatus = "staged" | "complete"

// a case will have an id, filename, imageUrl, status, file, result
export type Case = {
  id: string
  filename: string
  imageUrl: string
  status: CaseStatus
  file: File
  result?: any  
}

type CasesContextType = {
  cases: Case[]
  setCases: React.Dispatch<React.SetStateAction<Case[]>>
}

const CasesContext = createContext<CasesContextType | null>(null)

// the google doc
export const CasesProvider = ({ children }: { children: React.ReactNode }) => {
  const [cases, setCases] = useState<Case[]>([])
  return (
    <CasesContext.Provider value={{ cases, setCases }}>
      {children}
    </CasesContext.Provider>
  )
}

// opening the caes
export const useCases = () => {
  const ctx = useContext(CasesContext)
  if (!ctx) throw new Error("useCases must be used inside CasesProvider")
  return ctx
}