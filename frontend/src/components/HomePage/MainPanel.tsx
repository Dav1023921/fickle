import { Box, Typography, Button, Table, TableHead, TableBody, TableRow, TableCell } from '@mui/material';
import UploadBar from './UploadBar';
import { theme } from '../../theme';
import { useCases, type Case, type CaseStatus } from '../../CasesContext';
import { useNavigate } from 'react-router-dom'

const MainPanel = () => {
    // from context provider
    const { cases, setCases } = useCases()
    // allow navigation function
    const navigate = useNavigate()

    const staged = cases.filter(c => c.status === "staged")
    const toReview = cases.filter(c => c.status === "complete")
    
    // adds files in 
    const handleFilesAdded = (files: FileList) => {
        const existingFilenames = cases.map(c => c.filename)
        const newCases: Case[] = Array.from(files)
            .filter(file => !existingFilenames.includes(file.name))
            .map(file => ({
                id: crypto.randomUUID(),
                filename: file.name,
                imageUrl: URL.createObjectURL(file),
                status: "staged" as const,
                file,
            }))
        setCases(prev => [...prev, ...newCases])
    }

    // for all the files in staged send an API request and then set the status to complete
    // store the output from API in result
    const handleRunAll = async () => {
        for (const c of staged) {
            const formData = new FormData()
            formData.append("file", c.file)
            try {
                const res = await fetch("http://localhost:8003/analyse", { method: "POST", body: formData })
                const result = await res.json()
                setCases(prev => prev.map(x => x.id === c.id ? { ...x, status: "complete" as CaseStatus, result } : x))
            } catch (err) {
                console.error("Failed to analyse", c.filename, err)
            }
        }
    }
    // create an upload bar
    return (
        <Box sx={{ width: '90%', bgcolor: theme.palette.background.default, display: 'flex', flexDirection: 'column' }}>
            
            <UploadBar onFilesAdded={handleFilesAdded} />

            <Box sx={{ backgroundColor: '#e0e0e0', borderRadius: 1, padding: 2, minHeight: 180, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <Typography>Selected Files</Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                    {staged.map(c => (
                        <Box key={c.id} sx={{ display: 'flex', alignItems: 'center', bgcolor: 'white', borderRadius: 1, padding: '4px 8px' }}>
                            <Typography variant="caption">{c.filename}</Typography>
                        </Box>
                    ))}
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                    <Button variant="contained" color="primary" disabled={staged.length === 0} onClick={handleRunAll}>Analyse All</Button>
                </Box>
            </Box>

            <Box sx={{ mt: 3 }}>
                <Table>
                    <TableHead sx={{ backgroundColor: '#f5f5f5' }}>
                        <TableRow>
                            <TableCell>Case Number</TableCell>
                            <TableCell>AI Diagnosis</TableCell>
                            <TableCell>Confidence</TableCell>
                            <TableCell>Reviewed</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {toReview.map((c, i) => (
                            <TableRow key={c.id} hover sx={{ cursor: 'pointer' }} onClick={() => navigate(`/cases/${c.id}`)}>
                                <TableCell>#{i + 1} {c.filename}</TableCell>
                                <TableCell>{c.result?.diagnostic ?? "-"}</TableCell>
                                <TableCell>-</TableCell>
                                <TableCell>NO</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </Box>

        </Box>
    )
}

export default MainPanel;