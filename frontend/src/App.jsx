import React, { useState, useEffect } from "react";

function App() {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadResponse, setUploadResponse] = useState(null);
  const [tasks, setTasks] = useState([]);

  const handleFileChange = (e) => {
    setSelectedFiles(e.target.files);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      alert("Please select files to upload");
      return;
    }
    const formData = new FormData();
    for (let file of selectedFiles) {
      formData.append("audioFiles", file);
    }
    try {
      const response = await fetch("http://localhost:3001/upload", {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      setUploadResponse(data);
      fetchTasks(); // Refresh tasks after upload
    } catch (error) {
      console.error("Error uploading files:", error);
      alert("Upload failed");
    }
  };

  const fetchTasks = async () => {
    try {
      const response = await fetch("http://localhost:3001/tasks");
      const data = await response.json();
      setTasks(data.tasks);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      alert("Failed to fetch tasks");
    }
  };

  useEffect(() => {
    // Automatically refresh tasks every 10 seconds
    const interval = setInterval(fetchTasks, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleProofread = async (filename) => {
    try {
      const response = await fetch(
        "http://localhost:3001/proofread?filename=" +
          encodeURIComponent(filename)
      );
      const data = await response.json();
      // Update the specific task with the proofread result
      setTasks((prevTasks) =>
        prevTasks.map((task) =>
          task.filename === filename
            ? { ...task, proofread: data.proofread }
            : task
        )
      );
    } catch (error) {
      console.error("Error proofreading:", error);
      alert("Proofreading failed");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white p-4">
        <h1 className="text-xl font-bold text-center">
          Podcast Transcription System
        </h1>
      </header>
      <main className="p-4">
        <section className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Upload Audio Files</h2>
          <input
            type="file"
            multiple
            className="border p-2 mb-2"
            onChange={handleFileChange}
          />
          <button
            className="bg-green-500 text-white p-2 rounded mr-2"
            onClick={handleUpload}
          >
            Upload
          </button>
          <button
            className="bg-blue-500 text-white p-2 rounded"
            onClick={fetchTasks}
          >
            Refresh Tasks
          </button>
        </section>
        <section className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Upload Response</h2>
          {uploadResponse && (
            <pre className="bg-white p-4 rounded shadow">
              {JSON.stringify(uploadResponse, null, 2)}
            </pre>
          )}
        </section>
        <section>
          <h2 className="text-lg font-semibold mb-2">Tasks List</h2>
          {tasks.length > 0 ? (
            <div>
              {tasks.map((task, index) => (
                <div key={index} className="bg-white p-4 rounded shadow mb-2">
                  <p>
                    <strong>Filename:</strong> {task.filename}
                  </p>
                  <p>
                    <strong>Status:</strong> {task.status}
                  </p>
                  {task.transcription && (
                    <p>
                      <strong>Transcription:</strong> {task.transcription}
                    </p>
                  )}
                  {task.proofread ? (
                    <p>
                      <strong>Proofread:</strong> {task.proofread}
                    </p>
                  ) : (
                    <button
                      className="bg-purple-500 text-white p-1 rounded mt-2"
                      onClick={() => handleProofread(task.filename)}
                    >
                      Proofread
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p>No tasks available. Click "Refresh Tasks" to update.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
