import React, { useState } from "react";

function App() {
  const [file, setFile] = useState(null);

  const handleUpload = (e) => {
    setFile(e.target.files[0]);
  };

  const handleTest = () => {
    if (file) {
      alert(`File uploaded: ${file.name}`);
    } else {
      alert("No file selected");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>AI Wound Healing Monitor - React Test</h2>
      <input type="file" onChange={handleUpload} />
      <button onClick={handleTest} style={{ marginLeft: "10px" }}>Test Upload</button>
    </div>
  );
}

export default App;
