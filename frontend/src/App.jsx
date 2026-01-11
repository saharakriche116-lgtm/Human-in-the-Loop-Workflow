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
    setFormData(doc.ai_extraction || {});
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
      alert("✅ Document validé !");
      setCurrentDoc(null);
      fetchDocuments();
    } catch (error) {
      console.error("Erreur validation", error);
    }
  };

  const handleRetrain = async () => {
    if (!confirm("Voulez-vous lancer l'entraînement ?")) return;
    try {
        alert("Entraînement en cours...");
        const res = await axios.post(`${API_URL}/retrain`);
        alert(res.data.message);
    } catch (err) {
        alert("Erreur entraînement");
    }
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);
    try {
        await axios.post(`${API_URL}/upload`, formData);
        fetchDocuments();
    } catch (error) {
        console.error("Erreur upload", error);
    }
  };

  return (
    // CONTENEUR PRINCIPAL (Plein écran forcé)
    <div style={{ 
        width: '100vw', 
        height: '100vh', 
        maxWidth: 'none', 
        margin: 0, 
        padding: 0, 
        display: 'flex', 
        flexDirection: 'column', 
        fontFamily: 'Arial, sans-serif', 
        overflow: 'hidden',
        backgroundColor: '#1a1a1a', 
        color: 'white'
    }}>
      
      {/* HEADER */}
      <div style={{ 
          padding: '15px 20px', 
          backgroundColor: '#2b2b2b', 
          borderBottom: '1px solid #444', 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          flexShrink: 0 
      }}>
        <h1 style={{ margin: 0, fontSize: '1.2rem' }}>Human-in-the-Loop Workflow</h1>
        <button 
            onClick={handleRetrain} 
            style={{ backgroundColor: '#646cff', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
        >
            🧠 Ré-entraîner l'IA
        </button>
      </div>
      
      {/* CONTENU PRINCIPAL */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', width: '100%' }}>
        
        {/* --- CAS 1 : ACCUEIL --- */}
        {!currentDoc && (
            <div style={{ padding: '40px', width: '100%', overflowY: 'auto' }}>
                <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                    <div style={{ marginBottom: '30px', padding: '20px', border: '2px dashed #555', borderRadius: '10px', textAlign: 'center' }}>
                        <h3>📂 Ingérer un nouveau document</h3>
                        <input type="file" onChange={handleUpload} style={{ marginTop: '10px' }} />
                    </div>
                    
                    <h3>Documents en attente ({documents.length})</h3>
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                    {documents.map(doc => (
                        <li key={doc.id} style={{ padding: '15px', borderBottom: '1px solid #444', display: 'flex', justifyContent: 'space-between' }}>
                            <span>Document #{doc.id} ({doc.filename}) - <span style={{color: doc.status === 'validated' ? '#4ade80' : '#fbbf24'}}>{doc.status}</span></span>
                            {doc.status !== 'validated' && (
                                <button onClick={() => startCorrection(doc)} style={{ marginLeft: '10px', cursor: 'pointer', padding: '5px 10px' }}>
                                Corriger
                                </button>
                            )}
                        </li>
                    ))}
                    </ul>
                </div>
            </div>
        )}

        {/* --- CAS 2 : MODE CORRECTION (50% / 50%) --- */}
        {currentDoc && (
            <>
                {/* PARTIE GAUCHE : PDF 
                   - flex: 1 assure qu'il prend 50% de l'espace
                   - padding: 0 pour coller aux bords
                */}
                <div style={{ flex: 1, borderRight: '1px solid #444', height: '100%', padding: 0, overflow: 'hidden' }}>
                    <iframe 
                        // AJOUT DE #view=FitH ICI : Cela force le PDF à prendre toute la largeur
                        src={`${API_URL}/uploads/${currentDoc.filename}#view=FitH`} 
                        width="100%" 
                        height="100%" 
                        style={{ border: 'none', display: 'block' }} 
                        title="PDF Viewer"
                    />
                </div>

                {/* PARTIE DROITE : CHAMPS */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: '#222' }}>
                    
                    <div style={{ padding: '20px', borderBottom: '1px solid #444' }}>
                        <h2 style={{ margin: 0, fontSize: '1.2rem' }}>Extraction & Validation</h2>
                        <p style={{ color: '#aaa', margin: '5px 0 0 0', fontSize: '0.9rem' }}>Fichier : {currentDoc.filename}</p>
                    </div>

                    <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
                        {Object.keys(formData).length === 0 && (
                            <p style={{color: '#ef4444'}}>⚠️ Aucune donnée détectée.</p>
                        )}

                        {Object.keys(formData).map((key) => {
                            // Liste des champs qui nécessitent une grande zone de texte
                            const isLongText = ['skills', 'education', 'summary', 'experience'].includes(key);
                            
                            return (
                                <div key={key} style={{ marginBottom: '20px' }}>
                                    <label style={{ display: 'block', marginBottom: '8px', color: '#ddd', fontWeight: 'bold', textTransform: 'uppercase', fontSize: '0.85rem' }}>
                                        {key.replace('_', ' ')}
                                    </label>
                                    
                                    {isLongText ? (
                                        <textarea
                                            name={key}
                                            value={formData[key]}
                                            onChange={handleChange}
                                            rows={4} // Hauteur ajustée
                                            style={{ 
                                                width: '100%', 
                                                padding: '10px', 
                                                borderRadius: '5px', 
                                                border: '1px solid #555', 
                                                background: '#333', 
                                                color: 'white', 
                                                fontFamily: 'monospace',
                                                resize: 'vertical'
                                            }}
                                        />
                                    ) : (
                                        <input 
                                            type="text" 
                                            name={key} 
                                            value={formData[key]} 
                                            onChange={handleChange}
                                            style={{ 
                                                width: '100%', 
                                                padding: '10px', 
                                                borderRadius: '5px', 
                                                border: '1px solid #555', 
                                                background: '#333', 
                                                color: 'white' 
                                            }}
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    <div style={{ padding: '20px', borderTop: '1px solid #444', display: 'flex', gap: '10px' }}>
                        <button 
                            onClick={handleSubmit}
                            style={{ flex: 2, background: '#16a34a', color: 'white', padding: '12px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontWeight: 'bold', fontSize: '1rem' }}
                        >
                            Valider & Enregistrer
                        </button>
                        <button 
                            onClick={() => setCurrentDoc(null)}
                            style={{ flex: 1, background: '#4b5563', color: 'white', padding: '12px', border: 'none', borderRadius: '5px', cursor: 'pointer', fontSize: '1rem' }}
                        >
                            Annuler
                        </button>
                    </div>
                </div>
            </>
        )}
      </div>
    </div>
  )
}

export default App