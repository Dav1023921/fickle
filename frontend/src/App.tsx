import './App.css'
import Panel from "./components/DiagnosisPanel";
import Navbar from './components/Navbar';
import Viewer from './components/ImageViewer'

function App() {
  return (
    <>
      <Navbar />
      <div style={{ display: "flex", flexDirection: "row" , gap: "50px",
          margin: "50px",}}>
        <Viewer />
        <Panel />
        
      </div>
    </>
  )
}

export default App
