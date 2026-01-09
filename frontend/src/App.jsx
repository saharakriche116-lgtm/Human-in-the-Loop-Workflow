import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = "http://localhost:8000";

function App() {
  const [documents, setDocuments] = useState([]);
  const [currentDoc, setCurrentDoc] = useState(null);
  const [formData, setFormData] = useState({});
  const [startTime, setStartTime] = useState(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${API_URL}/documents`);
      setDocuments(res.data);
    } catch (error) {
      console.error("Erreur chargement documents", error);
    }
  };

  const startCorrection = (doc) => {
    setCurrentDoc(doc);
    setFormData(doc.ai_extraction);
    setStartTime(Date.now());
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async () => {
    const timeTaken = Math.round((Date.now() - startTime) / 1000);
    
    try {
      await axios.post(`${API_URL}/validate`, {
        document_id: currentDoc.id,
        corrected_data: formData,
        time_taken: timeTaken
      });
      
      alert("Document validé !");
      setCurrentDoc(null);
      fetchDocuments();
    } catch (error) {
      console.error("Erreur validation", error);
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    await axios.post(`${API_URL}/upload`, formData);
    fetchDocuments();
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>Human-in-the-Loop Workflow</h1>
      
      <div style={{ marginBottom: '20px', padding: '10px', border: '1px dashed grey' }}>
        <h3>1. Ingérer un nouveau document</h3>
        <input type="file" onChange={handleUpload} />
      </div>

      {!currentDoc && (
        <div>
          <h3>Documents en attente ({documents.length})</h3>
          <ul>
            {documents.map(doc => (
              <li key={doc.id}>
                Document #{doc.id} ({doc.filename}) 
                <button onClick={() => startCorrection(doc)} style={{marginLeft: '10px'}}>
                  Corriger
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {currentDoc && (
        <div style={{ display: 'flex', height: '80vh', border: '1px solid #ccc' }}>
          
          <div style={{ flex: 1, background: '#f0f0f0', padding: '20px', textAlign: 'center' }}>
            <h2>Document Original</h2>
            <div style={{background: 'white', height: '90%', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
               <p>[ Aperçu du PDF: {currentDoc.filename} ]</p>
            </div>
          </div>

          <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
            <h2>Extraction & Validation</h2>
            <p style={{color: 'grey'}}>Vérifiez les suggestions de l'IA :</p>
            
            {Object.keys(formData).map((key) => (
              <div key={key} style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', fontWeight: 'bold' }}>{key}</label>
                <input 
                  type="text" 
                  name={key} 
                  value={formData[key]} 
                  onChange={handleChange}
                  style={{ width: '100%', padding: '8px' }}
                />
              </div>
            ))}

            <div style={{ marginTop: '30px' }}>
              <button 
                onClick={handleSubmit}
                style={{ background: 'green', color: 'white', padding: '10px 20px', border: 'none', cursor: 'pointer' }}
              >
                Valider & Enregistrer (Dataset)
              </button>
              <button 
                onClick={() => setCurrentDoc(null)}
                style={{ marginLeft: '10px', padding: '10px' }}
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
