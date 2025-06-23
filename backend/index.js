const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const app = express();
const port = 3001;

// Ensure uploads directory exists
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadsDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + "-" + file.originalname);
  }
});

const upload = multer({ storage: storage });

app.use(express.json());
let globalTasks = [];

// Endpoint to upload audio files
app.post("/upload", upload.array("audioFiles", 10), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: "No files were uploaded." });
  }
  // For each uploaded file, create a task (stub)
  const tasks = req.files.map((file) => ({
    filename: file.filename,
    originalname: file.originalname,
    path: file.path,
    status: "pending"
  }));
  tasks.forEach((task) => {
    globalTasks.push(task);
    setTimeout(() => {
      task.status = "completed";
      task.transcription = `This is the transcription of ${task.filename}.`;
    }, 5000);
  });
  res.json({ message: "Files uploaded successfully.", tasks });
});

// Endpoint to list tasks (stub)
app.get("/tasks", (req, res) => {
  res.json({ tasks: globalTasks });
});

app.get("/transcribe", (req, res) => {
  const { filename } = req.query;
  if (!filename) {
    return res.status(400).json({ error: "filename parameter is required" });
  }
  const transcription = `This is the transcription of ${filename}.`;
  res.json({ filename, transcription });
});

app.get("/translate", (req, res) => {
  const { text, targetLanguage } = req.query;
  if (!text || !targetLanguage) {
    return res
      .status(400)
      .json({ error: "text and targetLanguage are required" });
  }
  const translatedText = `${text} (translated to ${targetLanguage})`;
  res.json({ text, targetLanguage, translatedText });
});

app.get("/proofread", (req, res) => {
  const { filename } = req.query;
  if (!filename) {
    return res.status(400).json({ error: "filename parameter is required" });
  }
  const proofread = `Proofread transcription for ${filename}: Corrected errors...`;
  res.json({ filename, proofread });
});

app.listen(port, () => {
  console.log(`Backend server listening on port ${port}`);
});
